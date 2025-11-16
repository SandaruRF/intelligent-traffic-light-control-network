"""
Real-time GUI Traffic Simulation using Pygame.

This module provides a visual interface showing:
- Traffic light states (red/green)
- Vehicle queues in each direction
- Real-time congestion levels
- System metrics

Runs in a separate thread alongside terminal output.
"""

import pygame
import threading
import time
from typing import Dict, Optional
from datetime import datetime
import math


class TrafficGUISimulator:
    """
    Interactive GUI showing traffic flow and congestion in real-time.
    
    Features:
    - 5 intersections in star topology
    - Color-coded traffic lights (red/green)
    - Animated vehicles in queues
    - Congestion heatmap
    - System metrics panel
    """
    
    def __init__(self, width: int = 1400, height: int = 900):
        """Initialize the GUI simulator."""
        pygame.init()
        
        # Window setup
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("🚦 Intelligent Traffic Light Control Network - Live Simulation")
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.RED = (220, 50, 50)
        self.GREEN = (50, 200, 50)
        self.YELLOW = (255, 215, 0)
        self.BLUE = (70, 130, 255)
        self.GRAY = (100, 100, 100)
        self.LIGHT_GRAY = (200, 200, 200)
        self.ORANGE = (255, 140, 0)
        self.DARK_GREEN = (0, 100, 0)
        
        # Fonts
        self.font_large = pygame.font.SysFont('Arial', 24, bold=True)
        self.font_medium = pygame.font.SysFont('Arial', 18)
        self.font_small = pygame.font.SysFont('Arial', 14)
        self.font_tiny = pygame.font.SysFont('Arial', 12)
        
        # Intersection positions (center at 700, 450)
        self.positions = {
            "TL_CENTER": (700, 450),
            "TL_NORTH": (700, 150),
            "TL_SOUTH": (700, 750),
            "TL_EAST": (1000, 450),
            "TL_WEST": (400, 450)
        }
        
        # State data
        self.intersection_states: Dict[str, Dict] = {}
        self.system_metrics: Dict = {
            "total_waiting": 0,
            "throughput": 0.0,
            "total_processed": 0,
            "avg_queue": 0.0
        }
        
        # Animation
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.clock = pygame.time.Clock()
        self.frame_count = 0
        
    def start(self):
        """Start the GUI in a separate thread."""
        self.running = True
        self.thread = threading.Thread(target=self._run_gui, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop the GUI."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        pygame.quit()
        
    def update_intersection(self, name: str, state: Dict):
        """
        Update intersection state.
        
        Args:
            name: Intersection name (e.g., "TL_CENTER")
            state: State dictionary with phase, queues, etc.
        """
        self.intersection_states[name] = state
        
    def update_metrics(self, metrics: Dict):
        """
        Update system metrics.
        
        Args:
            metrics: Dictionary with system-wide metrics
        """
        self.system_metrics = metrics
        
    def _run_gui(self):
        """Main GUI loop (runs in separate thread)."""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Draw components
            self._draw_title()
            self._draw_roads()
            self._draw_intersections()
            self._draw_vehicles()
            self._draw_metrics_panel()
            self._draw_legend()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(30)  # 30 FPS
            self.frame_count += 1
            
    def _draw_title(self):
        """Draw title bar."""
        title = self.font_large.render("🚦 Intelligent Traffic Light Control Network", True, self.WHITE)
        self.screen.blit(title, (20, 20))
        
        subtitle = self.font_small.render("Multi-Agent System Simulation - Real-time View", True, self.LIGHT_GRAY)
        self.screen.blit(subtitle, (20, 50))
        
    def _draw_roads(self):
        """Draw road network."""
        center_x, center_y = self.positions["TL_CENTER"]
        
        # Horizontal road (East-West)
        pygame.draw.rect(self.screen, self.GRAY, (50, center_y - 40, 1300, 80))
        # Center line
        for x in range(50, 1350, 40):
            pygame.draw.line(self.screen, self.YELLOW, (x, center_y), (x + 20, center_y), 2)
            
        # Vertical road (North-South)
        pygame.draw.rect(self.screen, self.GRAY, (center_x - 40, 50, 80, 800))
        # Center line
        for y in range(50, 850, 40):
            pygame.draw.line(self.screen, self.YELLOW, (center_x, y), (center_x, y + 20), 2)
            
    def _draw_intersections(self):
        """Draw all intersections with traffic lights."""
        for name, pos in self.positions.items():
            state = self.intersection_states.get(name, {})
            self._draw_intersection(name, pos, state)
            
    def _draw_intersection(self, name: str, pos: tuple, state: Dict):
        """
        Draw a single intersection with traffic light.
        
        Args:
            name: Intersection name
            pos: (x, y) position
            state: Current state dictionary
        """
        x, y = pos
        
        # Get state info
        phase = state.get("phase", "NS-Green")
        queues = state.get("queues", {"N": 0, "S": 0, "E": 0, "W": 0})
        total_queue = state.get("total_queue", 0)
        cycle = state.get("cycle_count", 0)
        processed = state.get("vehicles_processed", 0)
        
        # Intersection box (congestion color-coded)
        if total_queue > 20:
            bg_color = (150, 0, 0)  # Dark red
        elif total_queue > 10:
            bg_color = (200, 100, 0)  # Orange
        elif total_queue > 5:
            bg_color = (200, 200, 0)  # Yellow-ish
        else:
            bg_color = (0, 100, 0)  # Green
            
        pygame.draw.rect(self.screen, bg_color, (x - 60, y - 60, 120, 120))
        pygame.draw.rect(self.screen, self.WHITE, (x - 60, y - 60, 120, 120), 3)
        
        # Intersection name
        name_short = name.replace("TL_", "")
        text = self.font_medium.render(name_short, True, self.WHITE)
        text_rect = text.get_rect(center=(x, y - 35))
        self.screen.blit(text, text_rect)
        
        # Traffic lights (4 directions)
        self._draw_traffic_light(x, y - 20, phase, "NS")  # North
        self._draw_traffic_light(x, y + 20, phase, "NS")  # South
        self._draw_traffic_light(x - 20, y, phase, "EW")  # West
        self._draw_traffic_light(x + 20, y, phase, "EW")  # East
        
        # Queue numbers
        queue_text = self.font_small.render(f"Q:{total_queue}", True, self.WHITE)
        self.screen.blit(queue_text, (x - 25, y + 35))
        
        # Cycle count
        cycle_text = self.font_tiny.render(f"C:{cycle}", True, self.LIGHT_GRAY)
        self.screen.blit(cycle_text, (x - 25, y + 50))
        
        # Draw queue indicators
        self._draw_queue_indicators(x, y, queues)
        
    def _draw_traffic_light(self, x: int, y: int, phase: str, direction: str):
        """
        Draw a traffic light signal.
        
        Args:
            x, y: Position
            phase: Current phase (e.g., "NS-Green")
            direction: "NS" or "EW"
        """
        # Determine if this direction has green
        is_green = False
        if "NS" in phase and direction == "NS":
            is_green = True
        elif "EW" in phase and direction == "EW":
            is_green = True
            
        color = self.GREEN if is_green else self.RED
        pygame.draw.circle(self.screen, color, (x, y), 8)
        pygame.draw.circle(self.screen, self.WHITE, (x, y), 8, 1)
        
    def _draw_queue_indicators(self, x: int, y: int, queues: Dict):
        """
        Draw queue length indicators around intersection.
        
        Args:
            x, y: Intersection center
            queues: Queue dictionary {"N": int, "S": int, "E": int, "W": int}
        """
        # North queue
        self._draw_queue_bar(x, y - 100, queues.get("N", 0), "vertical")
        # South queue
        self._draw_queue_bar(x, y + 100, queues.get("S", 0), "vertical")
        # East queue
        self._draw_queue_bar(x + 100, y, queues.get("E", 0), "horizontal")
        # West queue
        self._draw_queue_bar(x - 100, y, queues.get("W", 0), "horizontal")
        
    def _draw_queue_bar(self, x: int, y: int, queue_length: int, orientation: str):
        """
        Draw a queue length bar.
        
        Args:
            x, y: Position
            queue_length: Number of vehicles
            orientation: "vertical" or "horizontal"
        """
        if queue_length == 0:
            return
            
        # Color based on congestion
        if queue_length > 15:
            color = self.RED
        elif queue_length > 8:
            color = self.ORANGE
        else:
            color = self.YELLOW
            
        # Draw bar
        max_length = 60
        bar_length = min(queue_length * 3, max_length)
        
        if orientation == "vertical":
            pygame.draw.rect(self.screen, color, (x - 5, y - bar_length // 2, 10, bar_length))
            # Number
            text = self.font_tiny.render(str(queue_length), True, self.WHITE)
            self.screen.blit(text, (x + 10, y - 5))
        else:  # horizontal
            pygame.draw.rect(self.screen, color, (x - bar_length // 2, y - 5, bar_length, 10))
            # Number
            text = self.font_tiny.render(str(queue_length), True, self.WHITE)
            self.screen.blit(text, (x - 5, y + 10))
            
    def _draw_vehicles(self):
        """Draw animated vehicles in queues."""
        for name, pos in self.positions.items():
            state = self.intersection_states.get(name, {})
            queues = state.get("queues", {"N": 0, "S": 0, "E": 0, "W": 0})
            
            x, y = pos
            
            # Draw vehicles approaching from each direction
            # North (vehicles moving south)
            self._draw_vehicle_queue(x, y - 140, queues.get("N", 0), "down")
            # South (vehicles moving north)
            self._draw_vehicle_queue(x, y + 140, queues.get("S", 0), "up")
            # East (vehicles moving west)
            self._draw_vehicle_queue(x + 140, y, queues.get("E", 0), "left")
            # West (vehicles moving east)
            self._draw_vehicle_queue(x - 140, y, queues.get("W", 0), "right")
            
    def _draw_vehicle_queue(self, x: int, y: int, count: int, direction: str):
        """
        Draw vehicles in a queue.
        
        Args:
            x, y: Starting position
            count: Number of vehicles
            direction: "up", "down", "left", "right"
        """
        vehicle_size = 8
        spacing = 12
        
        for i in range(min(count, 8)):  # Draw max 8 vehicles
            offset = i * spacing
            
            if direction == "down":
                vx, vy = x, y + offset
            elif direction == "up":
                vx, vy = x, y - offset
            elif direction == "right":
                vx, vy = x + offset, y
            else:  # left
                vx, vy = x - offset, y
                
            # Vehicle color (alternating for animation)
            if (self.frame_count // 10 + i) % 2 == 0:
                color = self.BLUE
            else:
                color = (100, 150, 255)
                
            pygame.draw.rect(self.screen, color, (vx - vehicle_size // 2, vy - vehicle_size // 2, vehicle_size, vehicle_size))
            pygame.draw.rect(self.screen, self.WHITE, (vx - vehicle_size // 2, vy - vehicle_size // 2, vehicle_size, vehicle_size), 1)
            
    def _draw_metrics_panel(self):
        """Draw system metrics panel."""
        panel_x = 20
        panel_y = 100
        panel_width = 320
        panel_height = 280
        
        # Panel background
        pygame.draw.rect(self.screen, (30, 30, 30), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, self.WHITE, (panel_x, panel_y, panel_width, panel_height), 2)
        
        # Title
        title = self.font_medium.render("System Metrics", True, self.WHITE)
        self.screen.blit(title, (panel_x + 10, panel_y + 10))
        
        # Metrics
        y_offset = panel_y + 45
        
        metrics = [
            ("Total Waiting:", str(self.system_metrics.get("total_waiting", 0)), self.ORANGE),
            ("Avg Queue:", f"{self.system_metrics.get('avg_queue', 0):.1f}", self.YELLOW),
            ("Throughput:", f"{self.system_metrics.get('throughput', 0):.1f}/min", self.GREEN),
            ("Total Processed:", str(self.system_metrics.get("total_processed", 0)), self.BLUE),
        ]
        
        for label, value, color in metrics:
            # Label
            text = self.font_small.render(label, True, self.LIGHT_GRAY)
            self.screen.blit(text, (panel_x + 15, y_offset))
            
            # Value
            val_text = self.font_medium.render(value, True, color)
            self.screen.blit(val_text, (panel_x + 160, y_offset - 2))
            
            y_offset += 35
            
        # Status indicator
        y_offset += 15
        status_text = self.font_small.render("Status:", True, self.LIGHT_GRAY)
        self.screen.blit(status_text, (panel_x + 15, y_offset))
        
        # Active agents count
        active_count = len(self.intersection_states)
        if active_count >= 5:
            status = "OPERATIONAL"
            status_color = self.GREEN
        elif active_count > 0:
            status = "PARTIAL"
            status_color = self.ORANGE
        else:
            status = "OFFLINE"
            status_color = self.RED
            
        status_val = self.font_medium.render(status, True, status_color)
        self.screen.blit(status_val, (panel_x + 80, y_offset - 2))
        
        # Agent count
        y_offset += 30
        agent_text = self.font_small.render(f"Active Agents: {active_count}/5", True, self.WHITE)
        self.screen.blit(agent_text, (panel_x + 15, y_offset))
        
    def _draw_legend(self):
        """Draw legend explaining colors."""
        legend_x = 1050
        legend_y = 100
        
        # Background
        pygame.draw.rect(self.screen, (30, 30, 30), (legend_x, legend_y, 320, 220))
        pygame.draw.rect(self.screen, self.WHITE, (legend_x, legend_y, 320, 220), 2)
        
        # Title
        title = self.font_medium.render("Legend", True, self.WHITE)
        self.screen.blit(title, (legend_x + 10, legend_y + 10))
        
        y_offset = legend_y + 45
        
        # Legend items
        items = [
            ("Traffic Light:", self.GREEN, "Green - Active"),
            ("", self.RED, "Red - Stopped"),
            ("Congestion:", (0, 100, 0), "Low (0-5)"),
            ("", (200, 200, 0), "Medium (6-10)"),
            ("", (200, 100, 0), "High (11-20)"),
            ("", (150, 0, 0), "Critical (>20)"),
        ]
        
        for label, color, desc in items:
            if label:
                text = self.font_small.render(label, True, self.LIGHT_GRAY)
                self.screen.blit(text, (legend_x + 15, y_offset))
                
            # Color square
            pygame.draw.rect(self.screen, color, (legend_x + 15, y_offset + 20, 20, 15))
            pygame.draw.rect(self.screen, self.WHITE, (legend_x + 15, y_offset + 20, 20, 15), 1)
            
            # Description
            desc_text = self.font_tiny.render(desc, True, self.WHITE)
            self.screen.blit(desc_text, (legend_x + 45, y_offset + 22))
            
            y_offset += 28


# Global instance
_gui_instance: Optional[TrafficGUISimulator] = None


def start_gui() -> TrafficGUISimulator:
    """
    Start the GUI simulator.
    
    Returns:
        TrafficGUISimulator instance
    """
    global _gui_instance
    if _gui_instance is None:
        _gui_instance = TrafficGUISimulator()
        _gui_instance.start()
        time.sleep(0.5)  # Give it time to initialize
    return _gui_instance


def stop_gui():
    """Stop the GUI simulator."""
    global _gui_instance
    if _gui_instance:
        _gui_instance.stop()
        _gui_instance = None


def get_gui() -> Optional[TrafficGUISimulator]:
    """Get the current GUI instance."""
    return _gui_instance
