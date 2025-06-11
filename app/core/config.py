from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/birjob_ios"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY: str = "your-api-key-change-in-production"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Apple Push Notifications
    APNS_KEY_PATH: str = "/secrets/apns.p8"
    APNS_KEY_ID: str = "your-apns-key-id"
    APNS_TEAM_ID: str = "your-team-id"
    APNS_BUNDLE_ID: str = "com.yourcompany.birjob"
    APNS_SANDBOX: bool = True
    
    # Background Jobs
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: str = "1000 per hour"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    
    # Job Matching
    MATCH_ENGINE_INTERVAL_MINUTES: int = 5
    MAX_NOTIFICATIONS_PER_HOUR: int = 5
    MAX_NOTIFICATIONS_PER_DAY: int = 20
    QUIET_HOURS_START: int = 22  # 10 PM
    QUIET_HOURS_END: int = 8     # 8 AM
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()