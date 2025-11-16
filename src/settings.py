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

# Signal timing constraints (seconds)
BASE_GREEN_TIME = float(os.getenv("BASE_GREEN_TIME", "5.0"))
MIN_GREEN_TIME = float(os.getenv("MIN_GREEN_TIME", "2.0"))
MAX_GREEN_TIME = float(os.getenv("MAX_GREEN_TIME", "10.0"))
ADJUSTMENT_FACTOR = float(os.getenv("ADJUSTMENT_FACTOR", "3.0"))

# Queue simulation parameters
ARRIVAL_RATE = float(os.getenv("ARRIVAL_RATE", "0.3"))  # Probability per second
DEPARTURE_RATE = float(os.getenv("DEPARTURE_RATE", "0.4"))  # Probability per second
MAX_QUEUE = 20  # Maximum queue length for normalization

# Behavior update periods (seconds)
SENSOR_PERIOD = 1.0
CONTROL_PERIOD = 2.0
COORDINATION_PERIOD = 2.0
BROADCAST_PERIOD = 3.0

# Yellow light duration (seconds)
YELLOW_LIGHT_DURATION = 2.0

# ============================================================================
# NETWORK TOPOLOGY
# ============================================================================

# Star topology: Center connected to North, South, East, West
INTERSECTIONS: Dict[str, Dict] = {
    "TL_CENTER": {
        "jid": os.getenv("TL_CENTER_JID", "tl_center@localhost"),
        "password": os.getenv("TL_CENTER_PASSWORD", "center123"),
        "neighbors": ["TL_NORTH", "TL_SOUTH", "TL_EAST", "TL_WEST"],
        "position": (0, 0),
        "display_name": "Center"
    },
    "TL_NORTH": {
        "jid": os.getenv("TL_NORTH_JID", "tl_north@localhost"),
        "password": os.getenv("TL_NORTH_PASSWORD", "north123"),
        "neighbors": ["TL_CENTER"],
        "position": (0, 1),
        "display_name": "North"
    },
    "TL_SOUTH": {
        "jid": os.getenv("TL_SOUTH_JID", "tl_south@localhost"),
        "password": os.getenv("TL_SOUTH_PASSWORD", "south123"),
        "neighbors": ["TL_CENTER"],
        "position": (0, -1),
        "display_name": "South"
    },
    "TL_EAST": {
        "jid": os.getenv("TL_EAST_JID", "tl_east@localhost"),
        "password": os.getenv("TL_EAST_PASSWORD", "east123"),
        "neighbors": ["TL_CENTER"],
        "position": (1, 0),
        "display_name": "East"
    },
    "TL_WEST": {
        "jid": os.getenv("TL_WEST_JID", "tl_west@localhost"),
        "password": os.getenv("TL_WEST_PASSWORD", "west123"),
        "neighbors": ["TL_CENTER"],
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
