"""
Escalation pipeline - Route events and trigger alerts based on severity
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Callable, Set
from app.database import save_compliance_event, save_alert_log, mark_event_as_alerted
from app.severity_classifier import get_severity_classifier

logger = logging.getLogger(__name__)

# Store for WebSocket connections
active_connections: Set = set()
alert_callbacks: List[Callable] = []


class EscalationPipeline:
    """Route and escalate compliance events"""

    def __init__(self):
        self.severity_classifier = get_severity_classifier()
        self.logger = logger
        self.alert_listeners: List[Callable] = []

    def register_alert_listener(self, callback: Callable):
        """Register a callback to be called when alerts occur"""
        self.alert_listeners.append(callback)
        self.logger.info(f"Alert listener registered: {callback.__name__}")

    def unregister_alert_listener(self, callback: Callable):
        """Unregister an alert callback"""
        if callback in self.alert_listeners:
            self.alert_listeners.remove(callback)
            self.logger.info(f"Alert listener unregistered: {callback.__name__}")

    async def notify_alert_listeners(self, event_data: dict):
        """Notify all registered alert listeners"""
        for callback in self.alert_listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_data)
                else:
                    callback(event_data)
            except Exception as e:
                self.logger.error(f"Error notifying alert listener: {str(e)}")

    def process_event(
        self,
        event_id: str,
        timestamp: datetime,
        clip_id: str,
        zone: str,
        behavior_class: str,
        policy_rule_ref: str,
        event_description: str,
        confidence: float = 1.0
    ) -> dict:
        """Process a compliance event through escalation pipeline"""
        
        try:
            # Classify severity
            severity = self.severity_classifier.classify_severity(behavior_class)
            
            # Skip safe behaviors (severity NONE)
            if severity == "NONE":
                self.logger.info(f"Skipping safe behavior: {behavior_class}")
                return {
                    "processed": False,
                    "reason": "Safe behavior - no escalation needed"
                }

            # Determine escalation action
            escalation_action = self.severity_classifier.get_escalation_action(severity)
            
            # Save to database
            event = save_compliance_event(
                event_id=event_id,
                timestamp=timestamp,
                clip_id=clip_id,
                zone=zone,
                behavior_class=behavior_class,
                policy_rule_ref=policy_rule_ref,
                event_description=event_description,
                severity=severity,
                escalation_action=escalation_action,
                confidence=confidence
            )
            
            # Log to database always (for unsafe behaviors)
            save_alert_log(event_id, "DATABASE_LOG", delivered=True)
            self.logger.info(f"Event logged to database: {event_id} ({severity})")
            
            # Trigger real-time alert if HIGH or CRITICAL
            result = {
                "processed": True,
                "event_id": event_id,
                "severity": severity,
                "escalation_action": escalation_action,
                "alert_triggered": False
            }
            
            if self.severity_classifier.should_trigger_real_time_alert(severity):
                result["alert_triggered"] = True
                
                # Log real-time alert
                save_alert_log(event_id, "REAL_TIME", delivered=True)
                mark_event_as_alerted(event_id)
                
                self.logger.warning(
                    f"Real-time alert triggered: {event_id} - "
                    f"{behavior_class} ({severity}) in {zone}"
                )
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}")
            raise

    async def broadcast_alert(self, event_id: str, alert_data: dict):
        """Broadcast alert to all connected clients (WebSocket)"""
        try:
            # Notify alert listeners
            await self.notify_alert_listeners(alert_data)
            
            # Send to all active WebSocket connections
            if active_connections:
                for connection in list(active_connections):
                    try:
                        await connection.send_json(alert_data)
                    except Exception as e:
                        self.logger.error(f"Error sending alert: {str(e)}")
                        active_connections.discard(connection)
                        
        except Exception as e:
            self.logger.error(f"Error broadcasting alert: {str(e)}")

    def get_escalation_routing(self, severity: str) -> dict:
        """Get routing information for event based on severity"""
        return {
            "severity": severity,
            "database_log": True,  # All unsafe events logged
            "real_time_alert": self.severity_classifier.should_trigger_real_time_alert(severity),
            "alert_color": self.severity_classifier.get_alert_color(severity),
            "escalation_action": self.severity_classifier.get_escalation_action(severity)
        }


# Global escalation pipeline instance
escalation_pipeline = EscalationPipeline()


def get_escalation_pipeline() -> EscalationPipeline:
    """Get escalation pipeline instance"""
    return escalation_pipeline


def add_websocket_connection(connection):
    """Add a WebSocket connection for alert broadcasting"""
    active_connections.add(connection)
    logger.info(f"WebSocket connection added. Total connections: {len(active_connections)}")


def remove_websocket_connection(connection):
    """Remove a WebSocket connection"""
    active_connections.discard(connection)
    logger.info(f"WebSocket connection removed. Total connections: {len(active_connections)}")


def get_active_connections_count() -> int:
    """Get number of active WebSocket connections"""
    return len(active_connections)
