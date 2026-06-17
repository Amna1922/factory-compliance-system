from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Dict, Any
from .config import settings

Base = declarative_base()

class EventDB(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, unique=True)
    timestamp = Column(DateTime)
    clip_id = Column(String)
    zone = Column(String)
    behavior_class = Column(String)
    policy_rule_ref = Column(String)
    event_description = Column(String)
    severity = Column(String)
    escalation_action = Column(String)

class Database:
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    async def initialize(self):
        """Initialize database"""
        pass
    
    async def save_event(self, event):
        """Save event to database"""
        session = self.Session()
        try:
            event_db = EventDB(
                event_id=event.event_id,
                timestamp=datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')),
                clip_id=event.clip_id,
                zone=event.zone,
                behavior_class=event.behavior_class,
                policy_rule_ref=event.policy_rule_ref,
                event_description=event.event_description,
                severity=event.severity,
                escalation_action=event.escalation_action
            )
            session.add(event_db)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    async def get_events(self, **filters):
        """Get events with filters"""
        session = self.Session()
        try:
            query = session.query(EventDB)
            
            if filters.get('severity'):
                query = query.filter(EventDB.severity == filters['severity'])
            if filters.get('behavior_class'):
                query = query.filter(EventDB.behavior_class == filters['behavior_class'])
            if filters.get('start_date'):
                start = datetime.fromisoformat(filters['start_date'].replace('Z', '+00:00'))
                query = query.filter(EventDB.timestamp >= start)
            if filters.get('end_date'):
                end = datetime.fromisoformat(filters['end_date'].replace('Z', '+00:00'))
                query = query.filter(EventDB.timestamp <= end)
            
            results = query.all()
            
            return [{
                "event_id": r.event_id,
                "timestamp": r.timestamp.isoformat() + "Z",
                "clip_id": r.clip_id,
                "zone": r.zone,
                "behavior_class": r.behavior_class,
                "policy_rule_ref": r.policy_rule_ref,
                "event_description": r.event_description,
                "severity": r.severity,
                "escalation_action": r.escalation_action
            } for r in results]
        finally:
            session.close()