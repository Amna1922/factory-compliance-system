import asyncio
from typing import Dict, Any
from .models import ViolationEvent, SeverityLevel
from .database import Database

class EscalationPipeline:
    def __init__(self):
        self.db = Database()
        self.alert_queue = asyncio.Queue()
    
    async def process_event(self, event: ViolationEvent) -> str:
        """
        Process event based on severity level
        """
        severity = event.severity
        
        if severity in [SeverityLevel.LOW.value, SeverityLevel.MEDIUM.value]:
            # Log only
            await self.db.save_event(event)
            return "Logged to DB"
        
        elif severity in [SeverityLevel.HIGH.value, SeverityLevel.CRITICAL.value]:
            # Log and trigger alert
            await self.db.save_event(event)
            await self.trigger_alert(event)
            return "Real-time alert triggered + DB log"
        
        return "No action taken"
    
    async def trigger_alert(self, event: ViolationEvent):
        """
        Trigger real-time alert
        """
        # Push to queue for broadcasting
        await self.alert_queue.put(event)
        
        # Log alert
        print(f"🚨 ALERT: {event.severity} violation detected in {event.zone}")
        print(f"   Behavior: {event.behavior_class}")
        print(f"   Description: {event.event_description}")