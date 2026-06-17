import json
import csv
import os
from datetime import datetime
from typing import Dict, Any
from .models import ViolationEvent
from .config import settings

class ReportGenerator:
    def __init__(self):
        self.reports_dir = settings.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)
        self.report_cache = {}
    
    async def generate_report(self, event: ViolationEvent) -> str:
        """
        Generate and save compliance report
        """
        report = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "clip_id": event.clip_id,
            "zone": event.zone,
            "behavior_class": event.behavior_class,
            "policy_rule_ref": event.policy_rule_ref,
            "event_description": event.event_description,
            "severity": event.severity,
            "escalation_action": event.escalation_action,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Save as JSON
        json_path = os.path.join(self.reports_dir, f"{event.event_id}.json")
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Append to CSV
        csv_path = os.path.join(self.reports_dir, "audit_log.csv")
        file_exists = os.path.isfile(csv_path)
        
        with open(csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=report.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(report)
        
        # Cache report
        self.report_cache[event.event_id] = report
        
        return json_path
    
    async def get_report(self, event_id: str) -> Dict[str, Any]:
        """
        Retrieve report by event ID
        """
        if event_id in self.report_cache:
            return self.report_cache[event_id]
        
        json_path = os.path.join(self.reports_dir, f"{event_id}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                report = json.load(f)
                self.report_cache[event_id] = report
                return report
        
        return None