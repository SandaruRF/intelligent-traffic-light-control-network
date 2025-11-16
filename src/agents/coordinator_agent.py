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
from src.models.traffic_state import SystemMetrics
from src.settings import ONTOLOGY_STATUS, get_all_traffic_light_jids


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
        
        # Generate report
        report = (
            f"\n{'='*60}\n"
            f"📈 SYSTEM METRICS REPORT\n"
            f"{'='*60}\n"
            f"Active Intersections: {active_count}\n"
            f"Total Vehicles Waiting: {metrics.total_vehicles_waiting}\n"
            f"Average Queue/Intersection: {avg_queue:.1f}\n"
            f"System Throughput: {metrics.system_throughput:.2f} vehicles/min\n"
            f"Total Processed: {metrics.total_vehicles_processed}\n"
            f"{'='*60}\n"
        )
        
        self.agent.log(report)
        
        # Detailed per-intersection report
        self.agent.log("Per-Intersection Status:")
        for intersection, state in metrics.intersection_states.items():
            self.agent.log(
                f"  {intersection}: Queue={state['total_queue']} "
                f"Phase={state['phase']} Cycle={state['cycle_count']}"
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
