"""
Traffic state models for the traffic light control system.

This module defines the core data structures representing traffic light states,
phases, and queue information.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


class TrafficPhase(Enum):
    """Multi-phase plan combining straight/right, left-only, yellow, and clearance states."""

    NS_STRAIGHT_RIGHT = "NS_SR"
    NS_YELLOW = "NS_YELLOW"
    CLEARANCE_NS_TO_EW = "CLR_NS_EW"
    EW_STRAIGHT_RIGHT = "EW_SR"
    EW_YELLOW = "EW_YELLOW"
    CLEARANCE_EW_TO_NSLEFT = "CLR_EW_NSLEFT"
    NS_LEFT_ONLY = "NS_LEFT"
    NS_LEFT_YELLOW = "NS_LEFT_YELLOW"
    CLEARANCE_NSLEFT_TO_EWLEFT = "CLR_NSLEFT_EWLEFT"
    EW_LEFT_ONLY = "EW_LEFT"
    EW_LEFT_YELLOW = "EW_LEFT_YELLOW"
    CLEARANCE_EWLEFT_TO_NS = "CLR_EWLEFT_NS"

    def next(self) -> 'TrafficPhase':
        """Return the next phase in the predefined sequence."""
        idx = PHASE_SEQUENCE.index(self)
        return PHASE_SEQUENCE[(idx + 1) % len(PHASE_SEQUENCE)]

    def is_clearance(self) -> bool:
        return self not in PHASE_MOVEMENTS

    def is_yellow(self) -> bool:
        """Check if phase is a yellow/amber transition."""
        return self in {TrafficPhase.NS_YELLOW, TrafficPhase.EW_YELLOW,
                        TrafficPhase.NS_LEFT_YELLOW, TrafficPhase.EW_LEFT_YELLOW}

    def is_left_phase(self) -> bool:
        return self in {TrafficPhase.NS_LEFT_ONLY, TrafficPhase.EW_LEFT_ONLY}

    def is_straight_phase(self) -> bool:
        return self in {TrafficPhase.NS_STRAIGHT_RIGHT, TrafficPhase.EW_STRAIGHT_RIGHT}

    def active_axis(self) -> Optional[str]:
        if self in {TrafficPhase.NS_STRAIGHT_RIGHT, TrafficPhase.NS_LEFT_ONLY}:
            return "NS"
        if self in {TrafficPhase.EW_STRAIGHT_RIGHT, TrafficPhase.EW_LEFT_ONLY}:
            return "EW"
        return None

    def get_green_movements(self, axis: str) -> List[str]:
        """Return permitted movements for the supplied axis during this phase."""
        return list(PHASE_MOVEMENTS.get(self, {}).get(axis, []))

    @classmethod
    def from_string(cls, value: str) -> 'TrafficPhase':
        """Parse a string (display label or enum value) into a TrafficPhase."""
        for phase in cls:
            if value == phase.value or value == str(phase):
                return phase
        # Backwards compatibility with legacy labels
        if value.lower().startswith("ns"):
            return cls.NS_STRAIGHT_RIGHT
        if value.lower().startswith("ew"):
            return cls.EW_STRAIGHT_RIGHT
        return cls.NS_STRAIGHT_RIGHT

    def __str__(self) -> str:
        return PHASE_DISPLAY_NAMES[self]


PHASE_SEQUENCE: List[TrafficPhase] = [
    TrafficPhase.NS_STRAIGHT_RIGHT,
    TrafficPhase.NS_YELLOW,
    TrafficPhase.CLEARANCE_NS_TO_EW,
    TrafficPhase.EW_STRAIGHT_RIGHT,
    TrafficPhase.EW_YELLOW,
    TrafficPhase.CLEARANCE_EW_TO_NSLEFT,
    TrafficPhase.NS_LEFT_ONLY,
    TrafficPhase.NS_LEFT_YELLOW,
    TrafficPhase.CLEARANCE_NSLEFT_TO_EWLEFT,
    TrafficPhase.EW_LEFT_ONLY,
    TrafficPhase.EW_LEFT_YELLOW,
    TrafficPhase.CLEARANCE_EWLEFT_TO_NS
]

PHASE_DISPLAY_NAMES = {
    TrafficPhase.NS_STRAIGHT_RIGHT: "NS Straight+Right",
    TrafficPhase.NS_YELLOW: "NS Yellow (Straight+Right)",
    TrafficPhase.CLEARANCE_NS_TO_EW: "All-Red (NS->EW)",
    TrafficPhase.EW_STRAIGHT_RIGHT: "EW Straight+Right",
    TrafficPhase.EW_YELLOW: "EW Yellow (Straight+Right)",
    TrafficPhase.CLEARANCE_EW_TO_NSLEFT: "All-Red (EW->NS Left)",
    TrafficPhase.NS_LEFT_ONLY: "NS Protected Left",
    TrafficPhase.NS_LEFT_YELLOW: "NS Yellow (Left)",
    TrafficPhase.CLEARANCE_NSLEFT_TO_EWLEFT: "All-Red (NS Left->EW Left)",
    TrafficPhase.EW_LEFT_ONLY: "EW Protected Left",
    TrafficPhase.EW_LEFT_YELLOW: "EW Yellow (Left)",
    TrafficPhase.CLEARANCE_EWLEFT_TO_NS: "All-Red (EW Left->NS)"
}

PHASE_MOVEMENTS = {
    TrafficPhase.NS_STRAIGHT_RIGHT: {"NS": ["straight", "right"], "EW": []},
    TrafficPhase.EW_STRAIGHT_RIGHT: {"NS": [], "EW": ["straight", "right"]},
    TrafficPhase.NS_LEFT_ONLY: {"NS": ["left"], "EW": []},
    TrafficPhase.EW_LEFT_ONLY: {"NS": [], "EW": ["left"]}
}


@dataclass
class TrafficLightState:
    """State for a single approach (north/south/east/west) of the junction."""

    intersection_name: str
    approach_direction: str  # "N", "S", "E", or "W"

    current_phase: TrafficPhase = TrafficPhase.NS_STRAIGHT_RIGHT
    green_time_remaining: float = 5.0
    right_turn_free: bool = True

    queue_straight: int = 0
    queue_left: int = 0
    queue_right: int = 0

    neighbor_queues: Dict[str, Dict[str, int]] = field(default_factory=dict)
    neighbor_axes: Dict[str, str] = field(default_factory=dict)

    cycle_count: int = 0
    total_vehicles_processed: int = 0
    cumulative_wait_time: float = 0.0

    last_update: datetime = field(default_factory=datetime.now)

    @property
    def axis(self) -> str:
        """Return axis (NS or EW) for this approach."""
        if self.approach_direction in ("N", "S"):
            return "NS"
        return "EW"

    def get_total_queue(self) -> int:
        return self.queue_straight + self.queue_left + self.queue_right

    def get_queues_dict(self) -> Dict[str, int]:
        return {
            "straight": self.queue_straight,
            "left": self.queue_left,
            "right": self.queue_right
        }

    def update_queues(self, queues: Dict[str, int]) -> None:
        self.queue_straight = queues.get("straight", self.queue_straight)
        self.queue_left = queues.get("left", self.queue_left)
        self.queue_right = queues.get("right", self.queue_right)
        self.last_update = datetime.now()

    def get_green_movements(self) -> List[str]:
        allowed = self.current_phase.get_green_movements(self.axis)
        if not self.right_turn_free:
            allowed = [movement for movement in allowed if movement != "right"]
        return allowed

    def calculate_pressure(self) -> float:
        from src.settings import MAX_QUEUE
        return min(1.0, self.get_total_queue() / MAX_QUEUE)

    def get_average_neighbor_pressure(self) -> float:
        if not self.neighbor_queues:
            return 0.0
        from src.settings import MAX_QUEUE
        total_pressure = 0.0
        for neighbor_queues_dict in self.neighbor_queues.values():
            neighbor_total = sum(neighbor_queues_dict.values())
            total_pressure += neighbor_total / MAX_QUEUE
        return total_pressure / len(self.neighbor_queues)

    def to_dict(self) -> Dict:
        return {
            "intersection": self.intersection_name,
            "approach": self.approach_direction,
            "axis": self.axis,
            "phase": str(self.current_phase),
            "green_time_remaining": self.green_time_remaining,
            "queues": self.get_queues_dict(),
            "green_movements": self.get_green_movements(),
            "total_queue": self.get_total_queue(),
            "cycle_count": self.cycle_count,
            "vehicles_processed": self.total_vehicles_processed,
            "timestamp": self.last_update.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"{self.intersection_name}: Cycle={self.cycle_count} "
            f"Phase={self.current_phase} Green={self.green_time_remaining:.1f}s | "
            f"Approach {self.approach_direction} Queues[straight:{self.queue_straight} "
            f"left:{self.queue_left} right:{self.queue_right}] Total={self.get_total_queue()}"
        )


@dataclass
class SystemMetrics:
    """
    System-wide performance metrics for the entire traffic network.
    
    Used by the coordinator agent to track overall system performance.
    """
    
    # Current state
    total_vehicles_waiting: int = 0
    total_vehicles_processed: int = 0
    
    # Performance metrics
    average_wait_time: float = 0.0
    system_throughput: float = 0.0  # vehicles per minute
    
    # Time tracking
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)
    
    # Per-intersection data
    intersection_states: Dict[str, Dict] = field(default_factory=dict)
    
    def update(self, intersection_state: Dict) -> None:
        """
        Update metrics with new intersection state.
        
        Args:
            intersection_state: State dictionary from a traffic light agent
        """
        intersection = intersection_state["intersection"]
        self.intersection_states[intersection] = intersection_state
        self.last_update = datetime.now()
        
        # Calculate system-wide totals
        self.total_vehicles_waiting = sum(
            state["total_queue"]
            for state in self.intersection_states.values()
        )

        self.total_vehicles_processed = sum(
            state.get("vehicles_processed", 0)
            for state in self.intersection_states.values()
        )
    
    def calculate_throughput(self) -> float:
        """
        Calculate system throughput (vehicles per minute).
        
        Returns:
            Throughput value
        """
        elapsed = (self.last_update - self.start_time).total_seconds()
        if elapsed > 0:
            self.system_throughput = (self.total_vehicles_processed / elapsed) * 60
        return self.system_throughput
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "total_waiting": self.total_vehicles_waiting,
            "total_processed": self.total_vehicles_processed,
            "avg_wait_time": self.average_wait_time,
            "throughput": self.system_throughput,
            "timestamp": self.last_update.isoformat()
        }
    
    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"System Metrics: Waiting={self.total_vehicles_waiting} "
            f"Processed={self.total_vehicles_processed} "
            f"Throughput={self.system_throughput:.2f} vehicles/min"
        )
