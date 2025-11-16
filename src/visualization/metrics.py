"""
Metrics tracking and calculation utilities.

Provides functions for calculating performance metrics and
comparing adaptive vs fixed-timing strategies.
"""

from typing import Dict, List, Tuple
from datetime import datetime


class PerformanceMetrics:
    """
    Tracks and calculates traffic system performance metrics.
    
    Used to demonstrate that the adaptive system outperforms
    fixed-timing baseline.
    """
    
    def __init__(self, system_name: str = "Adaptive"):
        """
        Initialize metrics tracker.
        
        Args:
            system_name: Name of the system being tracked
        """
        self.system_name = system_name
        self.start_time = datetime.now()
        
        # Raw data
        self.queue_samples: List[Tuple[datetime, int]] = []
        self.throughput_samples: List[Tuple[datetime, float]] = []
        self.phase_switches: List[Tuple[datetime, str]] = []
        
        # Aggregate metrics
        self.total_vehicle_minutes = 0.0  # Vehicle-minutes of delay
        self.peak_queue = 0
        self.average_queue = 0.0
    
    def record_queue_state(self, timestamp: datetime, total_queue: int) -> None:
        """
        Record system queue state at a point in time.
        
        Args:
            timestamp: Time of measurement
            total_queue: Total vehicles waiting across all intersections
        """
        self.queue_samples.append((timestamp, total_queue))
        
        # Update peak
        if total_queue > self.peak_queue:
            self.peak_queue = total_queue
    
    def record_throughput(self, timestamp: datetime, vehicles_per_min: float) -> None:
        """
        Record system throughput.
        
        Args:
            timestamp: Time of measurement
            vehicles_per_min: Throughput in vehicles per minute
        """
        self.throughput_samples.append((timestamp, vehicles_per_min))
    
    def record_phase_switch(self, timestamp: datetime, intersection: str) -> None:
        """
        Record a phase switch event.
        
        Args:
            timestamp: Time of switch
            intersection: Intersection name
        """
        self.phase_switches.append((timestamp, intersection))
    
    def calculate_average_queue(self) -> float:
        """
        Calculate time-weighted average queue length.
        
        Returns:
            Average queue length
        """
        if len(self.queue_samples) < 2:
            return 0.0
        
        total_weighted = 0.0
        total_time = 0.0
        
        for i in range(len(self.queue_samples) - 1):
            time1, queue1 = self.queue_samples[i]
            time2, queue2 = self.queue_samples[i + 1]
            
            duration = (time2 - time1).total_seconds()
            avg_queue = (queue1 + queue2) / 2
            
            total_weighted += avg_queue * duration
            total_time += duration
        
        if total_time > 0:
            self.average_queue = total_weighted / total_time
        
        return self.average_queue
    
    def calculate_average_throughput(self) -> float:
        """
        Calculate average system throughput.
        
        Returns:
            Average throughput in vehicles per minute
        """
        if not self.throughput_samples:
            return 0.0
        
        total = sum(tp for _, tp in self.throughput_samples)
        return total / len(self.throughput_samples)
    
    def calculate_vehicle_minutes_delay(self) -> float:
        """
        Calculate total vehicle-minutes of delay.
        
        This is a standard traffic engineering metric:
        Sum of (queue_length * time_duration) for all time periods.
        
        Returns:
            Total vehicle-minutes of delay
        """
        if len(self.queue_samples) < 2:
            return 0.0
        
        total_delay = 0.0
        
        for i in range(len(self.queue_samples) - 1):
            time1, queue1 = self.queue_samples[i]
            time2, queue2 = self.queue_samples[i + 1]
            
            duration_minutes = (time2 - time1).total_seconds() / 60.0
            avg_queue = (queue1 + queue2) / 2
            
            total_delay += avg_queue * duration_minutes
        
        self.total_vehicle_minutes = total_delay
        return total_delay
    
    def get_phase_switch_count(self) -> int:
        """Get total number of phase switches."""
        return len(self.phase_switches)
    
    def get_phase_switches_per_minute(self) -> float:
        """Calculate phase switches per minute."""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60.0
        if elapsed > 0:
            return len(self.phase_switches) / elapsed
        return 0.0
    
    def get_summary(self) -> Dict:
        """
        Get comprehensive metrics summary.
        
        Returns:
            Dictionary with all calculated metrics
        """
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "system_name": self.system_name,
            "runtime_seconds": runtime,
            "runtime_minutes": runtime / 60.0,
            "average_queue": self.calculate_average_queue(),
            "peak_queue": self.peak_queue,
            "average_throughput": self.calculate_average_throughput(),
            "vehicle_minutes_delay": self.calculate_vehicle_minutes_delay(),
            "phase_switch_count": self.get_phase_switch_count(),
            "phase_switches_per_minute": self.get_phase_switches_per_minute(),
            "samples_collected": len(self.queue_samples)
        }
    
    def compare_to(self, other: 'PerformanceMetrics') -> Dict:
        """
        Compare this system's performance to another.
        
        Args:
            other: Other metrics object to compare against
        
        Returns:
            Comparison dictionary with improvement percentages
        """
        my_summary = self.get_summary()
        other_summary = other.get_summary()
        
        def percent_improvement(baseline, improved):
            if baseline == 0:
                return 0.0
            return ((baseline - improved) / baseline) * 100
        
        return {
            "systems": f"{self.system_name} vs {other.system_name}",
            "avg_queue_improvement": percent_improvement(
                other_summary["average_queue"],
                my_summary["average_queue"]
            ),
            "peak_queue_improvement": percent_improvement(
                other_summary["peak_queue"],
                my_summary["peak_queue"]
            ),
            "delay_reduction": percent_improvement(
                other_summary["vehicle_minutes_delay"],
                my_summary["vehicle_minutes_delay"]
            ),
            "throughput_improvement": percent_improvement(
                -other_summary["average_throughput"],  # Negative because higher is better
                -my_summary["average_throughput"]
            )
        }
    
    def __str__(self) -> str:
        """String representation of metrics."""
        summary = self.get_summary()
        return (
            f"{self.system_name} Metrics:\n"
            f"  Runtime: {summary['runtime_minutes']:.1f} min\n"
            f"  Avg Queue: {summary['average_queue']:.2f}\n"
            f"  Peak Queue: {summary['peak_queue']}\n"
            f"  Avg Throughput: {summary['average_throughput']:.2f} veh/min\n"
            f"  Total Delay: {summary['vehicle_minutes_delay']:.1f} veh-min\n"
            f"  Phase Switches: {summary['phase_switch_count']}"
        )


