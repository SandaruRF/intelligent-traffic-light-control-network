"""
Traffic Light Agent with autonomous control and coordination behaviors.

This is the core agent that demonstrates:
- Autonomy: Independent decision-making
- Reactivity: Responds to queue changes
- Adaptivity: Adjusts timing dynamically
- Sociability: Coordinates with neighbors
- Situatedness: Bound to specific intersection
"""

import asyncio
import json
from typing import Dict, List

from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

from src.agents.base_agent import BaseTrafficAgent, FIPAPerformatives
from src.models.traffic_state import TrafficLightState, TrafficPhase
from src.models.queue_simulator import QueueSimulator
from src.settings import (
    INTERSECTIONS,
    ONTOLOGY_COORDINATION,
    ONTOLOGY_STATUS,
    BASE_GREEN_TIME,
    MIN_GREEN_TIME,
    MAX_GREEN_TIME,
    ADJUSTMENT_FACTOR,
    SENSOR_PERIOD,
    CONTROL_PERIOD,
    COORDINATION_PERIOD,
    BROADCAST_PERIOD,
    ARRIVAL_RATE,
    DEPARTURE_RATE,
    get_neighbor_jids
)


class SensorBehaviour(PeriodicBehaviour):
    """
    Simulates traffic sensors detecting vehicles at the intersection.
    
    Updates queue lengths using the stochastic queue simulator.
    This demonstrates the 'dynamic' and 'uncertain' nature of the environment.
    
    Period: 1 second (SENSOR_PERIOD)
    """
    
    async def run(self) -> None:
        """Update queue lengths based on current traffic conditions."""
        state: TrafficLightState = self.agent.state
        simulator: QueueSimulator = self.agent.queue_simulator
        
        # Get current green directions
        green_directions = state.current_phase.get_green_directions()
        
        # Get queues before update (to track departures)
        current_queues = state.get_queues_dict()
        old_total = sum(current_queues.values())
        
        # Update queues using stochastic simulation
        updated_queues = simulator.update_queues(
            current_queues,
            green_directions,
            time_delta=SENSOR_PERIOD
        )
        
        # Calculate vehicles processed (departed)
        new_total = sum(updated_queues.values())
        vehicles_departed = max(0, old_total - new_total + (simulator.total_arrivals - state.get_total_queue() - simulator.total_departures))
        
        # Update state
        state.update_queues(updated_queues)
        state.total_vehicles_processed += vehicles_departed
        
        # Log if queues changed significantly or vehicles departed
        total_queue = state.get_total_queue()
        if vehicles_departed > 0 and state.cycle_count % 5 == 0:
            self.agent.log(f"✅ Processed {vehicles_departed} vehicles | Queue: {total_queue} | Total processed: {state.total_vehicles_processed}")
        elif total_queue > 10:
            self.agent.log(f"⚠️  High queue: {total_queue} vehicles waiting", "WARNING")


