"""
Report generator - Generate JSON and CSV compliance reports
"""
import json
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.config import JSON_REPORTS_DIR, CSV_AUDIT_LOG
from app.database import save_compliance_report, get_all_events

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate compliance violation reports"""

    def __init__(self):
        self.json_reports_dir = JSON_REPORTS_DIR
        self.csv_audit_log = CSV_AUDIT_LOG
        self.logger = logger
        
        # Ensure directories exist
        self.json_reports_dir.mkdir(parents=True, exist_ok=True)
        self.csv_audit_log.parent.mkdir(parents=True, exist_ok=True)

    def generate_json_report(
        self,
        event_id: str,
        timestamp: datetime,
        clip_id: str,
        zone: str,
        behavior_class: str,
        policy_rule_ref: str,
        event_description: str,
        severity: str,
        escalation_action: str
    ) -> Optional[str]:
        """Generate JSON report for a single violation"""
        try:
            report_data = {
                "event_id": event_id,
                "timestamp": timestamp.isoformat(),
                "clip_id": clip_id,
                "zone": zone,
                "behavior_class": behavior_class,
                "policy_rule_ref": policy_rule_ref,
                "event_description": event_description,
                "severity": severity,
                "escalation_action": escalation_action,
                "report_generated_at": datetime.utcnow().isoformat()
            }
            
            # Create filename based on event_id
            filename = f"{event_id}.json"
            filepath = self.json_reports_dir / filename
            
            # Write JSON file
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.info(f"JSON report generated: {filepath}")
            
            # Save report record to database
            save_compliance_report(
                event_id=event_id,
                timestamp=timestamp,
                severity=severity,
                report_file_path=str(filepath)
            )
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error generating JSON report: {str(e)}")
            return None

    def append_csv_audit_log(
        self,
        event_id: str,
        timestamp: datetime,
        clip_id: str,
        zone: str,
        behavior_class: str,
        policy_rule_ref: str,
        event_description: str,
        severity: str,
        escalation_action: str
    ) -> bool:
        """Append event to CSV audit log"""
        try:
            csv_data = {
                "event_id": event_id,
                "timestamp": timestamp.isoformat(),
                "clip_id": clip_id,
                "zone": zone,
                "behavior_class": behavior_class,
                "policy_rule_ref": policy_rule_ref,
                "event_description": event_description,
                "severity": severity,
                "escalation_action": escalation_action,
                "report_generated_at": datetime.utcnow().isoformat()
            }
            
            fieldnames = [
                "event_id", "timestamp", "clip_id", "zone",
                "behavior_class", "policy_rule_ref", "event_description",
                "severity", "escalation_action", "report_generated_at"
            ]
            
            # Check if file exists to determine if we write header
            file_exists = self.csv_audit_log.exists() and self.csv_audit_log.stat().st_size > 0
            
            # Append to CSV
            with open(self.csv_audit_log, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(csv_data)
            
            self.logger.info(f"CSV audit log updated: {self.csv_audit_log}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error appending to CSV audit log: {str(e)}")
            return False

    def generate_both_reports(
        self,
        event_id: str,
        timestamp: datetime,
        clip_id: str,
        zone: str,
        behavior_class: str,
        policy_rule_ref: str,
        event_description: str,
        severity: str,
        escalation_action: str
    ) -> Dict[str, bool]:
        """Generate both JSON and CSV reports"""
        results = {
            "json_generated": False,
            "csv_appended": False
        }
        
        try:
            # Generate JSON report
            json_path = self.generate_json_report(
                event_id, timestamp, clip_id, zone,
                behavior_class, policy_rule_ref, event_description,
                severity, escalation_action
            )
            results["json_generated"] = json_path is not None
            
            # Append to CSV audit log
            results["csv_appended"] = self.append_csv_audit_log(
                event_id, timestamp, clip_id, zone,
                behavior_class, policy_rule_ref, event_description,
                severity, escalation_action
            )
            
            self.logger.info(f"Reports generated for {event_id}: {results}")
            
        except Exception as e:
            self.logger.error(f"Error generating reports: {str(e)}")
        
        return results

    def export_events_to_csv(
        self,
        filename: str,
        severity: Optional[str] = None,
        behavior_class: Optional[str] = None,
        zone: Optional[str] = None
    ) -> Optional[str]:
        """Export events to CSV file with filters"""
        try:
            events = get_all_events(
                severity=severity,
                behavior_class=behavior_class,
                zone=zone,
                limit=10000
            )
            
            if not events:
                self.logger.info("No events to export")
                return None
            
            # Determine export path
            export_path = self.json_reports_dir.parent / filename
            
            fieldnames = [
                "event_id", "timestamp", "clip_id", "zone",
                "behavior_class", "policy_rule_ref", "event_description",
                "severity", "escalation_action", "created_at"
            ]
            
            # Write CSV
            with open(export_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for event in events:
                    writer.writerow({
                        "event_id": event.event_id,
                        "timestamp": event.timestamp.isoformat(),
                        "clip_id": event.clip_id,
                        "zone": event.zone,
                        "behavior_class": event.behavior_class,
                        "policy_rule_ref": event.policy_rule_ref,
                        "event_description": event.event_description,
                        "severity": event.severity,
                        "escalation_action": event.escalation_action,
                        "created_at": event.created_at.isoformat()
                    })
            
            self.logger.info(f"Events exported to: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting events to CSV: {str(e)}")
            return None

    def get_audit_log_path(self) -> str:
        """Get path to audit log file"""
        return str(self.csv_audit_log)

    def get_json_reports_count(self) -> int:
        """Get count of JSON reports generated"""
        try:
            return len(list(self.json_reports_dir.glob("*.json")))
        except Exception:
            return 0


# Global report generator instance
report_generator = ReportGenerator()


def get_report_generator() -> ReportGenerator:
    """Get report generator instance"""
    return report_generator
