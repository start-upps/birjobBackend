from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/birjob_ios"
    
    # Redis - Support both standard Redis and Upstash REST
    REDIS_URL: str = "redis://localhost:6379/0"
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_KEY: str = "your-api-key-change-in-production"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Apple Push Notifications
    APNS_PRIVATE_KEY: Optional[str] = """-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgrOxq/lSe01cgSrMH
nkF1KrQI5cUjn43qqZFnsIWaHhSgCgYIKoZIzj0DAQehRANCAATIK3apIL+/6Oqn
9apRsv7kW3nGc8TWLWPSdcg/AhBVIN61PqiI2Hkm1t064JNR+EBHOhwfVRYrj7nC
OvjzFGyZ
-----END PRIVATE KEY-----"""
    APNS_KEY_PATH: str = "/etc/secrets/AuthKey_ZV2X5Y7D76.p8"  # Path to your APNS key file
    APNS_KEY_ID: str = "ZV2X5Y7D76"  # New production key ID
    APNS_TEAM_ID: str = "KK5HUUQ3HR"  # Apple Developer Team ID  
    APNS_BUNDLE_ID: str = "com.ismats.birjob"  # iOS app bundle ID
    APNS_SANDBOX: bool = False  # Production mode for TestFlight
    
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
    
    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

settings = Settings()