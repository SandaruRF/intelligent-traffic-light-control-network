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
        arrival_rate: float = 0.3,
        departure_rate: float = 0.4,
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
        green_directions: List[str],
        time_delta: float = 1.0
    ) -> Dict[str, int]:
        """
        Update queue lengths based on stochastic arrivals and departures.
        
        This is the core simulation logic:
        1. Vehicles arrive randomly in all directions (Poisson-like process)
        2. Vehicles depart only from directions with green light
        3. Queue length is constrained by maximum capacity
        
        Args:
            current_queues: Current queue lengths {"N": int, "S": int, "E": int, "W": int}
            green_directions: List of directions with green light (e.g., ["N", "S"])
            time_delta: Time elapsed since last update in seconds (default 1.0)
        
        Returns:
            Updated queue lengths as dictionary
        """
        updated_queues = current_queues.copy()
        
        for direction in ["N", "S", "E", "W"]:
            # === ARRIVALS (Stochastic) ===
            # Probability increases with time_delta
            arrival_probability = self.arrival_rate * time_delta
            
            # Random arrival event
            if random.random() < arrival_probability:
                if updated_queues[direction] < self.max_queue_length:
                    updated_queues[direction] += 1
                    self.total_arrivals += 1
            
            # === DEPARTURES (Only when green) ===
            if direction in green_directions and updated_queues[direction] > 0:
                departure_probability = self.departure_rate * time_delta
                
                # Random departure event
                if random.random() < departure_probability:
                    updated_queues[direction] = max(0, updated_queues[direction] - 1)
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
        self.arrival_rate = 0.3
        self.departure_rate = 0.4
    
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
    
    def simulate_burst(self, direction: str, count: int) -> int:
        """
        Simulate a burst of vehicles arriving at once (for testing butterfly effect).
        
        Args:
            direction: Direction code ("N", "S", "E", or "W")
            count: Number of vehicles to add
        
        Returns:
            Actual number of vehicles added (may be limited by max_queue_length)
        """
        if direction not in ["N", "S", "E", "W"]:
            return 0
        
        # This would typically be called externally, but we return the count
        # so the caller can add it to their queue
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
    """
    Enhanced queue simulator with direction-specific arrival rates.
    
    This allows simulation of scenarios where traffic is heavier in specific
    directions (e.g., rush hour with more northbound traffic).
    """
    
    def __init__(
        self,
        base_arrival_rate: float = 0.3,
        departure_rate: float = 0.4,
        max_queue_length: int = 30
    ):
        """
        Initialize directional queue simulator.
        
        Args:
            base_arrival_rate: Base arrival rate for all directions
            departure_rate: Departure rate when green
            max_queue_length: Maximum queue per direction
        """
        super().__init__(base_arrival_rate, departure_rate, max_queue_length)
        
        # Direction-specific multipliers (1.0 = normal)
        self.direction_multipliers = {
            "N": 1.0,
            "S": 1.0,
            "E": 1.0,
            "W": 1.0
        }
    
    def set_directional_bias(self, direction: str, multiplier: float) -> None:
        """
        Set arrival rate multiplier for a specific direction.
        
        Args:
            direction: Direction code ("N", "S", "E", or "W")
            multiplier: Arrival rate multiplier (e.g., 2.0 = double traffic)
        """
        if direction in self.direction_multipliers:
            self.direction_multipliers[direction] = max(0.0, multiplier)
    
    def set_ns_heavy(self) -> None:
        """Configure for heavy North-South traffic (directional scenario)."""
        self.direction_multipliers = {
            "N": 2.5,
            "S": 2.5,
            "E": 0.5,
            "W": 0.5
        }
    
    def set_ew_heavy(self) -> None:
        """Configure for heavy East-West traffic."""
        self.direction_multipliers = {
            "N": 0.5,
            "S": 0.5,
            "E": 2.5,
            "W": 2.5
        }
    
    def update_queues(
        self,
        current_queues: Dict[str, int],
        green_directions: List[str],
        time_delta: float = 1.0
    ) -> Dict[str, int]:
        """
        Update queues with direction-specific arrival rates.
        
        Args:
            current_queues: Current queue lengths
            green_directions: Directions with green light
            time_delta: Time elapsed in seconds
        
        Returns:
            Updated queue lengths
        """
        updated_queues = current_queues.copy()
        
        for direction in ["N", "S", "E", "W"]:
            # === ARRIVALS with directional bias ===
            directional_rate = self.arrival_rate * self.direction_multipliers[direction]
            arrival_probability = directional_rate * time_delta
            
            if random.random() < arrival_probability:
                if updated_queues[direction] < self.max_queue_length:
                    updated_queues[direction] += 1
                    self.total_arrivals += 1
            
            # === DEPARTURES (same logic as parent) ===
            if direction in green_directions and updated_queues[direction] > 0:
                departure_probability = self.departure_rate * time_delta
                
                if random.random() < departure_probability:
                    updated_queues[direction] = max(0, updated_queues[direction] - 1)
                    self.total_departures += 1
        
        return updated_queues
