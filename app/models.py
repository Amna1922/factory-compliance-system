from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime

class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class BehaviorClass(str, Enum):
    SAFE_WALKWAY_VIOLATION = "Safe Walkway Violation"
    UNAUTHORIZED_INTERVENTION = "Unauthorized Intervention"
    OPENED_PANEL_COVER = "Opened Panel Cover"
    CARRYING_OVERLOAD = "Carrying Overload with Forklift"

class ViolationEvent(BaseModel):
    event_id: str
    timestamp: str
    clip_id: str
    zone: str
    behavior_class: str
    policy_rule_ref: str
    event_description: str
    severity: str
    escalation_action: Optional[str] = ""
    location: Optional[dict] = None  # Bounding box or coordinates
    confidence: Optional[float] = 0.0

class DetectionResult(BaseModel):
    behavior_class: str
    policy_rule_ref: str
    description: str
    zone: str
    confidence: float
    location: dict
    timestamp: float