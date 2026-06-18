import os
import glob
from pathlib import Path
from typing import List, Dict, Any
import random
from .config import settings

class DataLoader:
    """Helper class to load and manage dataset"""
    
    def __init__(self):
        self.train_dir = settings.TRAIN_DIR
        self.test_dir = settings.TEST_DIR
        self.class_mapping = settings.CLASS_MAPPING
        
    def get_all_videos(self, split: str = "train") -> List[Dict[str, Any]]:
        """Get all videos from train or test split with their labels"""
        videos = []
        split_dir = self.train_dir if split == "train" else self.test_dir
        
        for folder_name in os.listdir(split_dir):
            folder_path = split_dir / folder_name
            
            if folder_path.is_dir() and folder_name in self.class_mapping:
                class_info = self.class_mapping[folder_name]
                
                # Get all video files
                video_files = glob.glob(str(folder_path / "*.mp4"))
                video_files.extend(glob.glob(str(folder_path / "*.avi")))
                video_files.extend(glob.glob(str(folder_path / "*.mov")))
                
                for video_path in video_files:
                    videos.append({
                        "path": video_path,
                        "folder_name": folder_name,
                        "class_name": class_info["policy_class"],
                        "is_unsafe": class_info["is_unsafe"],
                        "severity": class_info["severity"],
                        "split": split
                    })
        
        return videos
    
    def get_videos_by_class(self, class_name: str, split: str = "train") -> List[str]:
        """Get videos for a specific behavior class"""
        videos = self.get_all_videos(split)
        return [v["path"] for v in videos if v["folder_name"] == class_name]
    
    def get_unsafe_videos(self, split: str = "train") -> List[Dict[str, Any]]:
        """Get only unsafe behavior videos"""
        videos = self.get_all_videos(split)
        return [v for v in videos if v["is_unsafe"]]
    
    def get_safe_videos(self, split: str = "train") -> List[Dict[str, Any]]:
        """Get only safe behavior videos"""
        videos = self.get_all_videos(split)
        return [v for v in videos if not v["is_unsafe"]]
    
    def get_random_video(self, split: str = "train", unsafe_only: bool = False) -> Dict[str, Any]:
        """Get a random video"""
        videos = self.get_all_videos(split)
        if unsafe_only:
            videos = [v for v in videos if v["is_unsafe"]]
        return random.choice(videos) if videos else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        stats = {
            "train": {"total": 0, "unsafe": 0, "safe": 0},
            "test": {"total": 0, "unsafe": 0, "safe": 0}
        }
        
        for split in ["train", "test"]:
            videos = self.get_all_videos(split)
            stats[split]["total"] = len(videos)
            stats[split]["unsafe"] = len([v for v in videos if v["is_unsafe"]])
            stats[split]["safe"] = len([v for v in videos if not v["is_unsafe"]])
            
            # Count by class
            class_counts = {}
            for v in videos:
                class_name = v["class_name"]
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
            stats[split]["class_counts"] = class_counts
        
        return stats

# Create a global instance for easy access
data_loader = DataLoader()