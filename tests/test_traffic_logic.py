"""
Unit tests for traffic logic components.
"""

import unittest
from src.models.traffic_state import TrafficPhase, TrafficLightState
from src.models.queue_simulator import QueueSimulator


class TestTrafficPhase(unittest.TestCase):
    """Test TrafficPhase enum."""
    
    def test_phase_next(self):
        """Test phase cycling."""
        phase = TrafficPhase.NS_GREEN
        self.assertEqual(phase.next(), TrafficPhase.EW_GREEN)
        self.assertEqual(phase.next().next(), TrafficPhase.NS_GREEN)
    
    def test_green_directions(self):
        """Test green direction retrieval."""
        ns_phase = TrafficPhase.NS_GREEN
        self.assertEqual(ns_phase.get_green_directions(), ["N", "S"])
        
        ew_phase = TrafficPhase.EW_GREEN
        self.assertEqual(ew_phase.get_green_directions(), ["E", "W"])


class TestTrafficLightState(unittest.TestCase):
    """Test TrafficLightState dataclass."""
    
    def setUp(self):
        """Create test state."""
        self.state = TrafficLightState(
            intersection_name="TEST_INTERSECTION",
            queue_north=5,
            queue_south=3,
            queue_east=4,
            queue_west=2
        )
    
    def test_total_queue(self):
        """Test total queue calculation."""
        self.assertEqual(self.state.get_total_queue(), 14)
    
    def test_ns_queue(self):
        """Test North-South queue."""
        self.assertEqual(self.state.get_ns_queue(), 8)
    
    def test_ew_queue(self):
        """Test East-West queue."""
        self.assertEqual(self.state.get_ew_queue(), 6)
    
    def test_queues_dict(self):
        """Test queue dictionary conversion."""
        queues = self.state.get_queues_dict()
        self.assertEqual(queues["N"], 5)
        self.assertEqual(queues["S"], 3)
        self.assertEqual(queues["E"], 4)
        self.assertEqual(queues["W"], 2)
    
    def test_pressure_calculation(self):
        """Test traffic pressure calculation."""
        ns_pressure = self.state.calculate_pressure("NS")
        ew_pressure = self.state.calculate_pressure("EW")
        
        self.assertGreater(ns_pressure, ew_pressure)
        self.assertGreaterEqual(ns_pressure, 0.0)
        self.assertLessEqual(ns_pressure, 1.0)


class TestQueueSimulator(unittest.TestCase):
    """Test QueueSimulator."""
    
    def setUp(self):
        """Create test simulator."""
        self.simulator = QueueSimulator(arrival_rate=0.5, departure_rate=0.5)
    
    def test_initialization(self):
        """Test simulator initialization."""
        self.assertEqual(self.simulator.arrival_rate, 0.5)
        self.assertEqual(self.simulator.departure_rate, 0.5)
        self.assertEqual(self.simulator.total_arrivals, 0)
        self.assertEqual(self.simulator.total_departures, 0)
    
    def test_queue_update(self):
        """Test queue update logic."""
        current_queues = {"N": 5, "S": 3, "E": 4, "W": 2}
        green_directions = ["N", "S"]
        
        # Run multiple updates
        for _ in range(10):
            current_queues = self.simulator.update_queues(
                current_queues, green_directions, time_delta=1.0
            )
        
        # Verify queues are non-negative
        for queue in current_queues.values():
            self.assertGreaterEqual(queue, 0)
        
        # Verify some activity occurred
        self.assertGreater(
            self.simulator.total_arrivals + self.simulator.total_departures,
            0
        )
    
    def test_scenario_changes(self):
        """Test scenario switching."""
        self.simulator.set_rush_hour()
        self.assertEqual(self.simulator.arrival_rate, 0.6)
        
        self.simulator.set_light_traffic()
        self.assertEqual(self.simulator.arrival_rate, 0.1)
        
        self.simulator.set_normal_traffic()
        self.assertEqual(self.simulator.arrival_rate, 0.3)
    
    def test_statistics(self):
        """Test statistics retrieval."""
        stats = self.simulator.get_statistics()
        
        self.assertIn("total_arrivals", stats)
        self.assertIn("total_departures", stats)
        self.assertIn("arrival_rate", stats)
        self.assertIn("departure_rate", stats)


if __name__ == "__main__":
    unittest.main()
