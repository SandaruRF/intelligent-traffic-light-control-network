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
    MAX_QUEUE,
    ADJUSTMENT_FACTOR,
    SENSOR_PERIOD,
    CONTROL_PERIOD,
    COORDINATION_PERIOD,
    BROADCAST_PERIOD,
    ARRIVAL_RATE,
    DEPARTURE_RATE,
    YELLOW_LIGHT_DURATION,
    get_neighbor_jids
)

AXIS_LEADERS = {
    "NS": "TL_NORTH",
    "EW": "TL_EAST"
}


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
        permitted_movements = state.get_green_movements()
        
        # Track departures from simulator
        old_departures = simulator.total_departures
        
        # Update queues using stochastic simulation
        current_queues = state.get_queues_dict()
        updated_queues = simulator.update_queues(
            current_queues,
            permitted_movements,
            time_delta=SENSOR_PERIOD
        )
        
        # Calculate vehicles processed (departed this cycle)
        vehicles_departed = simulator.total_departures - old_departures
        
        # Update state
        state.update_queues(updated_queues)
        state.total_vehicles_processed += vehicles_departed
        
        # Log if queues changed significantly or vehicles departed
        total_queue = state.get_total_queue()
        if vehicles_departed > 0 and state.cycle_count % 5 == 0:
            self.agent.log(
                f"✅ {self.agent.approach_direction}: processed {vehicles_departed} vehicles | "
                f"Queue={total_queue} | Total processed={state.total_vehicles_processed}"
            )
        elif total_queue > 15:
            self.agent.log(
                f"⚠️  {self.agent.approach_direction} high queue: {total_queue} vehicles",
                "WARNING"
            )


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
        state.green_time_remaining = max(0.0, state.green_time_remaining - CONTROL_PERIOD)
        
        # Check if time to switch phase
        if state.green_time_remaining <= 0:
            if self.agent.is_axis_leader:
                await self._switch_phase()
            else:
                # Followers wait for leader broadcast; avoid negative timers
                state.green_time_remaining = MIN_GREEN_TIME
        
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
        old_phase = state.current_phase
        next_phase = state.current_phase.next()
        state.current_phase = next_phase

        if next_phase.is_clearance():
            new_green_time = self.agent.clearance_duration
        else:
            new_green_time = self._calculate_adaptive_green_time()
            state.cycle_count += 1

        state.green_time_remaining = new_green_time

        for msg in self.agent.create_phase_update_messages(next_phase, new_green_time):
            await self.send(msg)

        phase_mode = "Clearance" if next_phase.is_clearance() else "Movement"
        self.agent.log(
            f"🔄 Leader switched phase: {old_phase} -> {next_phase} "
            f"({phase_mode} {new_green_time:.1f}s)"
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
        active_axis = state.current_phase.active_axis()
        
        if active_axis is None:
            return YELLOW_LIGHT_DURATION
        
        opposite_axis = "EW" if active_axis == "NS" else "NS"
        current_pressure = self.agent.estimate_axis_pressure(active_axis)
        opposite_pressure = self.agent.estimate_axis_pressure(opposite_axis)
        
        # Step 2: Get average neighbor pressure
        avg_neighbor_pressure = state.get_average_neighbor_pressure()
        
        # Step 3: Enhanced decision logic (respecting phase type)
        phase_is_straight = state.current_phase.is_straight_phase()
        base_green = BASE_GREEN_TIME if phase_is_straight else max(MIN_GREEN_TIME, BASE_GREEN_TIME * 0.7)
        max_green = MAX_GREEN_TIME if phase_is_straight else max(MIN_GREEN_TIME, MAX_GREEN_TIME * 0.7)
        
        # Case 1: Current direction is MUCH busier than opposite (2x threshold)
        if current_pressure > opposite_pressure * 2.0 and current_pressure > 0.3:
            new_green_time = max_green
            reason = "Heavy current direction"
        
        # Case 2: Opposite direction is busier - switch quickly
        elif opposite_pressure > current_pressure * 1.5:
            new_green_time = MIN_GREEN_TIME
            reason = "Opposite direction needs service"
        
        # Case 3: Balanced locally - use neighbor coordination
        else:
            pressure_diff = current_pressure - avg_neighbor_pressure
            adjustment = pressure_diff * ADJUSTMENT_FACTOR
            new_green_time = base_green + adjustment
            reason = "Neighbor coordination"
        
        # Step 4: Enforce limits
        new_green_time = max(MIN_GREEN_TIME, min(max_green, new_green_time))
        
        # Debug logging
        self.agent.log(
            f"📊 Phase {state.current_phase}: Current={current_pressure:.2f}, Opposite={opposite_pressure:.2f}, "
            f"Neighbors={avg_neighbor_pressure:.2f} -> Green={new_green_time:.1f}s ({reason})",
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
                f"Green={state.green_time_remaining:.1f}s | Approach {self.agent.approach_direction} "
                f"Queues[straight:{state.queue_straight} left:{state.queue_left} right:{state.queue_right}] "
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
            "approach": self.agent.approach_direction,
            "axis": state.axis,
            "queues": state.get_queues_dict(),
            "total_queue": state.get_total_queue(),
            "current_phase": str(state.current_phase),
            "green_movements": state.get_green_movements(),
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
        
        if "phase_update" in data:
            self._apply_phase_update(data)
            return
        
        # Extract neighbor information
        neighbor_name = data.get("from", "Unknown")
        neighbor_total_queue = data.get("total_queue", 0)
        
        # Update neighbor queue information
        state.neighbor_queues[neighbor_name] = neighbor_total_queue
        state.neighbor_axes[neighbor_name] = data.get("axis", state.axis)
        
        # Log receipt (occasionally to avoid spam)
        if state.cycle_count % 10 == 0:
            self.agent.log(
                f"📥 Received from {neighbor_name}: Queue={neighbor_total_queue}"
            )

    def _apply_phase_update(self, data: Dict) -> None:
        state: TrafficLightState = self.agent.state
        phase_str = data.get("phase_update", str(TrafficPhase.NS_STRAIGHT_RIGHT))
        state.current_phase = TrafficPhase.from_string(phase_str)
        state.green_time_remaining = data.get("green_time", BASE_GREEN_TIME)
        incoming_cycle = data.get("cycle", state.cycle_count)
        state.cycle_count = max(state.cycle_count, incoming_cycle)
        self.agent.log(
            f"📡 Phase update received: {state.current_phase} | "
            f"Green={state.green_time_remaining:.1f}s"
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
        self.approach_direction = self._infer_direction(intersection_name)
        self.is_axis_leader = AXIS_LEADERS.get(self._axis_label) == intersection_name
        self.coordinator_jid = coordinator_jid
        
        # Get neighbor JIDs from topology
        self.neighbor_jids = get_neighbor_jids(intersection_name)
        
        # Initialize state
        self.state = TrafficLightState(
            intersection_name=intersection_name,
            approach_direction=self.approach_direction,
            current_phase=TrafficPhase.NS_STRAIGHT_RIGHT,
            green_time_remaining=BASE_GREEN_TIME
        )
        
        # Initialize queue simulator
        self.queue_simulator = QueueSimulator(
            arrival_rate=ARRIVAL_RATE,
            departure_rate=DEPARTURE_RATE
        )
        self.clearance_duration = YELLOW_LIGHT_DURATION
        
        self.log(f"🚦 Approach {self.approach_direction} initialized as part of four-way junction")
        self.log(f"   Neighbors: {[jid.split('@')[0] for jid in self.neighbor_jids]}")

    @property
    def _axis_label(self) -> str:
        return "NS" if self.approach_direction in ("N", "S") else "EW"

    @staticmethod
    def _infer_direction(name: str) -> str:
        if name.endswith("NORTH"):
            return "N"
        if name.endswith("SOUTH"):
            return "S"
        if name.endswith("EAST"):
            return "E"
        if name.endswith("WEST"):
            return "W"
        # Default to north for unknown names
        return "N"

    def estimate_axis_pressure(self, axis: str) -> float:
        total_queue = 0
        participants = 0

        if self.state.axis == axis:
            total_queue += self.state.get_total_queue()
            participants += 1

        for name, queue in self.state.neighbor_queues.items():
            if self.state.neighbor_axes.get(name) == axis:
                total_queue += queue
                participants += 1

        if participants == 0:
            return 0.0

        normalized = total_queue / (MAX_QUEUE * participants)
        return min(1.0, max(0.0, normalized))
    
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

    def create_phase_update_messages(self, phase: TrafficPhase, green_time: float) -> List[Message]:
        """Create phase update notifications for all neighbors."""
        body = {
            "from": self.intersection_name,
            "approach": self.approach_direction,
            "axis": self.state.axis,
            "phase_update": str(phase),
            "green_time": green_time,
            "cycle": self.state.cycle_count
        }
        return [
            self.create_fipa_message(
                to=neighbor,
                performative=FIPAPerformatives.INFORM,
                ontology=ONTOLOGY_COORDINATION,
                body_data=body
            )
            for neighbor in self.neighbor_jids
        ]
    
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
    
    def add_vehicle_burst(self, movement: str, count: int) -> None:
        """Inject vehicles into a specific lane (straight/left/right)."""
        normalized = movement.lower()
        if normalized in {"n", "s", "e", "w"}:
            normalized = "straight"
        if normalized not in {"straight", "left", "right"}:
            return

        current_queues = self.state.get_queues_dict()
        current_queues[normalized] = min(
            current_queues[normalized] + count,
            MAX_QUEUE
        )
        self.state.update_queues(current_queues)
        self.log(
            f"🦋 BUTTERFLY EFFECT: Added {count} vehicles to {normalized} lane of {self.approach_direction}"
        )
    
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
