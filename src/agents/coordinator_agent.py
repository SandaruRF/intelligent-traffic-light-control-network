"""
Coordinator Agent for system monitoring and metrics collection.

This agent demonstrates the Request-Resource-Message architecture:
- Traffic lights are Resource agents (managing intersection capacity)
- Coordinator is Message agent (logging and monitoring)

The coordinator provides centralized monitoring WITHOUT central control.
Traffic lights remain autonomous in their decision-making.
"""

import asyncio
from typing import Dict, List
from datetime import datetime

from spade.behaviour import CyclicBehaviour, PeriodicBehaviour

from src.agents.base_agent import BaseTrafficAgent
from src.models.traffic_state import SystemMetrics, TrafficPhase
from src.settings import ONTOLOGY_STATUS, get_all_traffic_light_jids

# GUI Visualization (optional)
try:
    from src.visualization.gui_simulator import get_gui
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    get_gui = lambda: None


class MonitorBehaviour(CyclicBehaviour):
    """
    Continuously monitor messages from traffic light agents.
    
    Collects state updates and calculates system-wide metrics.
    This enables performance tracking without interfering with
    autonomous agent decisions.
    """
    
    async def run(self) -> None:
        """Receive and process status updates."""
        msg = await self.receive(timeout=2.0)
        
        if msg:
            parsed = self.agent.parse_fipa_message(msg)
            
            if parsed and parsed["ontology"] == ONTOLOGY_STATUS:
                await self._handle_status_update(parsed)
    
    async def _handle_status_update(self, parsed: Dict) -> None:
        """
        Process status update from traffic light agent.
        
        Args:
            parsed: Parsed FIPA message
        """
        metrics: SystemMetrics = self.agent.metrics
        data = parsed["data"]
        
        # Update system metrics
        metrics.update(data)
        
        # Update GUI if available
        gui = get_gui()
        if gui and GUI_AVAILABLE:
            gui.update_intersection(data["intersection"], data)
        
        # Store in history for visualization
        intersection = data["intersection"]
        self.agent.state_history[intersection].append({
            "timestamp": datetime.now(),
            "data": data
        })
        
        # Keep only recent history (last 100 updates per intersection)
        if len(self.agent.state_history[intersection]) > 100:
            self.agent.state_history[intersection].pop(0)
        
        # Log summary occasionally
        if metrics.total_vehicles_waiting > 0:
            self.agent.log(
                f"📊 {intersection}: Queue={data['total_queue']} "
                f"Phase={data['phase']} Cycle={data['cycle_count']}"
            )


class MetricsReportBehaviour(PeriodicBehaviour):
    """
    Periodically report system-wide metrics.
    
    Calculates and logs aggregate statistics about network performance.
    This helps demonstrate the system's emergent optimization.
    
    Period: 10 seconds
    """
    
    async def run(self) -> None:
        """Generate and log metrics report."""
        metrics: SystemMetrics = self.agent.metrics
        
        # Calculate current metrics
        metrics.calculate_throughput()
        
        # Count active intersections
        active_count = len(metrics.intersection_states)
        
        if active_count == 0:
            return
        
        # Calculate average queue per intersection
        avg_queue = metrics.total_vehicles_waiting / active_count if active_count > 0 else 0
        axis_loads = {"NS": 0, "EW": 0}
        for state in metrics.intersection_states.values():
            axis = state.get("axis", "NS")
            axis_loads[axis] = axis_loads.get(axis, 0) + state.get("total_queue", 0)
        
        # Generate report
        throughput_per_min = metrics.system_throughput
        improvement_indicator = "📈" if throughput_per_min > 5 else "📊"
        
        report = (
            f"\n{'='*60}\n"
            f"{improvement_indicator} SYSTEM METRICS REPORT\n"
            f"{'='*60}\n"
            f"Active Intersections: {active_count}\n"
            f"Total Vehicles Waiting: {metrics.total_vehicles_waiting}\n"
            f"Average Queue/Intersection: {avg_queue:.1f}\n"
            f"System Throughput: {throughput_per_min:.2f} vehicles/min {improvement_indicator}\n"
            f"Total Processed: {metrics.total_vehicles_processed}\n"
        )
        
        # Show trend if we have history
        if hasattr(self.agent, '_last_total_processed'):
            vehicles_since_last = metrics.total_vehicles_processed - self.agent._last_total_processed
            report += f"Processed (last 10s): {vehicles_since_last} vehicles\n"
        
        report += f"{'='*60}\n"
        
        self.agent._last_total_processed = metrics.total_vehicles_processed
        
        self.agent.log(report)
        self.agent.log(
            f"Axis Load → NS:{axis_loads.get('NS', 0)} | EW:{axis_loads.get('EW', 0)}"
        )
        
        # Update GUI metrics
        gui = get_gui()
        if gui and GUI_AVAILABLE:
            gui.update_metrics({
                "total_waiting": metrics.total_vehicles_waiting,
                "avg_queue": avg_queue,
                "throughput": throughput_per_min,
                "total_processed": metrics.total_vehicles_processed,
                "active_phase": self.agent.get_active_phase(),
                "axis_loads": axis_loads
            })
        
        # Detailed per-intersection report
        self.agent.log("Per-Intersection Status:")
        for intersection, state in metrics.intersection_states.items():
            processed = state.get('vehicles_processed', 0)
            self.agent.log(
                f"  {intersection}: Queue={state['total_queue']} "
                f"Phase={state['phase']} Cycle={state['cycle_count']} "
                f"Processed={processed}"
            )


