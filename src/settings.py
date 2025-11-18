"""
Configuration settings for the Intelligent Traffic Light Control Network.
This module defines the network topology, agent parameters, and XMPP configuration.
"""

import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# XMPP SERVER CONFIGURATION (Local Prosody)
# ============================================================================

XMPP_SERVER = os.getenv("XMPP_SERVER", "localhost")
XMPP_PORT = int(os.getenv("XMPP_PORT", "5222"))

# ============================================================================
# TRAFFIC LIGHT PARAMETERS
# ============================================================================

# Industry-standard four-phase timing configuration (seconds)
# P1: N+S straight & right | P2: E+W straight & right | P3: N+S left | P4: E+W left
P1_GREEN_TIME = float(os.getenv("P1_GREEN_TIME", "18.0"))  # N+S through/right
P2_GREEN_TIME = float(os.getenv("P2_GREEN_TIME", "18.0"))  # E+W through/right
P3_GREEN_TIME = float(os.getenv("P3_GREEN_TIME", "7.0"))   # N+S protected left
P4_GREEN_TIME = float(os.getenv("P4_GREEN_TIME", "7.0"))   # E+W protected left

# Safety interval configuration
YELLOW_LIGHT_DURATION = float(os.getenv("YELLOW_LIGHT_DURATION", "3.0"))  # yellow (amber) time
ALL_RED_CLEARANCE = float(os.getenv("ALL_RED_CLEARANCE", "2.0"))  # all-red clearance between phases

# Minimum timing constraints (safety)
MIN_GREEN_STRAIGHT = float(os.getenv("MIN_GREEN_STRAIGHT", "8.0"))  # min green for through movements
MIN_GREEN_LEFT = float(os.getenv("MIN_GREEN_LEFT", "5.0"))  # min green for protected left
MIN_YELLOW_TIME = 3.0  # minimum yellow duration (urban speed)
MIN_ALL_RED_TIME = 1.0  # minimum all-red clearance

# Adaptive control bounds (legacy compatibility)
BASE_GREEN_TIME = float(os.getenv("BASE_GREEN_TIME", "12.0"))  # adaptive baseline
MIN_GREEN_TIME = float(os.getenv("MIN_GREEN_TIME", "5.0"))  # adaptive minimum
MAX_GREEN_TIME = float(os.getenv("MAX_GREEN_TIME", "24.0"))  # adaptive maximum
ADJUSTMENT_FACTOR = float(os.getenv("ADJUSTMENT_FACTOR", "3.5"))  # pressure-based scaling
PHASE_SPEEDUP_FACTOR = float(os.getenv("PHASE_SPEEDUP_FACTOR", "0.88"))  # global speed multiplier for non-critical greens
QUEUE_RELIEF_TARGET = float(os.getenv("QUEUE_RELIEF_TARGET", "0.30"))  # desired pressure gap relief

# Computed cycle metrics
CYCLE_LENGTH = (P1_GREEN_TIME + P2_GREEN_TIME + P3_GREEN_TIME + P4_GREEN_TIME +
                4 * YELLOW_LIGHT_DURATION + 4 * ALL_RED_CLEARANCE)  # ~90s default

# Queue simulation parameters
ARRIVAL_RATE = float(os.getenv("ARRIVAL_RATE", "0.3"))  # Probability per second
DEPARTURE_RATE = float(os.getenv("DEPARTURE_RATE", "0.4"))  # Probability per second
MAX_QUEUE = 20  # Maximum queue length for normalization

# Behavior update periods (seconds)
SENSOR_PERIOD = 1.0
CONTROL_PERIOD = 2.0
COORDINATION_PERIOD = 2.0
BROADCAST_PERIOD = 3.0

# ============================================================================
# NETWORK TOPOLOGY
# ============================================================================

