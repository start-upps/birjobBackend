from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for better validation
class RemoteWorkPreference(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "onsite"

class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class SalaryCurrency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"

# Unified User Schema
class UnifiedUserBase(BaseModel):
    """Base schema for unified user"""
    device_id: str = Field(..., max_length=255)
    
    # Personal Information
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    current_job_title: Optional[str] = Field(None, max_length=255)
    years_of_experience: Optional[str] = Field(None, max_length=255)
    linkedin_profile: Optional[str] = Field(None, max_length=255)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    
    # Job Preferences
    desired_job_types: Optional[List[str]] = Field(default_factory=list)
    remote_work_preference: Optional[RemoteWorkPreference] = RemoteWorkPreference.HYBRID
    skills: Optional[List[str]] = Field(default_factory=list)
    preferred_locations: Optional[List[str]] = Field(default_factory=list)
    
    # Salary Information
    min_salary: Optional[int] = Field(None, ge=0)
    max_salary: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[SalaryCurrency] = SalaryCurrency.USD
    salary_negotiable: Optional[bool] = True
    
    # Keyword Matching
    match_keywords: Optional[List[str]] = Field(default_factory=list)
    
    # Notification Settings
    job_matches_enabled: Optional[bool] = True
    application_reminders_enabled: Optional[bool] = True
    weekly_digest_enabled: Optional[bool] = True
    market_insights_enabled: Optional[bool] = False
    quiet_hours_enabled: Optional[bool] = False
    quiet_hours_start: Optional[str] = Field(None, max_length=10)
    quiet_hours_end: Optional[str] = Field(None, max_length=10)
    preferred_notification_time: Optional[str] = Field(None, max_length=10)
    
    # Privacy Settings
    profile_visibility: Optional[ProfileVisibility] = ProfileVisibility.PRIVATE
    share_analytics: Optional[bool] = False
    share_job_view_history: Optional[bool] = False
    allow_personalized_recommendations: Optional[bool] = True
    
    # Additional flexible data
    additional_personal_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    additional_job_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)
    additional_notification_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    additional_privacy_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('max_salary')
    def max_salary_greater_than_min(cls, v, values):
        if v is not None and 'min_salary' in values and values['min_salary'] is not None:
            if v < values['min_salary']:
                raise ValueError('max_salary must be greater than or equal to min_salary')
        return v

    @validator('match_keywords')
    def validate_keywords(cls, v):
        if v:
            # Remove duplicates and empty strings
            v = list(set(kw.strip().lower() for kw in v if kw and kw.strip()))
            # Limit to 50 keywords
            if len(v) > 50:
                raise ValueError('Maximum 50 keywords allowed')
        return v

class UnifiedUserCreate(UnifiedUserBase):
    """Schema for creating a unified user"""
    pass

class UnifiedUserUpdate(BaseModel):
    """Schema for updating a unified user (all fields optional)"""
    # Personal Information
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    current_job_title: Optional[str] = Field(None, max_length=255)
    years_of_experience: Optional[str] = Field(None, max_length=255)
    linkedin_profile: Optional[str] = Field(None, max_length=255)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    
    # Job Preferences
    desired_job_types: Optional[List[str]] = None
    remote_work_preference: Optional[RemoteWorkPreference] = None
    skills: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    
    # Salary Information
    min_salary: Optional[int] = Field(None, ge=0)
    max_salary: Optional[int] = Field(None, ge=0)
    salary_currency: Optional[SalaryCurrency] = None
    salary_negotiable: Optional[bool] = None
    
    # Keyword Matching
    match_keywords: Optional[List[str]] = None
    
    # Notification Settings
    job_matches_enabled: Optional[bool] = None
    application_reminders_enabled: Optional[bool] = None
    weekly_digest_enabled: Optional[bool] = None
    market_insights_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, max_length=10)
    quiet_hours_end: Optional[str] = Field(None, max_length=10)
    preferred_notification_time: Optional[str] = Field(None, max_length=10)
    
    # Privacy Settings
    profile_visibility: Optional[ProfileVisibility] = None
    share_analytics: Optional[bool] = None
    share_job_view_history: Optional[bool] = None
    allow_personalized_recommendations: Optional[bool] = None
    
    # Additional flexible data
    additional_personal_info: Optional[Dict[str, Any]] = None
    additional_job_preferences: Optional[Dict[str, Any]] = None
    additional_notification_settings: Optional[Dict[str, Any]] = None
    additional_privacy_settings: Optional[Dict[str, Any]] = None