class HealthCheckBehaviour(PeriodicBehaviour):
    """
    Monitor system health and detect anomalies.
    
    Checks for:
    - Unresponsive agents
    - Excessive queue buildup
    - Communication failures
    
    Period: 15 seconds
    """
    
    async def run(self) -> None:
        """Perform health check."""
        metrics: SystemMetrics = self.agent.metrics
        current_time = datetime.now()
        
        # Check for stale data (agents not reporting)
        stale_threshold = 30  # seconds
        
        for intersection, state in metrics.intersection_states.items():
            last_update = datetime.fromisoformat(state["timestamp"])
            age = (current_time - last_update).total_seconds()
            
            if age > stale_threshold:
                self.agent.log(
                    f"⚠️  WARNING: No update from {intersection} for {age:.0f}s",
                    "WARNING"
                )
        
        # Check for excessive queues
        excessive_queue_threshold = 15
        
        for intersection, state in metrics.intersection_states.items():
            if state["total_queue"] > excessive_queue_threshold:
                self.agent.log(
                    f"⚠️  ALERT: High queue at {intersection}: {state['total_queue']} vehicles",
                    "WARNING"
                )
        
        # Log health status
        if len(metrics.intersection_states) > 0:
            self.agent.log(f"✅ System health: {len(metrics.intersection_states)} agents reporting")


class CoordinatorAgent(BaseTrafficAgent):
    """
    Coordinator agent for centralized monitoring of distributed system.
    
    Responsibilities:
    - Collect status updates from all traffic lights
    - Calculate system-wide performance metrics
    - Detect anomalies and health issues
    - Provide visualization data
    
    Important: The coordinator OBSERVES but does NOT CONTROL.
    This maintains the distributed, autonomous nature of the system.
    """
    
    def __init__(self, jid: str, password: str):
        """
        Initialize coordinator agent.
        
        Args:
            jid: Agent JID
            password: XMPP password
        """
        super().__init__(jid, password, agent_name="Coordinator")
        
        # System metrics
        self.metrics = SystemMetrics()
        
        # State history for visualization
        self.state_history: Dict[str, List[Dict]] = {}
        
        # Initialize history for all expected intersections
        traffic_light_jids = get_all_traffic_light_jids()
        for jid in traffic_light_jids:
            intersection_name = jid.split("@")[0].replace("tl_", "TL_").upper()
            self.state_history[intersection_name] = []
        
        self.log("📊 Coordinator initialized")
    
    async def setup(self) -> None:
        """Setup coordinator behaviors."""
        await super().setup()
        
        self.log("🚀 Starting monitoring behaviors...")
        
        # Add monitoring behaviors
        self.add_behaviour(MonitorBehaviour())
        self.add_behaviour(MetricsReportBehaviour(period=10.0))
        self.add_behaviour(HealthCheckBehaviour(period=15.0))
        
        self.log("✅ Coordinator ready - monitoring all intersections")
    
    def get_system_metrics(self) -> Dict:
        """
        Get current system metrics.
        
        Returns:
            Dictionary with system-wide metrics
        """
        return self.metrics.to_dict()
    
    def get_active_phase(self) -> str:
        """Return the most recently reported phase for the junction."""
        default_phase = str(TrafficPhase.NS_STRAIGHT_RIGHT)
        for state in self.metrics.intersection_states.values():
            return state.get("phase", default_phase)
        return default_phase
    
    def get_intersection_history(self, intersection: str, limit: int = 50) -> List[Dict]:
        """
        Get state history for specific intersection.
        
        Args:
            intersection: Intersection name
            limit: Maximum number of records to return
        
        Returns:
            List of historical state records
        """
        if intersection in self.state_history:
            return self.state_history[intersection][-limit:]
        return []
    
    def get_all_current_states(self) -> Dict[str, Dict]:
        """
        Get current state of all intersections.
        
        Returns:
            Dictionary mapping intersection names to current states
        """
        return self.metrics.intersection_states.copy()
    
    def reset_metrics(self) -> None:
        """Reset all metrics (for scenario changes)."""
        self.metrics = SystemMetrics()
        for intersection in self.state_history:
            self.state_history[intersection] = []
        
        self.log("🔄 Metrics reset")
    
    def get_performance_summary(self) -> str:
        """
        Generate human-readable performance summary.
        
        Returns:
            Formatted summary string
        """
        metrics = self.metrics
        metrics.calculate_throughput()
        
        active_count = len(metrics.intersection_states)
        avg_queue = metrics.total_vehicles_waiting / active_count if active_count > 0 else 0
        
        summary = f"""
System Performance Summary
==========================
Runtime: {(datetime.now() - metrics.start_time).total_seconds():.0f} seconds
Active Intersections: {active_count}
Total Vehicles Waiting: {metrics.total_vehicles_waiting}
Average Queue Length: {avg_queue:.2f}
System Throughput: {metrics.system_throughput:.2f} vehicles/min
Total Processed: {metrics.total_vehicles_processed}
"""
        
        return summary
    
    def export_data(self) -> Dict:
        """
        Export all collected data for analysis.
        
        Returns:
            Complete dataset including metrics and history
        """
        return {
            "metrics": self.metrics.to_dict(),
            "current_states": self.get_all_current_states(),
            "history": self.state_history,
            "runtime_stats": self.get_runtime_stats(),
            "export_time": datetime.now().isoformat()
        }