# Single four-way junction: four autonomous approach agents
INTERSECTIONS: Dict[str, Dict] = {
    "TL_NORTH": {
        "jid": os.getenv("TL_NORTH_JID", "tl_north@localhost"),
        "password": os.getenv("TL_NORTH_PASSWORD", "north123"),
        "neighbors": ["TL_SOUTH", "TL_EAST", "TL_WEST"],
        "position": (0, 1),
        "display_name": "North"
    },
    "TL_SOUTH": {
        "jid": os.getenv("TL_SOUTH_JID", "tl_south@localhost"),
        "password": os.getenv("TL_SOUTH_PASSWORD", "south123"),
        "neighbors": ["TL_NORTH", "TL_EAST", "TL_WEST"],
        "position": (0, -1),
        "display_name": "South"
    },
    "TL_EAST": {
        "jid": os.getenv("TL_EAST_JID", "tl_east@localhost"),
        "password": os.getenv("TL_EAST_PASSWORD", "east123"),
        "neighbors": ["TL_WEST", "TL_NORTH", "TL_SOUTH"],
        "position": (1, 0),
        "display_name": "East"
    },
    "TL_WEST": {
        "jid": os.getenv("TL_WEST_JID", "tl_west@localhost"),
        "password": os.getenv("TL_WEST_PASSWORD", "west123"),
        "neighbors": ["TL_EAST", "TL_NORTH", "TL_SOUTH"],
        "position": (-1, 0),
        "display_name": "West"
    }
}

# Coordinator agent configuration
COORDINATOR_CONFIG = {
    "jid": os.getenv("COORDINATOR_JID", "coordinator@localhost"),
    "password": os.getenv("COORDINATOR_PASSWORD", "coordinator123")
}

# ============================================================================
# FIPA ACL MESSAGE ONTOLOGIES
# ============================================================================

ONTOLOGY_COORDINATION = "traffic-coordination"
ONTOLOGY_STATUS = "traffic-status"
ONTOLOGY_CONTROL = "traffic-control"

LANGUAGE_JSON = "json"

# ============================================================================
# TRAFFIC SCENARIOS
# ============================================================================

SCENARIOS = {
    "normal": {
        "arrival_rate": 0.3,
        "departure_rate": 0.4,
        "description": "Normal traffic conditions"
    },
    "rush_hour": {
        "arrival_rate": 0.6,
        "departure_rate": 0.4,
        "description": "Heavy traffic in all directions"
    },
    "light": {
        "arrival_rate": 0.1,
        "departure_rate": 0.5,
        "description": "Light traffic conditions"
    },
    "directional": {
        "arrival_rate": 0.8,
        "departure_rate": 0.4,
        "description": "Heavy traffic in specific direction (NS)"
    }
}

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

# Colors for traffic phases
COLOR_NS_GREEN = "#00FF00"
COLOR_EW_GREEN = "#00FF00"
COLOR_YELLOW = "#FFFF00"
COLOR_RED = "#FF0000"

# Dashboard update interval (seconds)
DASHBOARD_UPDATE_INTERVAL = 1.0

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(name)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_neighbor_jids(intersection_name: str) -> List[str]:
    """
    Get list of neighbor JIDs for a given intersection.
    
    Args:
        intersection_name: Name of the intersection (e.g., "TL_CENTER")
    
    Returns:
        List of neighbor JIDs
    """
    if intersection_name not in INTERSECTIONS:
        return []
    
    neighbor_names = INTERSECTIONS[intersection_name]["neighbors"]
    return [INTERSECTIONS[name]["jid"] for name in neighbor_names if name in INTERSECTIONS]


def get_all_traffic_light_jids() -> List[str]:
    """
    Get list of all traffic light agent JIDs.
    
    Returns:
        List of all traffic light JIDs
    """
    return [config["jid"] for config in INTERSECTIONS.values()]


def get_intersection_by_jid(jid: str) -> str:
    """
    Get intersection name from JID.
    
    Args:
        jid: Agent JID
    
    Returns:
        Intersection name or empty string if not found
    """
    for name, config in INTERSECTIONS.items():
        if config["jid"] == jid:
            return name
    return ""
