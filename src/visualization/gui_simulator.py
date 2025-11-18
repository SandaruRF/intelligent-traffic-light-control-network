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
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.models.traffic_state import TrafficPhase


@dataclass
class Vehicle:
    """Represents a single vehicle sprite travelling through the junction."""
    approach: str
    movement: str
    lane_offset: float
    active: bool = False
    progress: float = 0.0
    speed: float = 0.3  # normalized units per second
    position: Tuple[int, int] = (0, 0)
    path: Optional[Dict[str, Tuple[int, int]]] = None


class TrafficGUISimulator:
    """
    Interactive GUI showing traffic flow and congestion in real-time.
    
    Features:
    - Single four-way junction with angled approaches
    - Movement-level signal indicators (left/straight/right)
    - Animated lane queues per approach
    - Real-time congestion panels and metrics
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
        self.GRAY = (90, 90, 90)
        self.LIGHT_GRAY = (200, 200, 200)
        self.ORANGE = (255, 140, 0)
        self.DARK_GREEN = (0, 100, 0)
        self.ROAD_DARK = (60, 60, 60)
        self.ROAD_LIGHT = (80, 80, 80)
        
        # Fonts
        self.font_large = pygame.font.SysFont('Arial', 24, bold=True)
        self.font_medium = pygame.font.SysFont('Arial', 18)
        self.font_small = pygame.font.SysFont('Arial', 14)
        self.font_tiny = pygame.font.SysFont('Arial', 12)
        
        # Geometry for single junction (centered diamond layout)
        self.center = (self.width // 2, self.height // 2 + 40)
        self.approach_configs = {
            "TL_NORTH": {
                "direction": "N",
                "vector": (0.0, -1.0),
                "panel_pos": (self.center[0] - 140, self.center[1] - 250)
            },
            "TL_SOUTH": {
                "direction": "S",
                "vector": (0.0, 1.0),
                "panel_pos": (self.center[0] - 140, self.center[1] + 210)
            },
            "TL_EAST": {
                "direction": "E",
                "vector": (1.0, 0.0),
                "panel_pos": (self.center[0] + 180, self.center[1] - 30)
            },
            "TL_WEST": {
                "direction": "W",
                "vector": (-1.0, 0.0),
                "panel_pos": (self.center[0] - 320, self.center[1] - 30)
            }
        }
        self.approach_polygons = {
            name: self._create_approach_polygon(cfg["vector"])
            for name, cfg in self.approach_configs.items()
        }
        self.center_polygon = self._create_center_diamond()
        
        # Six-lane configuration: three inbound (facing intersection), three outbound (leaving)
        # Inbound offsets: left=0 (closest to center divider), straight=-20, right=-40
        # Outbound offsets: left=40, straight=20, right=0 (closest to center divider)
        self.inbound_lane_offsets = {"left": 0, "straight": -20, "right": -40}
        self.outbound_lane_offsets = {"left": 40, "straight": 20, "right": 0}
        self.lane_offsets = self.inbound_lane_offsets  # alias for waiting vehicle creation
        self.exit_lane_offsets = self.outbound_lane_offsets  # alias for exit path building
        self.movement_colors = {
            "left": self.ORANGE,
            "straight": self.GREEN,
            "right": self.BLUE
        }
        self.movement_labels = {"left": "L", "straight": "S", "right": "R"}
        self.movement_targets = {
            "TL_NORTH": {"straight": "TL_SOUTH", "left": "TL_EAST", "right": "TL_WEST"},
            "TL_SOUTH": {"straight": "TL_NORTH", "left": "TL_WEST", "right": "TL_EAST"},
            "TL_EAST": {"straight": "TL_WEST", "left": "TL_SOUTH", "right": "TL_NORTH"},
            "TL_WEST": {"straight": "TL_EAST", "left": "TL_NORTH", "right": "TL_SOUTH"}
        }
        
        self.vehicle_spawn_distance = 280
        self.vehicle_entry_distance = 90
        self.vehicle_wait_spacing = 18
        self.vehicle_size = (12, 8)
        self.vehicle_speed_range = (0.25, 0.5)
        
        self.waiting_queues: Dict[str, Dict[str, List[Vehicle]]] = {
            name: {move: [] for move in self.movement_labels}
            for name in self.approach_configs
        }
        self.active_vehicles: List[Vehicle] = []
        self.release_cooldowns: Dict[str, Dict[str, float]] = {
            name: {move: 0.0 for move in self.movement_labels}
            for name in self.approach_configs
        }
        
        # State data
        self.intersection_states: Dict[str, Dict] = {}
        self.system_metrics: Dict = {
            "total_waiting": 0,
            "throughput": 0.0,
            "total_processed": 0,
            "avg_queue": 0.0,
            "active_phase": str(TrafficPhase.NS_STRAIGHT_RIGHT),
            "axis_loads": {"NS": 0, "EW": 0}
        }
        self.state_lock = threading.Lock()
        
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
        with self.state_lock:
            self.intersection_states[name] = state
            self._sync_waiting_queue(name, state)
        
    def update_metrics(self, metrics: Dict):
        """
        Update system metrics.
        
        Args:
            metrics: Dictionary with system-wide metrics
        """
        with self.state_lock:
            self.system_metrics = metrics

    def _sync_waiting_queue(self, name: str, state: Dict) -> None:
        if name not in self.waiting_queues:
            return
        queues = state.get("queues", {})
        for movement in self.movement_labels:
            target = max(0, queues.get(movement, 0))
            lane_queue = self.waiting_queues[name][movement]
            diff = target - len(lane_queue)
            if diff > 0:
                for _ in range(diff):
                    lane_queue.append(self._create_waiting_vehicle(name, movement))
            elif diff < 0:
                for _ in range(-diff):
                    if lane_queue:
                        lane_queue.pop()
        self._update_waiting_positions(name)

    def _create_waiting_vehicle(self, name: str, movement: str) -> Vehicle:
        lane_offset = self.lane_offsets[movement]
        vehicle = Vehicle(
            approach=name,
            movement=movement,
            lane_offset=lane_offset,
            speed=random.uniform(*self.vehicle_speed_range)
        )
        vehicle.position = self._point_on_approach(name, self.vehicle_entry_distance, lane_offset)
        return vehicle

    def _update_waiting_positions(self, name: str) -> None:
        base_distance = self.vehicle_entry_distance
        for movement, lane_queue in self.waiting_queues[name].items():
            for idx, vehicle in enumerate(lane_queue):
                distance = base_distance + idx * self.vehicle_wait_spacing
                vehicle.position = self._point_on_approach(name, distance, vehicle.lane_offset)
        
    def _run_gui(self):
        """Main GUI loop (runs in separate thread)."""
        while self.running:
            dt = self.clock.tick(50) / 1000.0  # target 50 FPS
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            self._update_vehicle_system(dt)
            
            self.screen.fill(self.BLACK)
            self._draw_title()
            self._draw_roads()
            self._draw_intersections()
            self._draw_active_vehicles()
            self._draw_metrics_panel()
            self._draw_legend()
            pygame.display.flip()
            self.frame_count += 1
            
    def _draw_title(self):
        """Draw title bar."""
        title = self.font_large.render("🚦 Intelligent Traffic Light Control Network", True, self.WHITE)
        self.screen.blit(title, (20, 20))
        
        subtitle = self.font_small.render("Multi-Agent System Simulation - Real-time View", True, self.LIGHT_GRAY)
        self.screen.blit(subtitle, (20, 50))
    
    def _update_vehicle_system(self, dt: float) -> None:
        with self.state_lock:
            for name, state in self.intersection_states.items():
                allowed = state.get("green_movements", [])
                for movement in allowed:
                    self._maybe_release_vehicle(name, movement, dt)
            self._advance_active_vehicles(dt)

    def _maybe_release_vehicle(self, name: str, movement: str, dt: float) -> None:
        if name not in self.waiting_queues:
            return
        cooldown = self.release_cooldowns[name][movement]
        cooldown = max(0.0, cooldown - dt)
        lane_queue = self.waiting_queues[name][movement]
        if cooldown <= 0 and lane_queue:
            vehicle = lane_queue.pop(0)
            vehicle.active = True
            vehicle.progress = 0.0
            vehicle.speed = random.uniform(*self.vehicle_speed_range)
            vehicle.path = self._build_path(vehicle, start_override=vehicle.position)
            self.active_vehicles.append(vehicle)
            cooldown = 0.45  # seconds before next vehicle in same lane
            self._update_waiting_positions(name)
        self.release_cooldowns[name][movement] = cooldown

    def _advance_active_vehicles(self, dt: float) -> None:
        removal: List[Vehicle] = []
        for vehicle in self.active_vehicles:
            vehicle.progress += vehicle.speed * dt
            vehicle.position = self._path_position(vehicle)
            if vehicle.progress >= 1.05:
                removal.append(vehicle)
        for vehicle in removal:
            self.active_vehicles.remove(vehicle)

    def _build_path(self, vehicle: Vehicle, start_override: Optional[Tuple[int, int]] = None) -> Dict:
        # Vehicle starts in its inbound lane at current approach
        start = start_override or self._point_on_approach(
            vehicle.approach,
            self.vehicle_spawn_distance,
            vehicle.lane_offset
        )
        # Vehicle exits into the corresponding outbound lane of the target approach
        target_approach = self.movement_targets[vehicle.approach][vehicle.movement]
        # Map movement to outbound lane on target road (left->left, straight->straight, right->right)
        exit_offset = self.outbound_lane_offsets[vehicle.movement]
        end = self._point_on_approach(target_approach, self.vehicle_spawn_distance, exit_offset)
        
        if vehicle.movement == "straight":
            return {"type": "line", "start": start, "end": end}
        
        # Turning movements use curved paths
        approach_vec = self.approach_configs[vehicle.approach]["vector"]
        perp = (-approach_vec[1], approach_vec[0])
        curvature = 85 if vehicle.movement == "left" else -85
        control = (
            self.center[0] + perp[0] * curvature,
            self.center[1] + perp[1] * curvature
        )
        return {"type": "curve", "start": start, "control": control, "end": end}

    def _path_position(self, vehicle: Vehicle) -> Tuple[int, int]:
        if not vehicle.path:
            return vehicle.position
        t = min(1.0, max(0.0, vehicle.progress))
        if vehicle.path["type"] == "line":
            return self._lerp(vehicle.path["start"], vehicle.path["end"], t)
        return self._quadratic_bezier(
            vehicle.path["start"],
            vehicle.path["control"],
            vehicle.path["end"],
            t
        )

    @staticmethod
    def _lerp(a: Tuple[int, int], b: Tuple[int, int], t: float) -> Tuple[int, int]:
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t)
        )

    @staticmethod
    def _quadratic_bezier(p0: Tuple[int, int], p1: Tuple[int, int], p2: Tuple[int, int], t: float) -> Tuple[int, int]:
        u = 1 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        return (int(x), int(y))
        
    def _draw_roads(self):
        """Draw single-junction diamond road layout with angled approaches."""
        for name, polygon in self.approach_polygons.items():
            pygame.draw.polygon(self.screen, self.ROAD_DARK, polygon)
            pygame.draw.polygon(self.screen, self.GRAY, polygon, 2)
            self._draw_lane_markings(name)
        
        # Central diamond intersection
        pygame.draw.polygon(self.screen, (50, 50, 50), self.center_polygon)
        pygame.draw.polygon(self.screen, self.WHITE, self.center_polygon, 2)
        self._draw_intersection_status()

    def _draw_intersections(self):
        """Render approach-level panels, signals, and vehicle queues."""
        with self.state_lock:
            states = {name: dict(state) for name, state in self.intersection_states.items()}
            waiting_snapshot = {}
            for name in self.approach_configs:
                lanes = self.waiting_queues.get(name, {})
                waiting_snapshot[name] = {
                    movement: [vehicle.position for vehicle in lanes.get(movement, [])]
                    for movement in self.movement_labels
                }
        for name, cfg in self.approach_configs.items():
            state = states.get(name, {})
            lane_positions = waiting_snapshot.get(name, {})
            self._draw_signal_cluster(name, state)
            self._draw_waiting_vehicles(lane_positions)
            self._draw_queue_panel(name, cfg, state)
            
    def _draw_signal_cluster(self, name: str, state: Dict):
        """Render movement-level signal indicators for an approach."""
        allowed = set(state.get("green_movements", []))
        # Position signals above the three inbound lanes
        for movement, offset in self.inbound_lane_offsets.items():
            indicator_pos = self._point_on_approach(name, 60, offset)
            color = self.GREEN if movement in allowed else self.RED
            pygame.draw.circle(self.screen, color, indicator_pos, 10)
            pygame.draw.circle(self.screen, self.WHITE, indicator_pos, 10, 2)
            label = self.font_tiny.render(self.movement_labels[movement], True, self.BLACK if movement in allowed else self.WHITE)
            label_rect = label.get_rect(center=indicator_pos)
            self.screen.blit(label, label_rect)

    def _draw_waiting_vehicles(self, lane_positions: Dict[str, List[Tuple[int, int]]]) -> None:
        for movement, positions in lane_positions.items():
            for pos in positions:
                self._draw_vehicle_box(pos, idle=True)

    def _draw_vehicle_box(self, position: Tuple[int, int], idle: bool = False) -> None:
        if not position:
            return
        width, height = self.vehicle_size
        rect = pygame.Rect(0, 0, width, height)
        rect.center = position
        color = (90, 150, 255) if idle else self.BLUE
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.WHITE, rect, 1)

    def _draw_active_vehicles(self) -> None:
        with self.state_lock:
            positions = [vehicle.position for vehicle in self.active_vehicles]
        for pos in positions:
            self._draw_vehicle_box(pos, idle=False)

    def _draw_queue_panel(self, name: str, cfg: Dict, state: Dict):
        panel_x, panel_y = cfg["panel_pos"]
        panel_width = 140
        panel_height = 70
        pygame.draw.rect(self.screen, (25, 25, 25), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, self.WHITE, (panel_x, panel_y, panel_width, panel_height), 1)
        label = self.font_small.render(f"{cfg['direction']} | Q:{state.get('total_queue', 0)}", True, self.WHITE)
        self.screen.blit(label, (panel_x + 8, panel_y + 6))
        queues = state.get("queues", {"left": 0, "straight": 0, "right": 0})
        detail = self.font_tiny.render(
            f"L:{queues.get('left', 0)} S:{queues.get('straight', 0)} R:{queues.get('right', 0)}",
            True,
            self.LIGHT_GRAY
        )
        self.screen.blit(detail, (panel_x + 8, panel_y + 28))
        processed = state.get("vehicles_processed", 0)
        proc_text = self.font_tiny.render(f"Proc:{processed}", True, self.LIGHT_GRAY)
        self.screen.blit(proc_text, (panel_x + 8, panel_y + 48))

    def _draw_metrics_panel(self):
        """Draw system metrics panel."""
        panel_x = 20
        panel_y = 100
        panel_width = 330
        panel_height = 320
        
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
            ("Active Phase:", self._current_phase(), self.LIGHT_GRAY)
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
        
        active_count = len(self.intersection_states)
        status = "OPERATIONAL" if active_count == 4 else ("PARTIAL" if active_count > 0 else "OFFLINE")
        status_color = self.GREEN if status == "OPERATIONAL" else (self.ORANGE if status == "PARTIAL" else self.RED)
        status_val = self.font_medium.render(status, True, status_color)
        self.screen.blit(status_val, (panel_x + 110, y_offset - 2))
        y_offset += 30
        agent_text = self.font_small.render(f"Active Agents: {active_count}/4", True, self.WHITE)
        self.screen.blit(agent_text, (panel_x + 15, y_offset))
        
        # Per-approach snapshot
        y_offset += 20
        header = self.font_small.render("Approach Queues", True, self.LIGHT_GRAY)
        self.screen.blit(header, (panel_x + 15, y_offset))
        y_offset += 20
        for name in ["TL_NORTH", "TL_EAST", "TL_SOUTH", "TL_WEST"]:
            state = self.intersection_states.get(name)
            queue = state.get("total_queue", 0) if state else 0
            label = name.replace("TL_", "")
            text = self.font_tiny.render(f"{label:<5} {queue:>2} veh", True, self.WHITE)
            self.screen.blit(text, (panel_x + 20, y_offset))
            y_offset += 16
        axis_loads = self.system_metrics.get("axis_loads", {})
        axis_text = self.font_tiny.render(
            f"Axis Load NS:{axis_loads.get('NS', 0)} | EW:{axis_loads.get('EW', 0)}",
            True,
            self.LIGHT_GRAY
        )
        self.screen.blit(axis_text, (panel_x + 15, panel_y + panel_height - 30))
        
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
            ("Lane Colors:", self.movement_colors["left"], "Left turns"),
            ("", self.movement_colors["straight"], "Straight"),
            ("", self.movement_colors["right"], "Right turns"),
            ("Signals:", self.GREEN, "Movement permitted"),
            ("", self.RED, "Movement stopped"),
            ("Center Text:", self.WHITE, "Active NS/EW phase"),
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

    def _draw_lane_markings(self, approach_name: str) -> None:
        start_distance = 80
        end_distance = 260
        dash_length = 20
        dash_gap = 10
        
        # Six-lane setup: three inbound (left at -40, straight -20, right 0), three outbound (left 0, straight 20, right 40)
        # Center divider at 0
        inbound_lane_boundaries = [-50, -40, -20, 0]  # left edge, L|S boundary, S|R boundary, center divider
        outbound_lane_boundaries = [0, 20, 40, 50]  # center divider, L|S boundary, S|R boundary, right edge
        
        # Outer road edges (solid)
        for lateral in [-50, 50]:
            start = self._point_on_approach(approach_name, start_distance, lateral)
            end = self._point_on_approach(approach_name, end_distance, lateral)
            pygame.draw.line(self.screen, self.LIGHT_GRAY, start, end, 3)
        
        # Center divider (double solid yellow)
        for offset in [-1, 1]:
            start = self._point_on_approach(approach_name, start_distance, offset)
            end = self._point_on_approach(approach_name, end_distance, offset)
            pygame.draw.line(self.screen, self.YELLOW, start, end, 2)
        
        # Inbound lane markers (dashed white)
        for lateral in [-40, -20]:
            distance = start_distance
            while distance < end_distance:
                dash_end = min(distance + dash_length, end_distance)
                seg_start = self._point_on_approach(approach_name, distance, lateral)
                seg_end = self._point_on_approach(approach_name, dash_end, lateral)
                pygame.draw.line(self.screen, self.WHITE, seg_start, seg_end, 2)
                distance += dash_length + dash_gap
        
        # Outbound lane markers (dashed white)
        for lateral in [20, 40]:
            distance = start_distance
            while distance < end_distance:
                dash_end = min(distance + dash_length, end_distance)
                seg_start = self._point_on_approach(approach_name, distance, lateral)
                seg_end = self._point_on_approach(approach_name, dash_end, lateral)
                pygame.draw.line(self.screen, self.WHITE, seg_start, seg_end, 2)
                distance += dash_length + dash_gap

    def _draw_intersection_status(self) -> None:
        phase = self._current_phase()
        label = self.font_small.render(f"Active Phase: {phase}", True, self.WHITE)
        label_rect = label.get_rect(center=(self.center[0], self.center[1] - 10))
        self.screen.blit(label, label_rect)

    def _current_phase(self) -> str:
        if self.system_metrics.get("active_phase"):
            return self.system_metrics["active_phase"]
        for state in self.intersection_states.values():
            return state.get("phase", str(TrafficPhase.NS_STRAIGHT_RIGHT))
        return str(TrafficPhase.NS_STRAIGHT_RIGHT)

    def _point_on_approach(self, name: str, distance: float, lateral: float) -> Tuple[int, int]:
        cfg = self.approach_configs[name]
        vec_x, vec_y = cfg["vector"]
        perp_x, perp_y = -vec_y, vec_x
        x = self.center[0] + vec_x * distance + perp_x * lateral
        y = self.center[1] + vec_y * distance + perp_y * lateral
        return int(x), int(y)

    def _create_approach_polygon(self, vector: Tuple[float, float]) -> List[Tuple[int, int]]:
        base_offset = 60
        inner_half = 45  # expanded to accommodate six lanes
        outer_half = 105  # wider outer boundary
        length = 270
        perp = (-vector[1], vector[0])
        base_center = (
            self.center[0] + vector[0] * base_offset,
            self.center[1] + vector[1] * base_offset
        )
        far_center = (
            self.center[0] + vector[0] * length,
            self.center[1] + vector[1] * length
        )
        return [
            self._offset_point(base_center, perp, inner_half),
            self._offset_point(far_center, perp, outer_half),
            self._offset_point(far_center, perp, -outer_half),
            self._offset_point(base_center, perp, -inner_half)
        ]

    def _offset_point(self, point: Tuple[float, float], perp: Tuple[float, float], offset: float) -> Tuple[int, int]:
        return (
            int(point[0] + perp[0] * offset),
            int(point[1] + perp[1] * offset)
        )

    def _create_center_diamond(self) -> List[Tuple[int, int]]:
        radius = 90
        cx, cy = self.center
        return [
            (cx, cy - radius),
            (cx + radius, cy),
            (cx, cy + radius),
            (cx - radius, cy)
        ]


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
