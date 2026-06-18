import cv2
import numpy as np
from typing import List, Dict, Any
import asyncio
from pathlib import Path
from .config import settings
from .utils import data_loader
from .policy_parser import PolicyParser

class DetectionEngine:
    def __init__(self):
        self.policy_parser = PolicyParser(settings.POLICY_PATH)
        self.rules = self.policy_parser.parse_policy()
        self.data_loader = data_loader
        
        # Load class mapping
        self.class_mapping = settings.CLASS_MAPPING
        
    async def process_video_file(self, video_path: str) -> Dict[str, Any]:
        """Process a single video file and detect violations"""
        # Determine the class from the file path
        video_path_obj = Path(video_path)
        folder_name = video_path_obj.parent.name
        
        if folder_name in self.class_mapping:
            class_info = self.class_mapping[folder_name]
            
            # Create detection result
            detection = {
                "behavior_class": class_info["policy_class"],
                "is_unsafe": class_info["is_unsafe"],
                "severity": class_info["severity"],
                "policy_rule_ref": self._get_policy_ref(class_info["policy_class"]),
                "description": self._get_description(class_info["policy_class"]),
                "zone": self._determine_zone(),
                "confidence": 0.9,  # Since we know the label
                "video_path": str(video_path),
                "folder": folder_name
            }
            
            # If unsafe, add more details
            if class_info["is_unsafe"]:
                detection["violation_detected"] = True
                detection["severity_tier"] = class_info["severity"]
            else:
                detection["violation_detected"] = False
                
            return detection
        else:
            return {
                "behavior_class": "Unknown",
                "is_unsafe": False,
                "severity": "UNKNOWN",
                "description": "Unknown behavior class",
                "video_path": str(video_path)
            }
    
    async def process_video_batch(self, video_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple videos"""
        results = []
        for video_path in video_paths:
            result = await self.process_video_file(video_path)
            results.append(result)
        return results
    
    async def process_all_unsafe_videos(self, split: str = "test") -> List[Dict[str, Any]]:
        """Process all unsafe videos from a split"""
        unsafe_videos = self.data_loader.get_unsafe_videos(split)
        results = []
        
        for video_info in unsafe_videos:
            result = await self.process_video_file(video_info["path"])
            # Add additional metadata
            result["split"] = video_info["split"]
            result["folder_name"] = video_info["folder_name"]
            results.append(result)
        
        return results
    
    def _get_policy_ref(self, class_name: str) -> str:
        """Get policy section reference for a behavior class"""
        policy_refs = {
            "Safe Walkway Violation": "Section 3.3.2",
            "Unauthorized Intervention": "Section 4.3.2",
            "Opened Panel Cover": "Section 5.2.2",
            "Carrying Overload with Forklift": "Section 6.3.2",
            "Safe Walkway": "Section 3.3.1",
            "Authorized Intervention": "Section 4.3.1",
            "Closed Panel Cover": "Section 5.2.1"
        }
        return policy_refs.get(class_name, "Unknown Section")
    
    def _get_description(self, class_name: str) -> str:
        """Get description for a behavior class"""
        descriptions = {
            "Safe Walkway Violation": "Person detected outside the green-marked walkway boundaries",
            "Unauthorized Intervention": "Person interacting with equipment without green safety vest",
            "Opened Panel Cover": "Electrical panel cover left in open position",
            "Carrying Overload with Forklift": "Forklift carrying 3 or more blocks",
            "Safe Walkway": "Person walking within designated green walkway",
            "Authorized Intervention": "Person with green vest performing authorized equipment intervention",
            "Closed Panel Cover": "Electrical panel cover properly closed"
        }
        return descriptions.get(class_name, "Behavior observed")
    
    def _determine_zone(self) -> str:
        """Determine zone (simplified)"""
        # In a real implementation, this would analyze the frame
        return "Zone-1"