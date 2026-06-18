"""
Data models for the compliance system
Includes both Pydantic (API) and SQLAlchemy (ORM) models
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


# ==================== Pydantic Models (API Schemas) ====================

class DetectionResult(BaseModel):
    """Result from a single detection"""
    clip_id: str
    timestamp: float
    behavior_class: str
    policy_rule_ref: str
    description: str
    zone: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    class Config:
        schema_extra = {
            "example": {
                "clip_id": "video_001.mp4",
                "timestamp": 12.5,
                "behavior_class": "Safe Walkway Violation",
                "policy_rule_ref": "POL-PED-01",
                "description": "Employee walking outside designated safe walkway",
                "zone": "Factory Floor A",
                "confidence": 0.95
            }
        }


class ComplianceEvent(BaseModel):
    """A compliance event detected in the system"""
    event_id: str
    timestamp: datetime
    clip_id: str
    zone: str
    behavior_class: str
    policy_rule_ref: str
    event_description: str
    severity: str
    escalation_action: str
    confidence: float = 1.0

    class Config:
        schema_extra = {
            "example": {
                "event_id": "EVT-20240115-001",
                "timestamp": "2024-01-15T14:30:00Z",
                "clip_id": "video_001.mp4",
                "zone": "Factory Floor A",
                "behavior_class": "Safe Walkway Violation",
                "policy_rule_ref": "POL-PED-01",
                "event_description": "Employee walking outside designated safe walkway",
                "severity": "MEDIUM",
                "escalation_action": "Logged to database",
                "confidence": 0.95
            }
        }


class ComplianceReport(BaseModel):
    """Report for a compliance violation"""
    event_id: str
    timestamp: datetime
    clip_id: str
    zone: str
    behavior_class: str
    policy_rule_ref: str
    event_description: str
    severity: str
    escalation_action: str
    report_generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "event_id": "EVT-20240115-001",
                "timestamp": "2024-01-15T14:30:00Z",
                "clip_id": "video_001.mp4",
                "zone": "Factory Floor A",
                "behavior_class": "Safe Walkway Violation",
                "policy_rule_ref": "POL-PED-01",
                "event_description": "Employee walking outside designated safe walkway",
                "severity": "MEDIUM",
                "escalation_action": "Logged to database",
                "report_generated_at": "2024-01-15T14:35:00Z"
            }
        }


class AlertNotification(BaseModel):
    """Real-time alert notification"""
    event_id: str
    severity: str
    behavior_class: str
    zone: str
    timestamp: datetime
    description: str

    class Config:
        schema_extra = {
            "example": {
                "event_id": "EVT-20240115-001",
                "severity": "HIGH",
                "behavior_class": "Unauthorized Intervention",
                "zone": "Factory Floor A",
                "timestamp": "2024-01-15T14:30:00Z",
                "description": "Unauthorized personnel attempting to intervene with equipment"
            }
        }


class AnalysisRequest(BaseModel):
    """Request to analyze a video"""
    file_name: str
    zone: Optional[str] = None


class BatchAnalysisRequest(BaseModel):
    """Request to analyze multiple videos from dataset"""
    dataset_type: str = "train"  # train or test
    behavior_classes: Optional[list] = None  # None means all classes


class EventFilter(BaseModel):
    """Filters for querying events"""
    severity: Optional[str] = None
    behavior_class: Optional[str] = None
    zone: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50


class DatasetStats(BaseModel):
    """Statistics about the dataset"""
    total_videos: int
    total_train_videos: int
    total_test_videos: int
    class_distribution: dict
    safe_count: int
    unsafe_count: int


# ==================== SQLAlchemy ORM Models ====================

class ComplianceEventModel(Base):
    """SQLAlchemy model for compliance events"""
    __tablename__ = "compliance_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    clip_id = Column(String(255), nullable=False, index=True)
    zone = Column(String(100), nullable=False, index=True)
    behavior_class = Column(String(100), nullable=False, index=True)
    policy_rule_ref = Column(String(50), nullable=False)
    event_description = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    escalation_action = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    alerted = Column(Boolean, default=False)  # Track if alert was sent

    def __repr__(self):
        return f"<ComplianceEvent {self.event_id}>"

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "clip_id": self.clip_id,
            "zone": self.zone,
            "behavior_class": self.behavior_class,
            "policy_rule_ref": self.policy_rule_ref,
            "event_description": self.event_description,
            "severity": self.severity,
            "escalation_action": self.escalation_action,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


class ComplianceReportModel(Base):
    """SQLAlchemy model for compliance reports"""
    __tablename__ = "compliance_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    report_file_path = Column(String(255), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    exported = Column(Boolean, default=False)

    def __repr__(self):
        return f"<ComplianceReport {self.event_id}>"


class AlertLog(Base):
    """SQLAlchemy model for alert logs"""
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # REAL_TIME or DATABASE_LOG
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered = Column(Boolean, default=False)

    def __repr__(self):
        return f"<AlertLog {self.event_id}>"


def generate_event_id() -> str:
    """Generate a unique event ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_suffix = str(uuid.uuid4())[:8].upper()
    return f"EVT-{timestamp}-{unique_suffix}"
