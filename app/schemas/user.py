from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for better validation
class RemoteWorkPreference(str, Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ON_SITE = "On-site"

class ProfileVisibility(str, Enum):
    PUBLIC = "Public"
    PRIVATE = "Private"

class ApplicationStatus(str, Enum):
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    OFFERED = "offered"

class JobApplicationStatus(str, Enum):
    PENDING = "pending"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"

# Nested schemas
class PersonalInfo(BaseModel):
    firstName: Optional[str] = Field(None, max_length=100)
    lastName: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    currentJobTitle: Optional[str] = Field(None, max_length=255)
    yearsOfExperience: Optional[str] = Field(None, max_length=50)
    linkedInProfile: Optional[str] = Field(None, max_length=500)
    portfolioURL: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None

class SalaryRange(BaseModel):
    minSalary: Optional[int] = Field(None, ge=0)
    maxSalary: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field("USD", max_length=10)
    isNegotiable: Optional[bool] = True

    @validator('maxSalary')
    def max_salary_greater_than_min(cls, v, values):
        if v is not None and 'minSalary' in values and values['minSalary'] is not None:
            if v < values['minSalary']:
                raise ValueError('maxSalary must be greater than or equal to minSalary')
        return v

class JobPreferences(BaseModel):
    desiredJobTypes: Optional[List[str]] = []
    remoteWorkPreference: Optional[RemoteWorkPreference] = RemoteWorkPreference.HYBRID
    skills: Optional[List[str]] = []
    preferredLocations: Optional[List[str]] = []
    salaryRange: Optional[SalaryRange] = None

class NotificationSettings(BaseModel):
    jobMatchesEnabled: Optional[bool] = True
    applicationRemindersEnabled: Optional[bool] = True
    weeklyDigestEnabled: Optional[bool] = False
    marketInsightsEnabled: Optional[bool] = True
    quietHoursEnabled: Optional[bool] = True
    quietHoursStart: Optional[str] = Field("22:00", regex=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    quietHoursEnd: Optional[str] = Field("08:00", regex=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    preferredNotificationTime: Optional[str] = Field("09:00", regex=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')

class PrivacySettings(BaseModel):
    profileVisibility: Optional[ProfileVisibility] = ProfileVisibility.PUBLIC
    shareAnalytics: Optional[bool] = True
    shareJobViewHistory: Optional[bool] = False
    allowPersonalizedRecommendations: Optional[bool] = True

# Main schemas
class UserProfileCreate(BaseModel):
    deviceId: str = Field(..., min_length=1, max_length=255)
    personalInfo: Optional[PersonalInfo] = None
    jobPreferences: Optional[JobPreferences] = None
    notificationSettings: Optional[NotificationSettings] = None
    privacySettings: Optional[PrivacySettings] = None

class UserProfileResponse(BaseModel):
    userId: str
    deviceId: str
    personalInfo: Optional[PersonalInfo] = None
    jobPreferences: Optional[JobPreferences] = None
    notificationSettings: Optional[NotificationSettings] = None
    privacySettings: Optional[PrivacySettings] = None
    profileCompleteness: int
    createdAt: datetime
    lastUpdated: datetime

class UserProfileUpdateResponse(BaseModel):
    success: bool = True
    message: str
    data: Dict[str, Any]

# AI Recommendations schemas
class JobRecommendationFilters(BaseModel):
    jobType: Optional[str] = None
    location: Optional[str] = None
    remoteWork: Optional[str] = None

class JobRecommendationRequest(BaseModel):
    deviceId: str = Field(..., min_length=1)
    limit: Optional[int] = Field(20, ge=1, le=100)
    filters: Optional[JobRecommendationFilters] = None

class AIInsights(BaseModel):
    whyRecommended: str
    skillsMatch: List[str]
    missingSkills: List[str]
    salaryFit: str
    locationFit: str

class JobRecommendation(BaseModel):
    jobId: int
    title: str
    companyName: str
    location: str
    salary: str
    postedDate: datetime
    matchScore: int = Field(..., ge=0, le=100)
    aiInsights: AIInsights
    matchReasons: List[str]

class JobRecommendationsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]

class JobMatchAnalysisRequest(BaseModel):
    deviceId: str = Field(..., min_length=1)
    jobId: int = Field(..., gt=0)

# Saved Jobs schemas
class SaveJobRequest(BaseModel):
    jobId: int = Field(..., gt=0)
    notes: Optional[str] = None

class SavedJobResponse(BaseModel):
    savedJobId: str
    jobId: int
    title: str
    companyName: str
    location: str
    salary: str
    postedDate: datetime
    savedAt: datetime
    notes: Optional[str] = None
    applicationStatus: ApplicationStatus

class SavedJobsListResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]

# Analytics schemas
class JobViewRequest(BaseModel):
    jobId: int = Field(..., gt=0)
    viewDuration: int = Field(..., ge=0)  # seconds
    source: str = Field(..., max_length=50)
    timestamp: datetime

class ProfileInsights(BaseModel):
    profileStrength: int = Field(..., ge=0, le=100)
    profileCompleteness: int = Field(..., ge=0, le=100)
    skillsAssessment: str
    marketFit: int = Field(..., ge=0, le=100)
    improvementAreas: List[str]

class JobActivity(BaseModel):
    totalJobsViewed: int
    totalJobsSaved: int
    totalApplications: int
    averageViewTime: str
    mostViewedCategories: List[str]
    lastWeekActivity: Dict[str, int]

class MatchingInsights(BaseModel):
    totalMatches: int
    averageMatchScore: int
    topMatchingCompanies: List[str]
    recommendedSkills: List[str]

class MarketInsight(BaseModel):
    insight: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    category: str

class UserAnalyticsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]

# Application tracking schemas
class JobApplicationResponse(BaseModel):
    applicationId: str
    jobId: int
    title: str
    companyName: str
    appliedAt: datetime
    status: JobApplicationStatus
    notes: Optional[str] = None
    followUpDate: Optional[datetime] = None

class ApplicationHistoryResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]

# Profile sync schemas
class SyncData(BaseModel):
    profile: bool = True
    savedJobs: bool = True
    preferences: bool = True
    analytics: bool = True

class ProfileSyncRequest(BaseModel):
    sourceDeviceId: str = Field(..., min_length=1)
    targetDeviceId: str = Field(..., min_length=1)
    syncData: SyncData

class ProfileSyncResponse(BaseModel):
    success: bool = True
    message: str
    data: Dict[str, Any]

# Generic response schemas
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    reason: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, Any]