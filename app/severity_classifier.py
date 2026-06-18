"""
Severity classifier - Assign severity tiers based on policy
"""
import logging
from typing import Optional

from app.config import BEHAVIOR_SEVERITY_MAPPING, SEVERITY_LEVELS

logger = logging.getLogger(__name__)


class SeverityClassifier:
    """Classify event severity based on policy"""

    def __init__(self):
        self.severity_mappings = BEHAVIOR_SEVERITY_MAPPING
        self.severity_levels = SEVERITY_LEVELS
        self.logger = logger

    def classify_severity(self, behavior_class: str) -> str:
        """Classify severity for a behavior class"""
        if behavior_class in self.severity_mappings:
            return self.severity_mappings[behavior_class]
        return "NONE"  # Default for safe behaviors

    def get_severity_level_value(self, severity: str) -> int:
        """Get numeric value for severity level"""
        return self.severity_levels.get(severity, 0)

    def compare_severity(self, severity1: str, severity2: str) -> int:
        """
        Compare two severity levels
        Returns: 1 if severity1 > severity2, -1 if severity1 < severity2, 0 if equal
        """
        val1 = self.get_severity_level_value(severity1)
        val2 = self.get_severity_level_value(severity2)
        
        if val1 > val2:
            return 1
        elif val1 < val2:
            return -1
        else:
            return 0

    def is_high_severity(self, severity: str) -> bool:
        """Check if severity is HIGH or CRITICAL"""
        return severity in ["HIGH", "CRITICAL"]

    def is_low_severity(self, severity: str) -> bool:
        """Check if severity is LOW or MEDIUM"""
        return severity in ["LOW", "MEDIUM"]

    def should_trigger_real_time_alert(self, severity: str) -> bool:
        """Check if severity should trigger real-time alert"""
        return self.is_high_severity(severity)

    def should_log_to_database(self, severity: str) -> bool:
        """Check if severity should be logged to database"""
        return severity != "NONE"

    def get_escalation_action(self, severity: str) -> str:
        """Get escalation action based on severity"""
        if severity == "CRITICAL":
            return "Immediate alert to supervisor and safety team"
        elif severity == "HIGH":
            return "Real-time alert to monitoring dashboard"
        elif severity == "MEDIUM":
            return "Logged to database for review"
        elif severity == "LOW":
            return "Logged to database for review"
        else:
            return "No action required"

    def get_alert_color(self, severity: str) -> str:
        """Get color code for UI display"""
        color_map = {
            "CRITICAL": "#FF0000",  # Red
            "HIGH": "#FFA500",      # Orange
            "MEDIUM": "#FFFF00",    # Yellow
            "LOW": "#00FF00",       # Green
            "NONE": "#0000FF"       # Blue
        }
        return color_map.get(severity, "#808080")  # Gray default

    def validate_severity(self, severity: str) -> bool:
        """Validate that severity is a known level"""
        return severity in self.severity_levels

    def get_all_severity_levels(self) -> list:
        """Get sorted list of all severity levels"""
        return sorted(self.severity_levels.keys(), 
                     key=lambda x: self.severity_levels[x], 
                     reverse=True)

    def rank_behaviors_by_severity(self, behaviors: list) -> list:
        """Rank behaviors by their severity"""
        behavior_severity = []
        for behavior in behaviors:
            severity = self.classify_severity(behavior)
            level = self.get_severity_level_value(severity)
            behavior_severity.append((behavior, severity, level))
        
        # Sort by severity level (descending)
        return sorted(behavior_severity, key=lambda x: x[2], reverse=True)


# Global severity classifier instance
severity_classifier = SeverityClassifier()


def get_severity_classifier() -> SeverityClassifier:
    """Get severity classifier instance"""
    return severity_classifier


def classify_event_severity(behavior_class: str) -> str:
    """Convenience function to classify event severity"""
    return severity_classifier.classify_severity(behavior_class)
