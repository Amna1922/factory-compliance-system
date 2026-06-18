"""
Configuration management for the compliance system
"""
import os
from pathlib import Path
from typing import Dict, List

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_DIR = PROJECT_ROOT / "data"

# Database
DATABASE_URL = "sqlite:///./compliance.db"
DB_PATH = PROJECT_ROOT / "compliance.db"

# Video dataset paths
DATASET_BASE = DATA_DIR / "videos" / "Video Dataset for Safe and Unsafe Behaviours" / "Safe and Unsafe Behaviours Dataset"
DATASET_TRAIN = DATASET_BASE / "train"
DATASET_TEST = DATASET_BASE / "test"

# Reports output paths
REPORTS_DIR = PROJECT_ROOT / "reports"
JSON_REPORTS_DIR = REPORTS_DIR / "json"
CSV_AUDIT_LOG = REPORTS_DIR / "audit_log.csv"

# Create directories if they don't exist
for directory in [REPORTS_DIR, JSON_REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Settings
API_HOST = "0.0.0.0"
API_PORT = 8000
BACKEND_URL = "http://localhost:8000"

# Streamlit Settings
STREAMLIT_HOST = "0.0.0.0"
STREAMLIT_PORT = 8501

# WebSocket Settings
WS_URL = "ws://localhost:8000/ws/alerts"

# Behavior class mappings from dataset folder names
BEHAVIOR_CLASS_MAPPING = {
    "0_safe_walkway_violation": {
        "label": "Safe Walkway Violation",
        "is_safe": False,
        "description": "Employee walking outside designated safe walkway",
        "policy_ref": "POL-PED-01"
    },
    "1_unauthorized_intervention": {
        "label": "Unauthorized Intervention",
        "is_safe": False,
        "description": "Unauthorized personnel attempting to intervene with equipment",
        "policy_ref": "POL-EQP-01"
    },
    "2_opened_panel_cover": {
        "label": "Opened Panel Cover",
        "is_safe": False,
        "description": "Electrical panel or equipment cover left opened",
        "policy_ref": "POL-ELE-01"
    },
    "3_carrying_overload_with_forklift": {
        "label": "Carrying Overload with Forklift",
        "is_safe": False,
        "description": "Forklift carrying load exceeding safe capacity",
        "policy_ref": "POL-FOR-01"
    },
    "4_safe_walkway": {
        "label": "Safe Walkway",
        "is_safe": True,
        "description": "Employee safely walking in designated walkway",
        "policy_ref": "POL-PED-02"
    },
    "5_authorized_intervention": {
        "label": "Authorized Intervention",
        "is_safe": True,
        "description": "Authorized personnel performing authorized equipment intervention",
        "policy_ref": "POL-EQP-02"
    },
    "6_closed_panel_cover": {
        "label": "Closed Panel Cover",
        "is_safe": True,
        "description": "Equipment panels and covers properly closed",
        "policy_ref": "POL-ELE-02"
    }
}

# Severity levels
SEVERITY_LEVELS = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

# Severity mapping based on policy - unsafe behaviors only
BEHAVIOR_SEVERITY_MAPPING = {
    "Safe Walkway Violation": "MEDIUM",
    "Unauthorized Intervention": "HIGH",
    "Opened Panel Cover": "LOW",
    "Carrying Overload with Forklift": "CRITICAL"
}

# Default zone assignment (can be updated per video)
DEFAULT_ZONE = "Factory Floor A"

# PDF Parser Settings
PDF_POLICY_PATH = "Compliance_Policy_Manual.pdf"

# Logging
LOG_LEVEL = "INFO"

# Alert thresholds
ALERT_THRESHOLD_SEVERITY = "HIGH"  # Only HIGH and CRITICAL trigger real-time alerts

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100

# Video processing
VIDEO_EXTENSION = ".mp4"
VIDEO_FRAME_SKIP = 5  # Process every 5th frame for performance
MAX_VIDEO_DURATION = 3600  # seconds (1 hour)

# Cache settings
ENABLE_CACHING = True
CACHE_TTL = 3600  # seconds

# API response settings
API_TIMEOUT = 30
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