class UnifiedUserResponse(UnifiedUserBase):
    """Schema for unified user response"""
    id: str
    profile_completeness: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Keyword management schemas
class UpdateKeywordsRequest(BaseModel):
    match_keywords: List[str] = Field(..., max_items=50)

    @validator('match_keywords')
    def validate_keywords(cls, v):
        # Remove duplicates and empty strings
        v = list(set(kw.strip().lower() for kw in v if kw and kw.strip()))
        return v

class AddKeywordRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)

    @validator('keyword')
    def validate_keyword(cls, v):
        return v.strip().lower()

class KeywordResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any]

# Compatibility schemas for legacy endpoints
class PersonalInfo(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    currentJobTitle: Optional[str] = None
    yearsOfExperience: Optional[str] = None
    linkedInProfile: Optional[str] = None
    portfolioURL: Optional[str] = None
    bio: Optional[str] = None

class JobPreferences(BaseModel):
    desiredJobTypes: Optional[List[str]] = Field(default_factory=list)
    remoteWorkPreference: Optional[RemoteWorkPreference] = RemoteWorkPreference.HYBRID
    skills: Optional[List[str]] = Field(default_factory=list)
    preferredLocations: Optional[List[str]] = Field(default_factory=list)
    salaryRange: Optional[Dict[str, Any]] = None
    matchKeywords: Optional[List[str]] = Field(default_factory=list)  # New field

class NotificationSettings(BaseModel):
    jobMatchesEnabled: Optional[bool] = True
    applicationRemindersEnabled: Optional[bool] = True
    weeklyDigestEnabled: Optional[bool] = True
    marketInsightsEnabled: Optional[bool] = False
    quietHoursEnabled: Optional[bool] = False
    quietHoursStart: Optional[str] = None
    quietHoursEnd: Optional[str] = None
    preferredNotificationTime: Optional[str] = None

class PrivacySettings(BaseModel):
    profileVisibility: Optional[ProfileVisibility] = ProfileVisibility.PRIVATE
    shareAnalytics: Optional[bool] = False
    shareJobViewHistory: Optional[bool] = False
    allowPersonalizedRecommendations: Optional[bool] = True

# Legacy user profile schema for backward compatibility
class UserProfile(BaseModel):
    userId: str
    deviceId: str
    personalInfo: Optional[PersonalInfo] = None
    jobPreferences: Optional[JobPreferences] = None
    notificationSettings: Optional[NotificationSettings] = None
    privacySettings: Optional[PrivacySettings] = None
    profileCompleteness: int
    createdAt: datetime
    lastUpdated: datetime

class UserProfileCreate(BaseModel):
    deviceId: str
    personalInfo: Optional[PersonalInfo] = None
    jobPreferences: Optional[JobPreferences] = None
    notificationSettings: Optional[NotificationSettings] = None
    privacySettings: Optional[PrivacySettings] = None

class UserProfileResponse(BaseModel):
    success: bool
    message: str = ""
    data: UserProfile

class UserProfileUpdateResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

# Other response schemas
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None

# Job-related schemas (keeping existing ones)
class SaveJobRequest(BaseModel):
    jobId: int = Field(..., gt=0)

class SavedJobsListResponse(BaseModel):
    success: bool
    data: Dict[str, Any]

class JobViewRequest(BaseModel):
    jobId: int = Field(..., gt=0)
    viewDuration: Optional[int] = Field(None, ge=0)

class UserAnalyticsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]

class ApplicationHistoryResponse(BaseModel):
    success: bool
    data: Dict[str, Any]