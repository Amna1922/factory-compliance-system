"""
Policy parser - Extracts rules and severity mappings from policy document
"""
import logging
from typing import Dict, List, Optional
from app.config import BEHAVIOR_CLASS_MAPPING, BEHAVIOR_SEVERITY_MAPPING

logger = logging.getLogger(__name__)


class PolicyParser:
    """Parse compliance policy document"""

    def __init__(self):
        self.behavior_mappings = BEHAVIOR_CLASS_MAPPING
        self.severity_mappings = BEHAVIOR_SEVERITY_MAPPING
        self.logger = logger

    def get_behavior_class_info(self, folder_name: str) -> Optional[Dict]:
        """Get behavior class information from folder name"""
        if folder_name in self.behavior_mappings:
            return self.behavior_mappings[folder_name]
        return None

    def get_severity_for_behavior(self, behavior_class: str) -> str:
        """Get severity level for a behavior class"""
        if behavior_class in self.severity_mappings:
            return self.severity_mappings[behavior_class]
        return "NONE"  # Default for safe behaviors

    def get_policy_rule_ref(self, folder_name: str) -> Optional[str]:
        """Get policy rule reference from folder name"""
        info = self.get_behavior_class_info(folder_name)
        if info:
            return info.get("policy_ref", "POL-UNKNOWN")
        return None

    def get_all_behavior_classes(self) -> Dict[str, Dict]:
        """Get all behavior class mappings"""
        return self.behavior_mappings.copy()

    def get_unsafe_behaviors(self) -> List[str]:
        """Get list of unsafe behavior labels"""
        return [
            info["label"] for info in self.behavior_mappings.values()
            if not info["is_safe"]
        ]

    def get_safe_behaviors(self) -> List[str]:
        """Get list of safe behavior labels"""
        return [
            info["label"] for info in self.behavior_mappings.values()
            if info["is_safe"]
        ]

    def is_unsafe_behavior(self, behavior_class: str) -> bool:
        """Check if behavior class is unsafe"""
        for info in self.behavior_mappings.values():
            if info["label"] == behavior_class:
                return not info["is_safe"]
        return False

    def validate_policy_rules(self) -> bool:
        """Validate that all policy rules are correctly defined"""
        try:
            # Check that all unsafe behaviors have severity mappings
            unsafe = self.get_unsafe_behaviors()
            for behavior in unsafe:
                if behavior not in self.severity_mappings:
                    self.logger.warning(f"No severity mapping for: {behavior}")

            self.logger.info("Policy validation completed")
            return True
        except Exception as e:
            self.logger.error(f"Policy validation failed: {str(e)}")
            return False

    def extract_policy_summary(self) -> Dict:
        """Extract summary of policy rules"""
        return {
            "total_behaviors": len(self.behavior_mappings),
            "unsafe_behaviors": self.get_unsafe_behaviors(),
            "safe_behaviors": self.get_safe_behaviors(),
            "severity_rules": self.severity_mappings.copy()
        }


# Global policy parser instance
policy_parser = PolicyParser()


def get_policy_parser() -> PolicyParser:
    """Get or create policy parser instance"""
    return policy_parser


def initialize_policy_parser() -> PolicyParser:
    """Initialize policy parser with PDF parsing (for future enhancement)"""
    parser = PolicyParser()
    if not parser.validate_policy_rules():
        logger.warning("Policy validation encountered issues")
    return parser