class SignalControlBehaviour(PeriodicBehaviour):
    """
    Core traffic signal control logic with self-organizing algorithm.
    
    This behavior implements the emergent optimization:
    1. Calculate local traffic pressure
    2. Consider neighbor pressures
    3. Adjust green time to balance load
    4. Switch phases when timer expires
    
    This is where EMERGENT BEHAVIOR and SELF-ORGANIZATION happen!
    
    Period: 2 seconds (CONTROL_PERIOD)
    """
    
    async def run(self) -> None:
        """Execute signal control logic."""
        state: TrafficLightState = self.agent.state
        
        # Decrement green time
        state.green_time_remaining -= CONTROL_PERIOD
        
        # Check if time to switch phase
        if state.green_time_remaining <= 0:
            await self._switch_phase()
        
        # Log current status
        self._log_status()
    
    async def _switch_phase(self) -> None:
        """
        Switch to next phase and calculate optimal green time.
        
        CORE SELF-ORGANIZING ALGORITHM:
        - Compare my pressure to neighbor average
        - Adjust green time accordingly
        - System optimizes without central control!
        """
        state: TrafficLightState = self.agent.state
        
        # Switch phase
        old_phase = state.current_phase
        state.current_phase = state.current_phase.next()
        state.cycle_count += 1
        
        # Calculate new green time using self-organizing rule
        new_green_time = self._calculate_adaptive_green_time()
        state.green_time_remaining = new_green_time
        
        self.agent.log(
            f"🔄 Phase switch: {old_phase} → {state.current_phase} "
            f"(Green: {new_green_time:.1f}s)"
        )
    
    def _calculate_adaptive_green_time(self) -> float:
        """
        Calculate optimal green time using enhanced coordination algorithm.
        
        Enhanced Algorithm:
        1. Calculate my directional pressure (normalized queue length)
        2. Compare with opposite direction (internal balance)
        3. Consider average neighbor pressure (network coordination)
        4. Apply intelligent adjustments:
           - If current direction >> opposite: give max green
           - If current direction < opposite: reduce green quickly
           - Otherwise: use neighbor-based coordination
        5. Apply limits
        
        Returns:
            Optimal green time in seconds
        """
        state: TrafficLightState = self.agent.state
        
        # Step 1: Calculate pressure for current and opposite directions
        if state.current_phase == TrafficPhase.NS_GREEN:
            current_pressure = state.calculate_pressure("NS")
            opposite_pressure = state.calculate_pressure("EW")
        else:
            current_pressure = state.calculate_pressure("EW")
            opposite_pressure = state.calculate_pressure("NS")
        
        # Step 2: Get average neighbor pressure
        avg_neighbor_pressure = state.get_average_neighbor_pressure()
        
        # Step 3: Enhanced decision logic
        
        # Case 1: Current direction is MUCH busier than opposite (2x threshold)
        if current_pressure > opposite_pressure * 2.0 and current_pressure > 0.3:
            new_green_time = MAX_GREEN_TIME
            reason = "Heavy current direction"
        
        # Case 2: Opposite direction is busier - switch quickly
        elif opposite_pressure > current_pressure * 1.5:
            new_green_time = MIN_GREEN_TIME
            reason = "Opposite direction needs service"
        
        # Case 3: Balanced locally - use neighbor coordination
        else:
            pressure_diff = current_pressure - avg_neighbor_pressure
            adjustment = pressure_diff * ADJUSTMENT_FACTOR
            new_green_time = BASE_GREEN_TIME + adjustment
            reason = "Neighbor coordination"
        
        # Step 4: Enforce limits
        new_green_time = max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, new_green_time))
        
        # Debug logging
        self.agent.log(
            f"📊 Pressure: Current={current_pressure:.2f}, Opposite={opposite_pressure:.2f}, "
            f"Neighbors={avg_neighbor_pressure:.2f} → Green={new_green_time:.1f}s ({reason})",
            "DEBUG"
        )
        
        return new_green_time
    
    def _log_status(self) -> None:
        """Log current intersection status."""
        state: TrafficLightState = self.agent.state
        
        # Only log every 5 seconds to avoid spam
        if state.cycle_count % 3 == 0:
            self.agent.log(
                f"Cycle {state.cycle_count}: Phase={state.current_phase} "
                f"Green={state.green_time_remaining:.1f}s | "
                f"Queues[N:{state.queue_north} S:{state.queue_south} "
                f"E:{state.queue_east} W:{state.queue_west}] "
                f"Total={state.get_total_queue()}"
            )


class CoordinationBehaviour(PeriodicBehaviour):
    """
    Send queue status to neighbor agents for coordination.
    
    This enables distributed coordination without central control.
    Each agent shares local information, allowing emergent optimization.
    
    Period: 2 seconds (COORDINATION_PERIOD)
    """
    
    async def run(self) -> None:
        """Send coordination message to all neighbors."""
        state: TrafficLightState = self.agent.state
        neighbor_jids = self.agent.neighbor_jids
        
        # Prepare message data
        message_data = {
            "from": state.intersection_name,
            "queues": state.get_queues_dict(),
            "total_queue": state.get_total_queue(),
            "current_phase": str(state.current_phase),
            "cycle_count": state.cycle_count
        }
        
        # Send to all neighbors
        for neighbor_jid in neighbor_jids:
            msg = self.agent.create_fipa_message(
                to=neighbor_jid,
                performative=FIPAPerformatives.INFORM,
                ontology=ONTOLOGY_COORDINATION,
                body_data=message_data
            )
            
            await self.send(msg)
        
        # Log occasionally
        if state.cycle_count % 5 == 0 and neighbor_jids:
            self.agent.log(
                f"📤 Sent coordination to {len(neighbor_jids)} neighbors "
                f"(Total queue: {state.get_total_queue()})"
            )


class MessageHandlerBehaviour(CyclicBehaviour):
    """
    Receive and process messages from neighbor agents.
    
    This behavior enables peer-to-peer communication and coordination.
    Updates neighbor queue information for adaptive control.
    
    Runs continuously (CyclicBehaviour)
    """
    
    async def run(self) -> None:
        """Receive and process incoming messages."""
        # Wait for message (non-blocking with timeout)
        msg = await self.receive(timeout=1.0)
        
        if msg:
            parsed = self.agent.parse_fipa_message(msg)
            
            if parsed and parsed["ontology"] == ONTOLOGY_COORDINATION:
                await self._handle_coordination_message(parsed)
    
    async def _handle_coordination_message(self, parsed: Dict) -> None:
        """
        Process coordination message from neighbor.
        
        Args:
            parsed: Parsed message dictionary
        """
        state: TrafficLightState = self.agent.state
        data = parsed["data"]
        
        # Extract neighbor information
        neighbor_name = data.get("from", "Unknown")
        neighbor_total_queue = data.get("total_queue", 0)
        
        # Update neighbor queue information
        state.neighbor_queues[neighbor_name] = neighbor_total_queue
        
        # Log receipt (occasionally to avoid spam)
        if state.cycle_count % 10 == 0:
            self.agent.log(
                f"📥 Received from {neighbor_name}: Queue={neighbor_total_queue}"
            )


