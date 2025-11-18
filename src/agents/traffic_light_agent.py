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
    MIN_GREEN_STRAIGHT,
    MIN_GREEN_LEFT,
    P1_GREEN_TIME,
    P2_GREEN_TIME,
    P3_GREEN_TIME,
    P4_GREEN_TIME,
    MAX_QUEUE,
    ADJUSTMENT_FACTOR,
    PHASE_SPEEDUP_FACTOR,
    QUEUE_RELIEF_TARGET,
    SENSOR_PERIOD,
    CONTROL_PERIOD,
    COORDINATION_PERIOD,
    BROADCAST_PERIOD,
    ARRIVAL_RATE,
    DEPARTURE_RATE,
    YELLOW_LIGHT_DURATION,
    ALL_RED_CLEARANCE,
    get_neighbor_jids
)

PHASE_COORDINATOR = "TL_NORTH"


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
        """Execute signal control logic with real-time adaptive adjustments."""
        state: TrafficLightState = self.agent.state
        
        # Decrement green time
        state.green_time_remaining = max(0.0, state.green_time_remaining - CONTROL_PERIOD)
        
        # ADAPTIVE REAL-TIME ADJUSTMENT: Check if we should dynamically adjust green time
        if self.agent.is_phase_master and state.green_time_remaining > 0:
            if not state.current_phase.is_yellow() and not state.current_phase.is_clearance():
                await self._maybe_adjust_green_time()
        
        # Check if time to switch phase
        if state.green_time_remaining <= 0:
            if self.agent.is_phase_master:
                await self._switch_phase()
            else:
                # Followers wait for master broadcast; clamp at zero to reflect pending update
                state.green_time_remaining = 0.0
        
        # Log current status
        self._log_status()
    
    async def _switch_phase(self) -> None:
        """
        Switch to next phase and calculate optimal green time.
        
        Industry four-phase cycle with yellow and all-red intervals:
        P1 (NS straight+right) → yellow → all-red → P2 (EW straight+right) → yellow → all-red →
        P3 (NS left) → yellow → all-red → P4 (EW left) → yellow → all-red → repeat
        """
        state: TrafficLightState = self.agent.state
        old_phase = state.current_phase
        next_phase = state.current_phase.next()
        state.current_phase = next_phase

        if next_phase.is_yellow():
            new_green_time = YELLOW_LIGHT_DURATION
            phase_mode = "Yellow"
        elif next_phase.is_clearance():
            new_green_time = ALL_RED_CLEARANCE
            phase_mode = "All-Red"
        else:
            # Movement phase: compute adaptive green respecting phase-specific minimums
            new_green_time = self._calculate_adaptive_green_time()
            state.cycle_count += 1
            phase_mode = "Movement"

        state.green_time_remaining = new_green_time

        for msg in self.agent.create_phase_update_messages(next_phase, new_green_time):
            await self.send(msg)

        self.agent.log(
            f"🔄 Leader switched phase: {old_phase} -> {next_phase} "
            f"({phase_mode} {new_green_time:.1f}s)"
        )
    
    async def _maybe_adjust_green_time(self) -> None:
        """Dynamically adjust green time based on real-time queue conditions."""
        state: TrafficLightState = self.agent.state
        active_axis = state.current_phase.active_axis()
        
        if active_axis is None:
            return
        
        # Determine movement type and get pressures
        phase_is_straight = state.current_phase.is_straight_phase()
        phase_is_left = state.current_phase.is_left_phase()
        
        if phase_is_straight:
            min_green = MIN_GREEN_STRAIGHT
            relevant_movements = ["straight", "right"]
        elif phase_is_left:
            min_green = MIN_GREEN_LEFT
            relevant_movements = ["left"]
        else:
            return
        
        opposite_axis = "EW" if active_axis == "NS" else "NS"
        current_pressure = self.agent.estimate_movement_pressure(active_axis, relevant_movements)
        opposite_pressure = self.agent.estimate_movement_pressure(opposite_axis, relevant_movements)
        
        # Get actual queue counts for more precise switching
        current_total_queue = 0
        opposite_total_queue = 0
        
        for direction, queues_dict in state.neighbor_queues.items():
            axis = state.neighbor_axes.get(direction, state.axis)
            total = sum(queues_dict.values())
            if axis == active_axis:
                current_total_queue += total
            elif axis == opposite_axis:
                opposite_total_queue += total
        
        # Add own queue
        if state.axis == active_axis:
            current_total_queue += state.get_total_queue()
        elif state.axis == opposite_axis:
            opposite_total_queue += state.get_total_queue()
        
        # IMMEDIATE SWITCH: If current queue is very low (0-5 cars) and opposite queue is significantly higher
        if current_total_queue <= 5 and opposite_total_queue > current_total_queue * 2 and opposite_total_queue > 10:
            self.agent.log(
                f"🚀 IMMEDIATE SWITCH: Current {active_axis} queue={current_total_queue} (empty), "
                f"Opposite {opposite_axis} queue={opposite_total_queue} (high) → Switching now!",
                "INFO"
            )
            # Force immediate phase switch by setting timer to 0
            state.green_time_remaining = 0.0
            return
        
        # EMERGENCY CUT SHORT: If opposite axis is CRITICALLY congested and current is empty
        # Made less aggressive: only at 85% opposite and 10% current
        if opposite_pressure > 0.85 and current_pressure < 0.10:
            if state.green_time_remaining > min_green:
                old_time = state.green_time_remaining
                # Cut to minimum green (never below)
                state.green_time_remaining = max(min_green, 5.0)
                self.agent.log(
                    f"⚡ EMERGENCY CUT: Opposite {opposite_axis} pressure={opposite_pressure:.2f}, current={current_pressure:.2f} "
                    f"→ Reducing green from {old_time:.1f}s to {state.green_time_remaining:.1f}s",
                    "INFO"
                )
                # Broadcast updated green time to followers
                for msg in self.agent.create_phase_update_messages(state.current_phase, state.green_time_remaining):
                    await self.send(msg)
        
        # EXTENSION: If current axis still has heavy demand and we're near end
        elif current_pressure > 0.6 and state.green_time_remaining < 5.0:
            if state.green_time_remaining + 10.0 <= MAX_GREEN_TIME:
                old_time = state.green_time_remaining
                state.green_time_remaining = min(state.green_time_remaining + 8.0, MAX_GREEN_TIME)
                self.agent.log(
                    f"⚡ EXTENSION: Current {active_axis} pressure={current_pressure:.2f} "
                    f"→ Extending green from {old_time:.1f}s to {state.green_time_remaining:.1f}s",
                    "INFO"
                )
                # Broadcast updated green time to followers
                for msg in self.agent.create_phase_update_messages(state.current_phase, state.green_time_remaining):
                    await self.send(msg)
    
    
    def _calculate_adaptive_green_time(self) -> float:
        """
        Calculate optimal green time using multi-agent coordination.
        
        Algorithm:
        1. Determine phase type (straight/right vs protected left) and axis
        2. Compute per-movement pressure across own approach + axis partners
        3. Compare current axis demand vs opposite axis demand
        4. Apply adaptive scaling within min/max bounds per phase type
        5. Consider neighbor pressure for distributed optimization
        
        Returns:
            Adaptive green time in seconds (respects industry minimums)
        """
        state: TrafficLightState = self.agent.state
        active_axis = state.current_phase.active_axis()
        
        if active_axis is None:
            return YELLOW_LIGHT_DURATION
        
        # Phase-specific configuration
        phase_is_straight = state.current_phase.is_straight_phase()
        phase_is_left = state.current_phase.is_left_phase()
        
        if phase_is_straight:
            # P1 or P2: N+S or E+W straight+right
            min_green = MIN_GREEN_STRAIGHT
            base_green = P1_GREEN_TIME if active_axis == "NS" else P2_GREEN_TIME
            max_green = MAX_GREEN_TIME
            relevant_movements = ["straight", "right"]
        elif phase_is_left:
            # P3 or P4: N+S or E+W protected left
            min_green = MIN_GREEN_LEFT
            base_green = P3_GREEN_TIME if active_axis == "NS" else P4_GREEN_TIME
            max_green = max(MIN_GREEN_LEFT, MAX_GREEN_TIME * 0.5)
            relevant_movements = ["left"]
        else:
            return BASE_GREEN_TIME
        
        # Compute axis-level demand for current and opposite directions
        opposite_axis = "EW" if active_axis == "NS" else "NS"
        current_pressure = self.agent.estimate_movement_pressure(active_axis, relevant_movements)
        opposite_pressure = self.agent.estimate_movement_pressure(opposite_axis, relevant_movements)
        
        # Get average neighbor pressure for coordination
        avg_neighbor_pressure = state.get_average_neighbor_pressure()
        
        # Decision logic with industry constraints and queue-responsive behavior
        reason_parts = []
        if current_pressure < 0.05 and opposite_pressure > 0.4:
            # Almost no current demand and opposite has queue: use minimum green
            new_green_time = min_green
            reason_parts.append("No demand, opposite waiting")
        elif current_pressure < 0.05 and opposite_pressure < 0.1:
            # Low traffic overall: use minimum to keep cycle moving
            new_green_time = min_green
            reason_parts.append("Light traffic overall")
        elif opposite_pressure > 0.8 and current_pressure < 0.2:
            # Heavy opposite axis congestion with low current demand: reduce but respect minimum
            new_green_time = min_green + (base_green - min_green) * 0.3
            reason_parts.append(f"Opposite {opposite_axis} critically congested ({opposite_pressure:.2f})")
        elif current_pressure > 0.7:
            # Heavy current axis congestion: maximize green time
            new_green_time = max_green
            reason_parts.append(f"Heavy {active_axis} congestion ({current_pressure:.2f})")
        elif current_pressure > opposite_pressure * 2.0 and current_pressure > 0.3:
            # Current axis significantly higher demand
            new_green_time = base_green + (max_green - base_green) * 0.5
            reason_parts.append(f"{active_axis} priority (2x demand)")
        elif opposite_pressure > current_pressure * 2.0 and opposite_pressure > 0.3:
            # Opposite axis significantly higher demand: reduce current
            new_green_time = min_green + (base_green - min_green) * 0.5
            reason_parts.append(f"Reduce for {opposite_axis} (2x demand)")
        else:
            # Balanced or both low: use base time or pressure-based adjustment
            if current_pressure < 0.15 and opposite_pressure < 0.15:
                # Both axes low traffic: use base time to ensure fair cycling
                new_green_time = base_green
                reason_parts.append("Balanced low traffic")
            else:
                # Use pressure-based adaptive adjustment
                pressure_ratio = current_pressure / max(0.01, opposite_pressure)
                if pressure_ratio > 1.2:
                    adjustment = (pressure_ratio - 1.0) * ADJUSTMENT_FACTOR * 10
                elif pressure_ratio < 0.8:
                    adjustment = -(1.0 - pressure_ratio) * ADJUSTMENT_FACTOR * 10
                else:
                    # Nearly balanced, use neighbor coordination
                    pressure_diff = current_pressure - avg_neighbor_pressure
                    adjustment = pressure_diff * ADJUSTMENT_FACTOR
                new_green_time = base_green + adjustment
                reason_parts.append(f"Adaptive (ratio={pressure_ratio:.2f})")

        # Queue relief bias: if opposite has significantly more backlog, trim current phase
        queue_gap = opposite_pressure - current_pressure
        if queue_gap > QUEUE_RELIEF_TARGET and current_pressure < 0.65:
            before = new_green_time
            new_green_time = max(min_green, new_green_time * (1.0 - QUEUE_RELIEF_TARGET))
            reason_parts.append(
                f"Accelerated {active_axis} by {(before - new_green_time):.1f}s for {opposite_axis} relief"
            )
        elif queue_gap < -QUEUE_RELIEF_TARGET:
            before = new_green_time
            boost = 1.0 + (QUEUE_RELIEF_TARGET * 0.5)
            new_green_time = min(max_green, new_green_time * boost)
            reason_parts.append(
                f"Extended {active_axis} by {(new_green_time - before):.1f}s to clear backlog"
            )

        # Global speed-up for non-critical phases to increase cycle throughput
        if current_pressure < 0.65:
            new_green_time *= PHASE_SPEEDUP_FACTOR
            reason_parts.append(f"Speedup x{PHASE_SPEEDUP_FACTOR:.2f}")
        
        # Enforce bounds
        new_green_time = max(min_green, min(max_green, new_green_time))
        
        # Debug logging
        self.agent.log(
            f"📊 Phase {state.current_phase.name}: Axis {active_axis} moves={relevant_movements} | "
            f"Current pressure={current_pressure:.2f} Opposite pressure={opposite_pressure:.2f} | "
            f"→ Green={new_green_time:.1f}s ({'; '.join(reason_parts)})",
            "INFO"
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
            total_q = state.get_total_queue()
            self.agent.log(
                f"📤 Coordination: {self.agent.approach_direction} Total={total_q} "
                f"Queues[S:{state.queue_straight} L:{state.queue_left} R:{state.queue_right}] "
                f"→ {len(neighbor_jids)} neighbors",
                "INFO"
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
        neighbor_approach = data.get("approach", "Unknown")
        neighbor_queues_dict = data.get("queues", {})
        
        # Update neighbor queue information with per-movement data
        state.neighbor_queues[neighbor_approach] = neighbor_queues_dict
        state.neighbor_axes[neighbor_approach] = data.get("axis", state.axis)
        
        # Log receipt (occasionally to avoid spam)
        if state.cycle_count % 10 == 0:
            total_q = sum(neighbor_queues_dict.values())
            self.agent.log(
                f"📥 Received from {neighbor_approach}: Queues={neighbor_queues_dict} (Total={total_q})"
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
        self.is_phase_master = intersection_name == PHASE_COORDINATOR
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
        
        self.log(f"🚦 Approach {self.approach_direction} initialized as part of four-way junction")
        self.log(f"   Neighbors: {[jid.split('@')[0] for jid in self.neighbor_jids]}")

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

        for name, queues_dict in self.state.neighbor_queues.items():
            if self.state.neighbor_axes.get(name) == axis:
                total_queue += sum(queues_dict.values())
                participants += 1

        if participants == 0:
            return 0.0

        normalized = total_queue / (MAX_QUEUE * participants)
        return min(1.0, max(0.0, normalized))

    def estimate_movement_pressure(self, axis: str, movements: List[str]) -> float:
        """Estimate pressure for specific movements (straight/right/left) on an axis."""
        state = self.state

        if axis == "NS":
            approaches = ["N", "S"]
        elif axis == "EW":
            approaches = ["E", "W"]
        else:
            return 0.0

        total_queue = 0.0
        max_possible = 0.0

        for approach in approaches:
            if approach == self.approach_direction:
                # Use own queues directly
                for movement in movements:
                    if movement == "straight":
                        total_queue += state.queue_straight
                    elif movement == "left":
                        total_queue += state.queue_left
                    elif movement == "right":
                        total_queue += state.queue_right
                    max_possible += MAX_QUEUE
            else:
                neighbor_queues = state.neighbor_queues.get(approach, {})
                for movement in movements:
                    total_queue += neighbor_queues.get(movement, 0)
                    max_possible += MAX_QUEUE

        pressure = (total_queue / max_possible) if max_possible > 0 else 0.0

        if self.is_phase_master and state.cycle_count % 3 == 0:
            self.log(
                f"🔍 Pressure calc axis={axis} moves={movements} total={total_queue:.0f} "
                f"capacity={max_possible:.0f} pressure={pressure:.3f}",
                "DEBUG"
            )

        return pressure
    
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
