import os
from pathlib import Path

class Settings:
    # Project root
    BASE_DIR = Path(__file__).parent.parent
    
    # Data paths - Updated to match your exact structure
    DATA_DIR = BASE_DIR / "data"
    VIDEOS_DIR = DATA_DIR / "videos"
    DATASET_DIR = VIDEOS_DIR / "Video Dataset for Safe and Unsafe Behaviours" / "Safe and Unsafe Behaviours Dataset"
    
    # Train/Test splits
    TRAIN_DIR = DATASET_DIR / "train"
    TEST_DIR = DATASET_DIR / "test"
    
    # Behavior class folders (with numbers as in your dataset)
    BEHAVIOR_CLASSES = {
        "safe_walkway_violation": "0_safe_walkway_violation",
        "unauthorized_intervention": "1_unauthorized_intervention",
        "opened_panel_cover": "2_opened_panel_cover",
        "carrying_overload_with_forklift": "3_carrying_overload_with_forklift",
        "safe_walkway": "4_safe_walkway",
        "authorized_intervention": "5_authorized_intervention",
        "closed_panel_cover": "6_closed_panel_cover"
    }
    
    # Map folder names to policy behavior classes
    CLASS_MAPPING = {
        "0_safe_walkway_violation": {
            "policy_class": "Safe Walkway Violation",
            "is_unsafe": True,
            "severity": "MEDIUM"
        },
        "1_unauthorized_intervention": {
            "policy_class": "Unauthorized Intervention",
            "is_unsafe": True,
            "severity": "HIGH"
        },
        "2_opened_panel_cover": {
            "policy_class": "Opened Panel Cover",
            "is_unsafe": True,
            "severity": "LOW"
        },
        "3_carrying_overload_with_forklift": {
            "policy_class": "Carrying Overload with Forklift",
            "is_unsafe": True,
            "severity": "CRITICAL"
        },
        "4_safe_walkway": {
            "policy_class": "Safe Walkway",
            "is_unsafe": False,
            "severity": "NONE"
        },
        "5_authorized_intervention": {
            "policy_class": "Authorized Intervention",
            "is_unsafe": False,
            "severity": "NONE"
        },
        "6_closed_panel_cover": {
            "policy_class": "Closed Panel Cover",
            "is_unsafe": False,
            "severity": "NONE"
        }
    }
    
    # Policy document
    POLICY_PATH = BASE_DIR / "Compliance_Policy_Manual.pdf"
    
    # Report storage
    REPORTS_DIR = DATA_DIR / "reports"
    
    # Database
    DATABASE_URL = f"sqlite:///{DATA_DIR}/database.db"
    
    # Video processing
    VIDEO_FPS = 30
    DETECTION_THRESHOLD = 0.5
    
    # Alert settings
    ALERT_TIMEOUT = 60  # seconds

settings = Settings()