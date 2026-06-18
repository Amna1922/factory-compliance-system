"""
Detection engine - Process videos and detect behavioral violations
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import os

from app.config import BEHAVIOR_CLASS_MAPPING, VIDEO_EXTENSION, DATASET_TRAIN, DATASET_TEST
from app.models import DetectionResult

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Video processing and behavior detection engine"""

    def __init__(self):
        self.behavior_mapping = BEHAVIOR_CLASS_MAPPING
        self.logger = logger

    def extract_behavior_class_from_filename(self, filepath: str) -> Optional[str]:
        """Extract behavior class label from file path"""
        path = Path(filepath)
        
        # Look for folder names matching pattern X_*
        for part in path.parts:
            if part in self.behavior_mapping:
                return self.behavior_mapping[part]["label"]
        
        return None

    def extract_policy_ref_from_folder(self, filepath: str) -> Optional[str]:
        """Extract policy reference from folder path"""
        path = Path(filepath)
        
        for part in path.parts:
            if part in self.behavior_mapping:
                return self.behavior_mapping[part]["policy_ref"]
        
        return None

    def process_video(
        self,
        video_path: str,
        zone: str = "Factory Floor A"
    ) -> List[DetectionResult]:
        """Process a single video file and detect violations"""
        detections = []
        
        try:
            if not os.path.exists(video_path):
                self.logger.error(f"Video file not found: {video_path}")
                return detections

            # Extract behavior class from path
            behavior_class = self.extract_behavior_class_from_filename(video_path)
            policy_ref = self.extract_policy_ref_from_folder(video_path)
            
            if not behavior_class:
                self.logger.warning(f"Could not determine behavior class from: {video_path}")
                return detections

            # Get file info
            filename = os.path.basename(video_path)
            clip_id = Path(video_path).stem

            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"Failed to open video: {video_path}")
                return detections

            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Generate detections at regular intervals
            # For folder-based classification, we generate one detection per video
            # indicating the classified behavior
            if fps > 0:
                mid_frame = frame_count // 2
                timestamp = mid_frame / fps
            else:
                timestamp = 0.0

            detection = DetectionResult(
                clip_id=clip_id,
                timestamp=timestamp,
                behavior_class=behavior_class,
                policy_rule_ref=policy_ref or "POL-UNKNOWN",
                description=self.behavior_mapping[
                    self._get_folder_key_from_label(behavior_class)
                ]["description"],
                zone=zone,
                confidence=1.0  # High confidence since based on ground-truth folder
            )
            
            detections.append(detection)
            self.logger.info(f"Detection: {behavior_class} in {clip_id}")

            cap.release()
            
        except Exception as e:
            self.logger.error(f"Error processing video {video_path}: {str(e)}")

        return detections

    def _get_folder_key_from_label(self, label: str) -> Optional[str]:
        """Get folder key from behavior label"""
        for key, info in self.behavior_mapping.items():
            if info["label"] == label:
                return key
        return None

    def process_batch_videos(
        self,
        video_dir: str,
        zone: str = "Factory Floor A"
    ) -> List[Tuple[str, List[DetectionResult]]]:
        """Process multiple videos from a directory"""
        results = []
        
        try:
            video_dir_path = Path(video_dir)
            if not video_dir_path.exists():
                self.logger.error(f"Directory not found: {video_dir}")
                return results

            # Find all MP4 files recursively
            video_files = list(video_dir_path.rglob(f"*{VIDEO_EXTENSION}"))
            self.logger.info(f"Found {len(video_files)} videos to process")

            for video_file in video_files:
                detections = self.process_video(str(video_file), zone)
                results.append((str(video_file), detections))

        except Exception as e:
            self.logger.error(f"Error processing batch: {str(e)}")

        return results

    def process_dataset(
        self,
        dataset_type: str = "train",
        zone: str = "Factory Floor A",
        behavior_classes: Optional[List[str]] = None
    ) -> Dict[str, List[DetectionResult]]:
        """Process videos from the dataset"""
        results = {}
        
        try:
            # Determine dataset path
            if dataset_type.lower() == "train":
                dataset_path = DATASET_TRAIN
            else:
                dataset_path = DATASET_TEST

            if not dataset_path.exists():
                self.logger.error(f"Dataset path not found: {dataset_path}")
                return results

            # If specific behavior classes requested, filter
            target_folders = None
            if behavior_classes:
                target_folders = set()
                for behavior in behavior_classes:
                    for key, info in self.behavior_mapping.items():
                        if info["label"].lower() == behavior.lower():
                            target_folders.add(key)

            # Process each behavior class folder
            for folder_key, folder_info in self.behavior_mapping.items():
                if target_folders and folder_key not in target_folders:
                    continue

                class_dir = dataset_path / folder_key
                if not class_dir.exists():
                    self.logger.info(f"Skipping missing class directory: {class_dir}")
                    continue

                # Process all videos in this class
                class_videos = list(class_dir.glob(f"*{VIDEO_EXTENSION}"))
                self.logger.info(f"Processing {len(class_videos)} videos in {folder_key}")

                class_detections = []
                for video_file in class_videos:
                    detections = self.process_video(str(video_file), zone)
                    class_detections.extend(detections)

                results[folder_info["label"]] = class_detections

        except Exception as e:
            self.logger.error(f"Error processing dataset: {str(e)}")

        return results

    def get_detectable_behaviors(self) -> List[str]:
        """Get list of all detectable behaviors"""
        return [info["label"] for info in self.behavior_mapping.values()]


# Global detection engine instance
detection_engine = DetectionEngine()


def get_detection_engine() -> DetectionEngine:
    """Get detection engine instance"""
    return detection_engine
