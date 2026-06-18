"""
Utility functions and dataset operations
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Tuple
from app.config import DATASET_TRAIN, DATASET_TEST, BEHAVIOR_CLASS_MAPPING, VIDEO_EXTENSION

logger = logging.getLogger(__name__)


class DatasetLoader:
    """Load and inspect the video dataset"""

    def __init__(self):
        self.behavior_mapping = BEHAVIOR_CLASS_MAPPING
        self.logger = logger

    def get_dataset_statistics(self) -> Dict:
        """Get statistics about the dataset"""
        stats = {
            "total_videos": 0,
            "train_videos": 0,
            "test_videos": 0,
            "class_distribution": {},
            "safe_count": 0,
            "unsafe_count": 0
        }

        try:
            # Train dataset
            train_count = self._count_videos_in_dataset(DATASET_TRAIN)
            stats["train_videos"] = train_count
            stats["total_videos"] += train_count

            # Test dataset
            test_count = self._count_videos_in_dataset(DATASET_TEST)
            stats["test_videos"] = test_count
            stats["total_videos"] += test_count

            # Class distribution
            class_dist = self._get_class_distribution()
            stats["class_distribution"] = class_dist

            # Safe/Unsafe count
            for class_name, count in class_dist.items():
                is_safe = self._is_class_safe(class_name)
                if is_safe:
                    stats["safe_count"] += count
                else:
                    stats["unsafe_count"] += count

        except Exception as e:
            self.logger.error(f"Error getting dataset statistics: {str(e)}")

        return stats

    def _count_videos_in_dataset(self, dataset_path: Path) -> int:
        """Count total videos in a dataset"""
        try:
            if not dataset_path.exists():
                return 0

            videos = list(dataset_path.rglob(f"*{VIDEO_EXTENSION}"))
            return len(videos)

        except Exception as e:
            self.logger.error(f"Error counting videos: {str(e)}")
            return 0

    def _get_class_distribution(self) -> Dict[str, int]:
        """Get video count per class"""
        distribution = {}

        try:
            for folder_key, folder_info in self.behavior_mapping.items():
                train_path = DATASET_TRAIN / folder_key
                test_path = DATASET_TEST / folder_key

                train_count = len(list(train_path.glob(f"*{VIDEO_EXTENSION}"))) if train_path.exists() else 0
                test_count = len(list(test_path.glob(f"*{VIDEO_EXTENSION}"))) if test_path.exists() else 0

                total = train_count + test_count
                distribution[folder_info["label"]] = total

        except Exception as e:
            self.logger.error(f"Error calculating class distribution: {str(e)}")

        return distribution

    def _is_class_safe(self, class_name: str) -> bool:
        """Check if a class is safe"""
        for info in self.behavior_mapping.values():
            if info["label"] == class_name:
                return info["is_safe"]
        return False

    def list_videos_in_class(self, class_name: str, dataset_type: str = "train") -> List[str]:
        """List all videos in a specific class"""
        videos = []

        try:
            # Find matching folder
            folder_key = None
            for key, info in self.behavior_mapping.items():
                if info["label"] == class_name:
                    folder_key = key
                    break

            if not folder_key:
                return videos

            # Get dataset path
            if dataset_type.lower() == "train":
                dataset_path = DATASET_TRAIN
            else:
                dataset_path = DATASET_TEST

            class_path = dataset_path / folder_key
            if not class_path.exists():
                return videos

            # List videos
            video_files = sorted(class_path.glob(f"*{VIDEO_EXTENSION}"))
            videos = [str(f) for f in video_files]

        except Exception as e:
            self.logger.error(f"Error listing videos: {str(e)}")

        return videos

    def get_all_behavior_classes(self) -> List[str]:
        """Get all behavior class names"""
        return [info["label"] for info in self.behavior_mapping.values()]

    def get_safe_behaviors(self) -> List[str]:
        """Get safe behavior classes"""
        return [info["label"] for info in self.behavior_mapping.values() if info["is_safe"]]

    def get_unsafe_behaviors(self) -> List[str]:
        """Get unsafe behavior classes"""
        return [info["label"] for info in self.behavior_mapping.values() if not info["is_safe"]]

    def get_dataset_info(self) -> Dict:
        """Get comprehensive dataset information"""
        return {
            "statistics": self.get_dataset_statistics(),
            "all_classes": self.get_all_behavior_classes(),
            "safe_behaviors": self.get_safe_behaviors(),
            "unsafe_behaviors": self.get_unsafe_behaviors(),
            "train_path": str(DATASET_TRAIN),
            "test_path": str(DATASET_TEST)
        }


# Global dataset loader
dataset_loader = DatasetLoader()


def get_dataset_loader() -> DatasetLoader:
    """Get dataset loader instance"""
    return dataset_loader


def get_dataset_stats() -> Dict:
    """Convenience function to get dataset statistics"""
    return dataset_loader.get_dataset_statistics()


def format_file_size(bytes_size: int) -> str:
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def get_folder_size(path: Path) -> int:
    """Get total size of folder"""
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception as e:
        logger.error(f"Error calculating folder size: {str(e)}")
    return total


def ensure_directories_exist():
    """Ensure all required directories exist"""
    directories = [
        DATASET_TRAIN,
        DATASET_TEST,
        Path("reports"),
        Path("reports/json"),
        Path("logs")
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")


def validate_dataset() -> Tuple[bool, str]:
    """Validate that dataset exists and is accessible"""
    try:
        stats = dataset_loader.get_dataset_statistics()

        if stats["total_videos"] == 0:
            return False, "No videos found in dataset"

        if stats["safe_count"] == 0 and stats["unsafe_count"] == 0:
            return False, "No behaviors found in dataset"

        return True, f"Dataset validated: {stats['total_videos']} videos found"

    except Exception as e:
        return False, f"Dataset validation error: {str(e)}"
