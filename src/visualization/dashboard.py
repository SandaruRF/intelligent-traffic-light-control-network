"""
Real-time dashboard for visualizing traffic light system.

Provides live monitoring of:
- Intersection states (traffic light colors, queues)
- System-wide metrics
- Queue evolution graphs
- Communication logs
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from src.models.traffic_state import TrafficPhase


class TrafficDashboard:
    """
    Real-time visualization dashboard for the traffic light network.
    
    Creates a matplotlib figure with multiple panels:
    1. Network topology with traffic light states
    2. Queue length time series
    3. System metrics
    4. Performance indicators
    """
    
    def __init__(self, coordinator_agent=None):
        """
        Initialize dashboard.
        
        Args:
            coordinator_agent: Reference to coordinator agent for data access
        """
        self.coordinator = coordinator_agent
        
        # Setup figure
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle('Intelligent Traffic Light Control Network', 
                         fontsize=16, fontweight='bold')
        
        # Create subplots
        self._setup_subplots()
        
        # Data storage
        self.time_data = []
        self.queue_data = {
            "TL_CENTER": [],
            "TL_NORTH": [],
            "TL_SOUTH": [],
            "TL_EAST": [],
            "TL_WEST": []
        }
        
        self.start_time = datetime.now()
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    def _setup_subplots(self):
        """Create subplot layout."""
        # Grid: 3 rows x 2 columns
        
        # Row 1: Network topology (left), System metrics (right)
        self.ax_network = plt.subplot2grid((3, 2), (0, 0), rowspan=2)
        self.ax_metrics = plt.subplot2grid((3, 2), (0, 1))
        
        # Row 2: Queue graphs
        self.ax_queues = plt.subplot2grid((3, 2), (1, 1))
        
        # Row 3: Performance summary (full width)
        self.ax_performance = plt.subplot2grid((3, 2), (2, 0), colspan=2)
        
        # Configure axes
        self.ax_network.set_title('Network Topology')
        self.ax_network.axis('equal')
        self.ax_network.axis('off')
        
        self.ax_metrics.set_title('System Metrics')
        self.ax_metrics.axis('off')
        
        self.ax_queues.set_title('Queue Lengths Over Time')
        self.ax_queues.set_xlabel('Time (seconds)')
        self.ax_queues.set_ylabel('Vehicles Waiting')
        self.ax_queues.grid(True, alpha=0.3)
        
        self.ax_performance.set_title('Performance Indicators')
        self.ax_performance.axis('off')
    
    def draw_intersection(self, ax, x: float, y: float, name: str, 
                         phase: TrafficPhase, total_queue: int):
        """
        Draw a single intersection with traffic light visualization.
        
        Args:
            ax: Matplotlib axes
            x, y: Position coordinates
            name: Intersection name
            phase: Current traffic phase
            total_queue: Total vehicles waiting
        """
        # Determine colors based on axis activity
        axis = phase.active_axis()
        if axis == "NS":
            ns_color, ew_color = 'green', 'red'
        elif axis == "EW":
            ns_color, ew_color = 'red', 'green'
        else:
            ns_color = ew_color = 'red'
        
        # Draw intersection square
        square = patches.Rectangle(
            (x - 0.3, y - 0.3), 0.6, 0.6,
            linewidth=2, edgecolor='black', facecolor='lightgray'
        )
        ax.add_patch(square)
        
        # Draw traffic lights (small circles)
        # North-South lights
        ns_light = patches.Circle((x, y + 0.4), 0.1, color=ns_color, 
                                 edgecolor='black', linewidth=1)
        ax.add_patch(ns_light)
        
        # East-West lights
        ew_light = patches.Circle((x + 0.4, y), 0.1, color=ew_color,
                                 edgecolor='black', linewidth=1)
        ax.add_patch(ew_light)
        
        # Label
        ax.text(x, y, name.replace('TL_', ''), 
               ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Queue indicator
        queue_text = f'Q: {total_queue}'
        ax.text(x, y - 0.5, queue_text,
               ha='center', va='top', fontsize=9,
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
    
    def update_network_topology(self, states: Dict[str, Dict]):
        """
        Update network topology visualization.
        
        Args:
            states: Dictionary of intersection states
        """
        self.ax_network.clear()
        self.ax_network.set_title('Network Topology')
        self.ax_network.axis('equal')
        self.ax_network.axis('off')
        
        # Define positions (star topology)
        positions = {
            "TL_CENTER": (0, 0),
            "TL_NORTH": (0, 2),
            "TL_SOUTH": (0, -2),
            "TL_EAST": (2, 0),
            "TL_WEST": (-2, 0)
        }
        
        # Draw connections
        center_pos = positions["TL_CENTER"]
        for name, pos in positions.items():
            if name != "TL_CENTER":
                self.ax_network.plot([center_pos[0], pos[0]], 
                                   [center_pos[1], pos[1]],
                                   'k--', alpha=0.3, linewidth=1)
        
        # Draw intersections
        for name, pos in positions.items():
            if name in states:
                state = states[name]
                phase_str = state.get('phase', str(TrafficPhase.NS_STRAIGHT_RIGHT))
                phase = TrafficPhase.from_string(phase_str)
                total_queue = state.get('total_queue', 0)
                
                self.draw_intersection(
                    self.ax_network, pos[0], pos[1], name, phase, total_queue
                )
            else:
                # Draw inactive intersection
                self.draw_intersection(
                    self.ax_network, pos[0], pos[1], name, 
                    TrafficPhase.NS_STRAIGHT_RIGHT, 0
                )
        
        # Set limits
        self.ax_network.set_xlim(-3, 3)
        self.ax_network.set_ylim(-3, 3)
    
    def update_metrics_panel(self, metrics: Dict):
        """
        Update system metrics panel.
        
        Args:
            metrics: System metrics dictionary
        """
        self.ax_metrics.clear()
        self.ax_metrics.set_title('System Metrics')
        self.ax_metrics.axis('off')
        
        # Format metrics text
        metrics_text = f"""