class StateBroadcastBehaviour(PeriodicBehaviour):
    """
    Broadcast full state to coordinator for monitoring.
    
    This enables the coordinator to collect system-wide metrics
    and demonstrate the Request-Resource-Message architecture.
    
    Period: 3 seconds (BROADCAST_PERIOD)
    """
    
    async def run(self) -> None:
        """Send state update to coordinator."""
        state: TrafficLightState = self.agent.state
        coordinator_jid = self.agent.coordinator_jid
        
        # Prepare full state data
        state_data = state.to_dict()
        
        # Add simulator statistics
        state_data["simulator_stats"] = self.agent.queue_simulator.get_statistics()
        
        # Create FIPA message
        msg = self.agent.create_fipa_message(
            to=coordinator_jid,
            performative=FIPAPerformatives.INFORM,
            ontology=ONTOLOGY_STATUS,
            body_data=state_data
        )
        
        await self.send(msg)
        
        # Log occasionally
        if state.cycle_count % 10 == 0:
            self.agent.log(f"📊 Sent status to coordinator")


class TrafficLightAgent(BaseTrafficAgent):
    """
    Autonomous traffic light agent with adaptive control.
    
    Demonstrates all required MAS characteristics:
    - Autonomy: Makes independent timing decisions
    - Reactivity: Responds to queue changes
    - Adaptivity: Adjusts green time dynamically
    - Sociability: Coordinates with neighbors
    - Situatedness: Bound to specific intersection
    
    Exhibits complex systems properties:
    - Emergent Behavior: System optimization emerges from local rules
    - Self-Organization: No central controller
    - Distributed Control: Each agent operates independently
    """
    
    def __init__(
        self,
        intersection_name: str,
        jid: str,
        password: str,
        coordinator_jid: str
    ):
        """
        Initialize traffic light agent.
        
        Args:
            intersection_name: Name of intersection (e.g., "TL_CENTER")
            jid: Agent JID
            password: XMPP password
            coordinator_jid: Coordinator agent JID
        """
        super().__init__(jid, password, agent_name=intersection_name)
        
        self.intersection_name = intersection_name
        self.coordinator_jid = coordinator_jid
        
        # Get neighbor JIDs from topology
        self.neighbor_jids = get_neighbor_jids(intersection_name)
        
        # Initialize state
        self.state = TrafficLightState(
            intersection_name=intersection_name,
            current_phase=TrafficPhase.NS_GREEN,
            green_time_remaining=BASE_GREEN_TIME
        )
        
        # Initialize queue simulator
        self.queue_simulator = QueueSimulator(
            arrival_rate=ARRIVAL_RATE,
            departure_rate=DEPARTURE_RATE
        )
        
        self.log(f"🚦 Initialized at intersection {intersection_name}")
        self.log(f"   Neighbors: {[jid.split('@')[0] for jid in self.neighbor_jids]}")
    
    async def setup(self) -> None:
        """Setup behaviors when agent starts."""
        await super().setup()
        
        self.log("🚀 Starting behaviors...")
        
        # Add all 5 behaviors
        self.add_behaviour(SensorBehaviour(period=SENSOR_PERIOD))
        self.add_behaviour(SignalControlBehaviour(period=CONTROL_PERIOD))
        self.add_behaviour(CoordinationBehaviour(period=COORDINATION_PERIOD))
        self.add_behaviour(MessageHandlerBehaviour())
        self.add_behaviour(StateBroadcastBehaviour(period=BROADCAST_PERIOD))
        
        self.log("✅ All behaviors active")
    
    def set_traffic_scenario(self, scenario: str) -> None:
        """
        Change traffic scenario (for demos).
        
        Args:
            scenario: Scenario name ("normal", "rush_hour", "light", etc.)
        """
        if scenario == "rush_hour":
            self.queue_simulator.set_rush_hour()
            self.log("🚗 Traffic scenario: RUSH HOUR")
        elif scenario == "light":
            self.queue_simulator.set_light_traffic()
            self.log("🚗 Traffic scenario: LIGHT")
        elif scenario == "heavy":
            self.queue_simulator.set_heavy_traffic()
            self.log("🚗 Traffic scenario: HEAVY")
        else:
            self.queue_simulator.set_normal_traffic()
            self.log("🚗 Traffic scenario: NORMAL")
    
    def add_vehicle_burst(self, direction: str, count: int) -> None:
        """
        Add burst of vehicles (for butterfly effect demo).
        
        Args:
            direction: Direction code ("N", "S", "E", "W")
            count: Number of vehicles to add
        """
        if direction in ["N", "S", "E", "W"]:
            current_queues = self.state.get_queues_dict()
            current_queues[direction] += count
            self.state.update_queues(current_queues)
            
            self.log(f"🦋 BUTTERFLY EFFECT: Added {count} vehicles to {direction}")
    
    def get_status(self) -> Dict:
        """
        Get complete agent status.
        
        Returns:
            Status dictionary
        """
        return {
            "intersection": self.intersection_name,
            "state": self.state.to_dict(),
            "neighbors": len(self.neighbor_jids),
            "simulator_stats": self.queue_simulator.get_statistics(),
            "runtime_stats": self.get_runtime_stats()
        }