def calculate_system_efficiency(
    vehicles_processed: int,
    total_delay: float,
    runtime_minutes: float
) -> float:
    """
    Calculate overall system efficiency score.
    
    Efficiency = (vehicles_processed / runtime) / (1 + delay_factor)
    
    Args:
        vehicles_processed: Total vehicles that passed through system
        total_delay: Total vehicle-minutes of delay
        runtime_minutes: Total runtime in minutes
    
    Returns:
        Efficiency score (higher is better)
    """
    if runtime_minutes == 0:
        return 0.0
    
    throughput = vehicles_processed / runtime_minutes
    delay_factor = total_delay / max(vehicles_processed, 1)
    
    efficiency = throughput / (1 + delay_factor)
    
    return efficiency


def generate_comparison_report(
    adaptive_metrics: PerformanceMetrics,
    baseline_metrics: PerformanceMetrics
) -> str:
    """
    Generate formatted comparison report.
    
    Args:
        adaptive_metrics: Metrics from adaptive system
        baseline_metrics: Metrics from fixed-timing baseline
    
    Returns:
        Formatted report string
    """
    comparison = adaptive_metrics.compare_to(baseline_metrics)
    
    report = f"""
{'='*70}
PERFORMANCE COMPARISON: Adaptive vs Fixed-Timing Baseline
{'='*70}

Metric                          Improvement
------                          -----------
Average Queue Length            {comparison['avg_queue_improvement']:+.1f}%
Peak Queue Length               {comparison['peak_queue_improvement']:+.1f}%
Total Delay Reduction           {comparison['delay_reduction']:+.1f}%
Throughput Improvement          {comparison['throughput_improvement']:+.1f}%

{'='*70}

{adaptive_metrics}

{baseline_metrics}

{'='*70}
CONCLUSION: {'Adaptive system shows significant improvement!' if comparison['delay_reduction'] > 10 else 'Results are comparable.'}
{'='*70}
"""
    
    return report
