"""
Traffic state models for the traffic light control system.

This module defines the core data structures representing traffic light states,
phases, and queue information.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime


class TrafficPhase(Enum):
    """
    Enumeration of traffic light phases.
    
    NS_GREEN: North-South direction has green light (East-West has red)
    EW_GREEN: East-West direction has green light (North-South has red)
    """
    NS_GREEN = 0
    EW_GREEN = 1
    
    def next(self) -> 'TrafficPhase':
        """Get the next phase in the cycle."""
        if self == TrafficPhase.NS_GREEN:
            return TrafficPhase.EW_GREEN
        return TrafficPhase.NS_GREEN
    
    def get_green_directions(self) -> list[str]:
        """
        Get the directions that have green light in this phase.
        
        Returns:
            List of direction codes: ["N", "S"] or ["E", "W"]
        """
        if self == TrafficPhase.NS_GREEN:
            return ["N", "S"]
        return ["E", "W"]
    
    def __str__(self) -> str:
        """String representation for logging."""
        if self == TrafficPhase.NS_GREEN:
            return "NS-Green"
        return "EW-Green"


@dataclass
class TrafficLightState:
    """
    Complete state of a traffic light agent.
    
    This dataclass encapsulates all the information needed to represent
    the current state of a traffic light intersection, including:
    - Current signal phase
    - Queue lengths in all directions
    - Timing information
    - Performance metrics
    """
    
    # Identity
    intersection_name: str
    
    # Current signal state
    current_phase: TrafficPhase = TrafficPhase.NS_GREEN
    green_time_remaining: float = 5.0  # seconds
    
    # Queue lengths (number of vehicles waiting)
    queue_north: int = 0
    queue_south: int = 0
    queue_east: int = 0
    queue_west: int = 0
    
    # Neighbor information (for coordination)
    neighbor_queues: Dict[str, int] = field(default_factory=dict)
    
    # Performance tracking
    cycle_count: int = 0
    total_vehicles_processed: int = 0
    cumulative_wait_time: float = 0.0
    
    # Timestamp
    last_update: datetime = field(default_factory=datetime.now)
    
    def get_total_queue(self) -> int:
        """Get total number of vehicles waiting at this intersection."""
        return self.queue_north + self.queue_south + self.queue_east + self.queue_west
    
    def get_ns_queue(self) -> int:
        """Get total queue for North-South direction."""
        return self.queue_north + self.queue_south
    
    def get_ew_queue(self) -> int:
        """Get total queue for East-West direction."""
        return self.queue_east + self.queue_west
    
    def get_current_direction_queue(self) -> int:
        """Get queue length for the direction that currently has green light."""
        if self.current_phase == TrafficPhase.NS_GREEN:
            return self.get_ns_queue()
        return self.get_ew_queue()
    
    def get_queues_dict(self) -> Dict[str, int]:
        """
        Get queue lengths as a dictionary.
        
        Returns:
            Dictionary with direction codes as keys and queue lengths as values
        """
        return {
            "N": self.queue_north,
            "S": self.queue_south,
            "E": self.queue_east,
            "W": self.queue_west
        }
    
    def update_queues(self, queues: Dict[str, int]) -> None:
        """
        Update queue lengths from a dictionary.
        
        Args:
            queues: Dictionary with direction codes ("N", "S", "E", "W") as keys
        """
        self.queue_north = queues.get("N", self.queue_north)
        self.queue_south = queues.get("S", self.queue_south)
        self.queue_east = queues.get("E", self.queue_east)
        self.queue_west = queues.get("W", self.queue_west)
        self.last_update = datetime.now()
    
    def calculate_pressure(self, direction: str) -> float:
        """
        Calculate traffic pressure for a given direction (normalized).
        
        Args:
            direction: "NS" or "EW"
        
        Returns:
            Normalized pressure value (0.0 to 1.0)
        """
        from src.settings import MAX_QUEUE
        
        if direction == "NS":
            return self.get_ns_queue() / MAX_QUEUE
        elif direction == "EW":
            return self.get_ew_queue() / MAX_QUEUE
        return 0.0
    
    def get_average_neighbor_pressure(self) -> float:
        """
        Calculate average traffic pressure from neighboring intersections.
        
        Returns:
            Average normalized pressure (0.0 to 1.0)
        """
        from src.settings import MAX_QUEUE
        
        if not self.neighbor_queues:
            return 0.0
        
        total_pressure = sum(queue / MAX_QUEUE for queue in self.neighbor_queues.values())
        return total_pressure / len(self.neighbor_queues)
    
    def to_dict(self) -> Dict:
        """
        Convert state to dictionary for message passing.
        
        Returns:
            Dictionary representation of the state
        """
        return {
            "intersection": self.intersection_name,
            "phase": str(self.current_phase),
            "green_time_remaining": self.green_time_remaining,
            "queues": self.get_queues_dict(),
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
            f"Queues[N:{self.queue_north} S:{self.queue_south} "
            f"E:{self.queue_east} W:{self.queue_west}] Total={self.get_total_queue()}"
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
