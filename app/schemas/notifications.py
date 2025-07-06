from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    JOB_MATCH = "job_match"
    DAILY_DIGEST = "daily_digest"
    SYSTEM = "system"

class JobMatchRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    job_id: int = Field(..., description="Job ID")
    job_title: str = Field(..., description="Job title")
    job_company: str = Field(..., description="Job company")
    job_source: Optional[str] = Field(None, description="Job source")
    matched_keywords: List[str] = Field(..., description="Keywords that matched")

class JobMatchResponse(BaseModel):
    success: bool = True
    message: str = "Job match notification processed"
    notification_sent: bool = Field(..., description="Whether notification was actually sent")
    data: Dict[str, Any] = Field(default_factory=dict)

class NotificationHistoryResponse(BaseModel):
    user_id: str
    total_notifications: int
    recent_notifications: List[Dict[str, Any]]
    data: Dict[str, Any] = Field(default_factory=dict)

class NotificationSettingsRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    notifications_enabled: bool = Field(True, description="Enable/disable notifications")
    keywords: List[str] = Field(..., description="Keywords to match for notifications")

class NotificationSettingsResponse(BaseModel):
    success: bool = True
    message: str = "Notification settings updated"
    data: Dict[str, Any] = Field(default_factory=dict)

class JobNotificationTriggerRequest(BaseModel):
    """Request to trigger job matching notifications for all users"""
    source_filter: Optional[str] = Field(None, description="Filter by job source")
    limit: Optional[int] = Field(100, description="Limit number of jobs to process")
    dry_run: bool = Field(False, description="Test mode without sending notifications")

class JobNotificationTriggerResponse(BaseModel):
    success: bool = True
    message: str = "Job notification processing completed"
    processed_jobs: int = Field(..., description="Number of jobs processed")
    matched_users: int = Field(..., description="Number of users with matches")
    notifications_sent: int = Field(..., description="Number of notifications sent")
    data: Dict[str, Any] = Field(default_factory=dict)

class NotificationJobItem(BaseModel):
    """Job item within a notification"""
    id: int
    title: str
    company: str
    location: Optional[str] = None
    apply_link: str
    posted_at: str
    source: str

class NotificationInboxItem(BaseModel):
    """Single notification item in inbox"""
    id: str
    type: str = "job_match"
    title: str
    message: str
    matched_keywords: List[str]
    job_count: int
    created_at: str
    is_read: bool = False
    jobs: List[NotificationJobItem]

class NotificationInboxResponse(BaseModel):
    """Notification inbox response"""
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

class MarkReadResponse(BaseModel):
    """Mark notification as read response"""
    success: bool = True
    message: str = "Notification marked as read"

class DeleteNotificationResponse(BaseModel):
    """Delete notification response"""
    success: bool = True
    message: str = "Notification deleted successfully"