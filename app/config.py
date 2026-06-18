from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///data/database.db"
    
    # Video processing
    VIDEO_FPS: int = 30
    DETECTION_THRESHOLD: float = 0.5
    
    # Policy document path
    POLICY_PATH: str = "Compliance_Policy_Manual.pdf"
    
    # Report storage
    REPORTS_DIR: str = "data/reports"
    
    # Alert settings
    ALERT_TIMEOUT: int = 60  # seconds
    
    class Config:
        env_file = ".env"

settings = Settings()