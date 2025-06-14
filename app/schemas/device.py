from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class DeviceInfo(BaseModel):
    os_version: str = Field(alias='osVersion')
    app_version: str = Field(alias='appVersion')
    device_model: str = Field(alias='deviceModel')
    timezone: str
    
    class Config:
        populate_by_name = True

class DeviceRegisterRequest(BaseModel):
    device_token: str = Field(..., min_length=64, max_length=255)
    device_info: DeviceInfo

class DeviceRegisterResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

class LocationFilters(BaseModel):
    cities: Optional[List[str]] = None
    remote_only: Optional[bool] = False

class KeywordSubscriptionRequest(BaseModel):
    device_id: str
    keywords: List[str] = Field(..., min_items=1, max_items=20)
    sources: Optional[List[str]] = None
    location_filters: Optional[LocationFilters] = None

class KeywordSubscriptionResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

class KeywordSubscriptionInfo(BaseModel):
    subscription_id: str
    keywords: List[str]
    sources: Optional[List[str]]
    location_filters: Optional[LocationFilters]
    created_at: datetime
    last_match: Optional[datetime] = None

class KeywordSubscriptionsResponse(BaseModel):
    success: bool = True
    data: Dict[str, List[KeywordSubscriptionInfo]] = Field(default_factory=dict)

class Job(BaseModel):
    id: int
    title: str
    company: str
    apply_link: str
    source: str
    posted_at: datetime

class JobMatch(BaseModel):
    match_id: str
    job: Job
    matched_keywords: List[str]
    relevance_score: float
    matched_at: datetime

class Pagination(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool

class JobMatchesResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

class MarkReadRequest(BaseModel):
    match_id: str

class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None