Total Vehicles Waiting: {metrics.get('total_waiting', 0)}
Total Processed: {metrics.get('total_processed', 0)}
System Throughput: {metrics.get('throughput', 0):.2f} veh/min
Average Wait Time: {metrics.get('avg_wait_time', 0):.1f}s

Last Update: {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.ax_metrics.text(0.1, 0.5, metrics_text,
                           fontsize=11, verticalalignment='center',
                           family='monospace')
    
    def update_queue_graphs(self):
        """Update queue length time series graphs."""
        self.ax_queues.clear()
        self.ax_queues.set_title('Queue Lengths Over Time')
        self.ax_queues.set_xlabel('Time (seconds)')
        self.ax_queues.set_ylabel('Vehicles Waiting')
        self.ax_queues.grid(True, alpha=0.3)
        
        if not self.time_data:
            return
        
        # Plot each intersection's queue
        colors = {
            "TL_CENTER": 'red',
            "TL_NORTH": 'blue',
            "TL_SOUTH": 'green',
            "TL_EAST": 'orange',
            "TL_WEST": 'purple'
        }
        
        for intersection, color in colors.items():
            if intersection in self.queue_data and self.queue_data[intersection]:
                self.ax_queues.plot(
                    self.time_data[-len(self.queue_data[intersection]):],
                    self.queue_data[intersection],
                    label=intersection.replace('TL_', ''),
                    color=color,
                    linewidth=2,
                    marker='o',
                    markersize=3
                )
        
        self.ax_queues.legend(loc='upper right')
    
    def update_performance_panel(self, states: Dict[str, Dict]):
        """
        Update performance summary panel.
        
        Args:
            states: Dictionary of intersection states
        """
        self.ax_performance.clear()
        self.ax_performance.set_title('Performance Indicators')
        self.ax_performance.axis('off')
        
        if not states:
            return
        
        # Calculate per-intersection statistics
        performance_text = "Per-Intersection Status:\n\n"
        
        for name in ["TL_CENTER", "TL_NORTH", "TL_SOUTH", "TL_EAST", "TL_WEST"]:
            if name in states:
                state = states[name]
                performance_text += (
                    f"{name:12s}: "
                    f"Queue={state.get('total_queue', 0):3d}  "
                    f"Phase={state.get('phase', 'Unknown'):10s}  "
                    f"Cycle={state.get('cycle_count', 0):3d}\n"
                )
        
        self.ax_performance.text(0.1, 0.5, performance_text,
                               fontsize=10, verticalalignment='center',
                               family='monospace')
    
    def update(self, states: Dict[str, Dict], metrics: Dict):
        """
        Update all dashboard panels.
        
        Args:
            states: Dictionary of intersection states
            metrics: System metrics
        """
        # Update time data
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.time_data.append(elapsed)
        
        # Update queue data
        for name in self.queue_data.keys():
            if name in states:
                self.queue_data[name].append(states[name].get('total_queue', 0))
            else:
                self.queue_data[name].append(0)
        
        # Keep only recent data (last 100 points)
        if len(self.time_data) > 100:
            self.time_data = self.time_data[-100:]
            for name in self.queue_data:
                self.queue_data[name] = self.queue_data[name][-100:]
        
        # Update all panels
        self.update_network_topology(states)
        self.update_metrics_panel(metrics)
        self.update_queue_graphs()
        self.update_performance_panel(states)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    def show(self):
        """Display the dashboard (blocking)."""
        plt.show()
    
    def save(self, filename: str):
        """
        Save current dashboard to file.
        
        Args:
            filename: Output filename (e.g., 'dashboard.png')
        """
        self.fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Dashboard saved to {filename}")


def create_animated_dashboard(coordinator_agent, update_interval: int = 1000):
    """
    Create animated dashboard that updates automatically.
    
    Args:
        coordinator_agent: Coordinator agent instance
        update_interval: Update interval in milliseconds (default 1000ms = 1s)
    
    Returns:
        TrafficDashboard instance with animation
    """
    dashboard = TrafficDashboard(coordinator_agent)
    
    def update_frame(frame):
        """Animation update function."""
        if coordinator_agent and coordinator_agent.is_alive():
            states = coordinator_agent.get_all_current_states()
            metrics = coordinator_agent.get_system_metrics()
            dashboard.update(states, metrics)
    
    animation = FuncAnimation(
        dashboard.fig,
        update_frame,
        interval=update_interval,
        blit=False
    )
    
    return dashboard, animation


def create_static_dashboard(states: Dict[str, Dict], metrics: Dict) -> TrafficDashboard:
    """
    Create static dashboard snapshot.
    
    Args:
        states: Intersection states
        metrics: System metrics
    
    Returns:
        TrafficDashboard instance
    """
    dashboard = TrafficDashboard()
    dashboard.update(states, metrics)
    return dashboard
