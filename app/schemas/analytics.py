from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ActionType(str, Enum):
    APP_OPEN = "app_open"
    APP_CLOSE = "app_close"
    JOB_VIEW = "job_view"
    JOB_SAVE = "job_save"
    JOB_UNSAVE = "job_unsave"
    SEARCH = "search"
    PROFILE_UPDATE = "profile_update"
    SETTINGS_CHANGE = "settings_change"
    NOTIFICATION_CLICK = "notification_click"
    CHATBOT_MESSAGE = "chatbot_message"
    JOB_RECOMMENDATIONS = "job_recommendations"
    JOB_ANALYSIS = "job_analysis"
    JOBS_CLEAR_ALL_INDIVIDUAL = "jobs_clear_all_individual"

class AnalyticsEventRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    action_type: ActionType = Field(..., description="Type of action performed")
    action_data: Dict[str, Any] = Field(default_factory=dict, description="Additional action data")
    session_id: Optional[str] = Field(None, description="Session identifier")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="Device information")

class AnalyticsEventResponse(BaseModel):
    success: bool = True
    message: str = "Analytics event recorded successfully"
    data: Dict[str, Any] = Field(default_factory=dict)

class UserAnalyticsResponse(BaseModel):
    user_id: str
    total_events: int
    events_by_type: Dict[str, int]
    first_event: Optional[datetime]
    last_event: Optional[datetime]
    data: Dict[str, Any] = Field(default_factory=dict)

class AnalyticsStatsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)