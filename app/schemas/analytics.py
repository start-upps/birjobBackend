from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# Enums for validation
class ActionType(str, Enum):
    VIEW_JOB = "view_job"
    SAVE_JOB = "save_job"
    UNSAVE_JOB = "unsave_job"
    SEARCH = "search"
    APPLY_JOB = "apply_job"
    SHARE_JOB = "share_job"
    FILTER_JOBS = "filter_jobs"
    VIEW_COMPANY = "view_company"
    UPDATE_PROFILE = "update_profile"
    CHANGE_PREFERENCES = "change_preferences"

class NotificationType(str, Enum):
    JOB_MATCH = "job_match"
    APPLICATION_REMINDER = "application_reminder"
    WEEKLY_DIGEST = "weekly_digest"
    MARKET_INSIGHTS = "market_insights"
    SYSTEM_UPDATE = "system_update"

class DeliveryStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    PENDING = "pending"

# Session Management Schemas
class SessionStartRequest(BaseModel):
    device_id: str
    app_version: str = Field(..., max_length=20)
    os_version: str = Field(..., max_length=20)

class SessionEndRequest(BaseModel):
    session_id: str
    actions_count: int = Field(0, ge=0)
    jobs_viewed_count: int = Field(0, ge=0)
    jobs_saved_count: int = Field(0, ge=0)
    searches_performed: int = Field(0, ge=0)

class SessionResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

# User Action Schemas
class UserActionRequest(BaseModel):
    device_id: str
    session_id: Optional[str] = None
    action_type: ActionType
    action_details: Dict[str, Any] = Field(default_factory=dict)
    job_id: Optional[int] = None
    search_id: Optional[str] = None  # New: reference to search_analytics
    search_query: Optional[str] = Field(None, max_length=500)
    page_url: Optional[str] = Field(None, max_length=500)
    duration_seconds: int = Field(0, ge=0)

class UserActionResponse(BaseModel):
    success: bool = True
    message: str = "Action recorded successfully"

# Search Analytics Schemas
class SearchRequest(BaseModel):
    device_id: str
    session_id: Optional[str] = None  # New: reference to user_sessions
    search_query: str = Field(..., min_length=1, max_length=500)
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('search_query')
    def validate_search_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Search query cannot be empty')
        return v.strip()

class SearchResultsRequest(BaseModel):
    device_id: str
    search_query: str
    results_count: int = Field(0, ge=0)
    result_job_ids: List[int] = Field(default_factory=list)
    time_to_first_click: Optional[int] = Field(None, ge=0)

class SearchClickRequest(BaseModel):
    device_id: str
    search_query: str
    clicked_job_ids: List[int]
    total_session_time: int = Field(0, ge=0)

class SearchResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

# Job Engagement Schemas
class JobEngagementRequest(BaseModel):
    device_id: str
    session_id: Optional[str] = None  # New: reference to user_sessions
    job_id: int = Field(..., gt=0)
    job_title: Optional[str] = Field(None, max_length=500)
    job_company: Optional[str] = Field(None, max_length=255)
    job_source: Optional[str] = Field(None, max_length=100)
    job_location: Optional[str] = Field(None, max_length=255)
    view_duration_seconds: int = Field(0, ge=0)

class JobApplicationRequest(BaseModel):
    device_id: str
    job_id: int = Field(..., gt=0)
    application_source: str = Field(..., max_length=100)

class JobEngagementResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

# Notification Analytics Schemas
class NotificationRequest(BaseModel):
    device_id: str
    notification_type: NotificationType
    notification_title: str = Field(..., max_length=200)
    notification_body: str
    job_id: Optional[int] = None

class NotificationDeliveryRequest(BaseModel):
    notification_id: str
    delivery_status: DeliveryStatus
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None

class NotificationEngagementRequest(BaseModel):
    notification_id: str
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    led_to_app_open: bool = False
    led_to_job_view: bool = False
    led_to_job_save: bool = False

class NotificationResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

# Analytics Report Schemas
class UserAnalyticsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]

class DashboardMetrics(BaseModel):
    total_users: int
    active_users_24h: int
    active_users_7d: int
    active_users_30d: int
    total_sessions_24h: int
    avg_session_duration: float
    total_job_views_24h: int
    total_job_saves_24h: int
    total_searches_24h: int
    notification_delivery_rate: float

class UserEngagementMetrics(BaseModel):
    user_id: str
    email: Optional[str]
    user_since: datetime
    total_sessions: int
    total_time_spent: int
    unique_jobs_viewed: int
    total_jobs_saved: int
    total_searches: int
    avg_engagement_score: Optional[float]
    last_active: Optional[datetime]

class JobEngagementMetrics(BaseModel):
    job_id: int
    job_title: str
    job_company: str
    total_views: int
    unique_viewers: int
    avg_view_time: float
    total_saves: int
    save_rate: float
    total_applications: int
    application_rate: float
    avg_engagement_score: float

class SearchAnalyticsMetrics(BaseModel):
    search_query: str
    search_count: int
    avg_results_count: float
    avg_clicks_per_search: float
    click_through_rate: float
    avg_time_to_first_click: Optional[float]

class NotificationMetrics(BaseModel):
    notification_type: str
    total_sent: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    conversion_rate: float

# Response schemas for analytics endpoints
class AnalyticsOverviewResponse(BaseModel):
    success: bool = True
    data: DashboardMetrics

class UserEngagementResponse(BaseModel):
    success: bool = True
    data: List[UserEngagementMetrics]

class JobAnalyticsResponse(BaseModel):
    success: bool = True
    data: List[JobEngagementMetrics]

class SearchAnalyticsResponse(BaseModel):
    success: bool = True
    data: List[SearchAnalyticsMetrics]

class NotificationAnalyticsResponse(BaseModel):
    success: bool = True
    data: List[NotificationMetrics]

# Real-time analytics schemas
class RealTimeMetrics(BaseModel):
    active_users_now: int
    sessions_last_hour: int
    job_views_last_hour: int
    searches_last_hour: int
    notifications_sent_last_hour: int

class RealTimeResponse(BaseModel):
    success: bool = True
    data: RealTimeMetrics
    timestamp: datetime

# User behavior analysis schemas
class UserBehaviorPattern(BaseModel):
    pattern_type: str
    description: str
    frequency: int
    confidence_score: float

class UserBehaviorAnalysis(BaseModel):
    user_id: str
    patterns: List[UserBehaviorPattern]
    recommendations: List[str]
    engagement_trend: str  # "increasing", "stable", "decreasing"

class BehaviorAnalysisResponse(BaseModel):
    success: bool = True
    data: UserBehaviorAnalysis