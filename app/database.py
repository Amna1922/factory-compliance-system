"""
Database operations and session management
"""
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import os

from app.config import DATABASE_URL, DB_PATH
from app.models import Base, ComplianceEventModel, ComplianceReportModel, AlertLog

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/database.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


def save_compliance_event(
    event_id: str,
    timestamp: datetime,
    clip_id: str,
    zone: str,
    behavior_class: str,
    policy_rule_ref: str,
    event_description: str,
    severity: str,
    escalation_action: str,
    confidence: float = 1.0
) -> ComplianceEventModel:
    """Save a compliance event to database"""
    db = get_db()
    try:
        event = ComplianceEventModel(
            event_id=event_id,
            timestamp=timestamp,
            clip_id=clip_id,
            zone=zone,
            behavior_class=behavior_class,
            policy_rule_ref=policy_rule_ref,
            event_description=event_description,
            severity=severity,
            escalation_action=escalation_action,
            confidence=confidence,
            alerted=False
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"Compliance event saved: {event_id}")
        return event
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving compliance event: {str(e)}")
        raise
    finally:
        db.close()


def get_event(event_id: str) -> Optional[ComplianceEventModel]:
    """Get a compliance event by ID"""
    db = get_db()
    try:
        return db.query(ComplianceEventModel).filter(
            ComplianceEventModel.event_id == event_id
        ).first()
    except Exception as e:
        logger.error(f"Error retrieving event: {str(e)}")
        raise
    finally:
        db.close()


def get_all_events(
    severity: Optional[str] = None,
    behavior_class: Optional[str] = None,
    zone: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> List[ComplianceEventModel]:
    """Query events with optional filters"""
    db = get_db()
    try:
        query = db.query(ComplianceEventModel)

        if severity:
            query = query.filter(ComplianceEventModel.severity == severity)

        if behavior_class:
            query = query.filter(ComplianceEventModel.behavior_class == behavior_class)

        if zone:
            query = query.filter(ComplianceEventModel.zone == zone)

        if start_date:
            query = query.filter(ComplianceEventModel.timestamp >= start_date)

        if end_date:
            query = query.filter(ComplianceEventModel.timestamp <= end_date)

        events = query.order_by(
            ComplianceEventModel.timestamp.desc()
        ).limit(limit).offset(offset).all()

        return events
    except Exception as e:
        logger.error(f"Error querying events: {str(e)}")
        raise
    finally:
        db.close()


def get_events_by_severity(severity: str, limit: int = 50) -> List[ComplianceEventModel]:
    """Get events filtered by severity"""
    return get_all_events(severity=severity, limit=limit)


def get_events_by_behavior_class(behavior_class: str, limit: int = 50) -> List[ComplianceEventModel]:
    """Get events filtered by behavior class"""
    return get_all_events(behavior_class=behavior_class, limit=limit)


def save_compliance_report(
    event_id: str,
    timestamp: datetime,
    severity: str,
    report_file_path: Optional[str] = None
) -> ComplianceReportModel:
    """Save a compliance report record"""
    db = get_db()
    try:
        report = ComplianceReportModel(
            event_id=event_id,
            timestamp=timestamp,
            severity=severity,
            report_file_path=report_file_path,
            exported=False
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Compliance report saved: {event_id}")
        return report
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving compliance report: {str(e)}")
        raise
    finally:
        db.close()


def save_alert_log(
    event_id: str,
    alert_type: str,
    delivered: bool = True
) -> AlertLog:
    """Log an alert"""
    db = get_db()
    try:
        alert = AlertLog(
            event_id=event_id,
            alert_type=alert_type,
            delivered=delivered
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        logger.info(f"Alert logged: {event_id} ({alert_type})")
        return alert
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving alert log: {str(e)}")
        raise
    finally:
        db.close()


def get_event_count_by_severity() -> dict:
    """Get count of events grouped by severity"""
    db = get_db()
    try:
        results = db.query(
            ComplianceEventModel.severity,
            func.count(ComplianceEventModel.id).label('count')
        ).group_by(ComplianceEventModel.severity).all()

        return {severity: count for severity, count in results}
    except Exception as e:
        logger.error(f"Error getting event count: {str(e)}")
        raise
    finally:
        db.close()


def get_events_by_date_range(
    start_date: datetime,
    end_date: datetime
) -> List[ComplianceEventModel]:
    """Get events within a date range"""
    return get_all_events(start_date=start_date, end_date=end_date)


def get_recent_events(hours: int = 24, limit: int = 100) -> List[ComplianceEventModel]:
    """Get events from the last N hours"""
    start_date = datetime.utcnow() - timedelta(hours=hours)
    return get_all_events(start_date=start_date, limit=limit)


def mark_event_as_alerted(event_id: str) -> bool:
    """Mark an event as having sent an alert"""
    db = get_db()
    try:
        event = db.query(ComplianceEventModel).filter(
            ComplianceEventModel.event_id == event_id
        ).first()

        if event:
            event.alerted = True
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking event as alerted: {str(e)}")
        raise
    finally:
        db.close()


def delete_old_events(days: int = 90) -> int:
    """Delete events older than N days"""
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = db.query(ComplianceEventModel).filter(
            ComplianceEventModel.timestamp < cutoff_date
        ).delete()
        db.commit()
        logger.info(f"Deleted {deleted_count} events older than {days} days")
        return deleted_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting old events: {str(e)}")
        raise
    finally:
        db.close()


def get_db_connection_string() -> str:
    """Get database connection string"""
    return DATABASE_URL
