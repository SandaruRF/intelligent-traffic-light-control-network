"""
Stochastic queue simulator for traffic flow.

This module simulates realistic vehicle arrivals and departures at intersections
using probabilistic models to create dynamic and uncertain traffic conditions.
"""

import random
from typing import Dict, List
from datetime import datetime


class QueueSimulator:
    """
    Simulates vehicle queues at an intersection using stochastic processes.
    
    The simulator uses Poisson-like arrival patterns and departure rates
    to create realistic traffic dynamics. This demonstrates the 'uncertain'
    and 'dynamic' characteristics of complex systems.
    
    Attributes:
        arrival_rate: Probability of vehicle arrival per second (0.0 to 1.0)
        departure_rate: Probability of vehicle departure per second when green
        max_queue_length: Maximum vehicles that can queue in one direction
        total_arrivals: Total vehicles that have arrived
        total_departures: Total vehicles that have departed
    """
    
    def __init__(
        self,
        arrival_rate: float = 0.15,
        departure_rate: float = 0.6,
        max_queue_length: int = 30
    ):
        """
        Initialize the queue simulator.
        
        Args:
            arrival_rate: Base probability of vehicle arrival per second (default 0.3)
            departure_rate: Probability of vehicle departure per second (default 0.4)
            max_queue_length: Maximum queue length per direction (default 30)
        """
        self.arrival_rate = arrival_rate
        self.departure_rate = departure_rate
        self.max_queue_length = max_queue_length
        
        # Statistics tracking
        self.total_arrivals = 0
        self.total_departures = 0
        self.start_time = datetime.now()
        
        # Random seed for reproducibility (optional)
        random.seed()
    
    def update_queues(
        self,
        current_queues: Dict[str, int],
        permitted_movements: List[str],
        time_delta: float = 1.0
    ) -> Dict[str, int]:
        """Update straight/left/right queues for a single approach."""
        updated_queues = current_queues.copy()

        for movement in ["straight", "left", "right"]:
            if movement not in updated_queues:
                updated_queues[movement] = 0
            arrival_probability = self.arrival_rate * time_delta
            if random.random() < arrival_probability:
                if updated_queues[movement] < self.max_queue_length:
                    updated_queues[movement] += 1
                    self.total_arrivals += 1

            if movement in permitted_movements and updated_queues[movement] > 0:
                departure_probability = self.departure_rate * time_delta
                if random.random() < departure_probability:
                    updated_queues[movement] = max(0, updated_queues[movement] - 1)
                    self.total_departures += 1

        return updated_queues
    
    def set_rush_hour(self) -> None:
        """
        Configure simulator for rush hour traffic (high arrival rate).
        
        Rush hour scenario: Heavy traffic in all directions.
        """
        self.arrival_rate = 0.6
        self.departure_rate = 0.4
    
    def set_normal_traffic(self) -> None:
        """
        Configure simulator for normal traffic conditions.
        
        Normal scenario: Moderate traffic flow.
        """
        self.arrival_rate = 0.15
        self.departure_rate = 0.6
    
    def set_light_traffic(self) -> None:
        """
        Configure simulator for light traffic conditions.
        
        Light scenario: Low traffic with quick departures.
        """
        self.arrival_rate = 0.1
        self.departure_rate = 0.5
    
    def set_heavy_traffic(self) -> None:
        """
        Configure simulator for heavy congested traffic.
        
        Heavy scenario: Very high arrivals with slower departures.
        """
        self.arrival_rate = 0.8
        self.departure_rate = 0.3
    
    def set_arrival_rate(self, rate: float) -> None:
        """
        Set custom arrival rate.
        
        Args:
            rate: Probability per second (0.0 to 1.0)
        """
        self.arrival_rate = max(0.0, min(1.0, rate))
    
    def set_departure_rate(self, rate: float) -> None:
        """
        Set custom departure rate.
        
        Args:
            rate: Probability per second (0.0 to 1.0)
        """
        self.departure_rate = max(0.0, min(1.0, rate))
    
    def get_statistics(self) -> Dict:
        """
        Get simulation statistics.
        
        Returns:
            Dictionary with simulation metrics
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "total_arrivals": self.total_arrivals,
            "total_departures": self.total_departures,
            "vehicles_in_system": self.total_arrivals - self.total_departures,
            "arrival_rate": self.arrival_rate,
            "departure_rate": self.departure_rate,
            "elapsed_time": elapsed,
            "arrivals_per_minute": (self.total_arrivals / elapsed * 60) if elapsed > 0 else 0,
            "departures_per_minute": (self.total_departures / elapsed * 60) if elapsed > 0 else 0
        }
    
    def reset_statistics(self) -> None:
        """Reset simulation statistics."""
        self.total_arrivals = 0
        self.total_departures = 0
        self.start_time = datetime.now()
    
    def simulate_burst(self, movement: str, count: int) -> int:
        """Return how many vehicles can be injected for a movement queue."""
        if movement not in ["straight", "left", "right"]:
            return 0
        return min(count, self.max_queue_length)
    
    def __str__(self) -> str:
        """String representation of simulator state."""
        stats = self.get_statistics()
        return (
            f"QueueSimulator(arrivals={stats['total_arrivals']}, "
            f"departures={stats['total_departures']}, "
            f"in_system={stats['vehicles_in_system']}, "
            f"arr_rate={self.arrival_rate:.2f}, "
            f"dep_rate={self.departure_rate:.2f})"
        )


class DirectionalQueueSimulator(QueueSimulator):
    """Queue simulator with multipliers per movement type."""

    def __init__(
        self,
        base_arrival_rate: float = 0.3,
        departure_rate: float = 0.4,
        max_queue_length: int = 30
    ):
        super().__init__(base_arrival_rate, departure_rate, max_queue_length)
        self.movement_multipliers = {
            "straight": 1.0,
            "left": 1.0,
            "right": 1.0
        }

    def set_movement_bias(self, movement: str, multiplier: float) -> None:
        if movement in self.movement_multipliers:
            self.movement_multipliers[movement] = max(0.0, multiplier)

    def update_queues(
        self,
        current_queues: Dict[str, int],
        permitted_movements: List[str],
        time_delta: float = 1.0
    ) -> Dict[str, int]:
        updated = current_queues.copy()
        for movement in ["straight", "left", "right"]:
            directional_rate = self.arrival_rate * self.movement_multipliers[movement]
            arrival_probability = directional_rate * time_delta
            if random.random() < arrival_probability:
                if updated[movement] < self.max_queue_length:
                    updated[movement] += 1
                    self.total_arrivals += 1

            if movement in permitted_movements and updated[movement] > 0:
                departure_probability = self.departure_rate * time_delta
                if random.random() < departure_probability:
                    updated[movement] = max(0, updated[movement] - 1)
                    self.total_departures += 1
        return updated
