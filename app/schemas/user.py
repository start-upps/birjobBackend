from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Simple User schemas matching the simplified model
class UserBase(BaseModel):
    device_id: str = Field(..., max_length=255)
    email: Optional[EmailStr] = None
    keywords: Optional[List[str]] = Field(default_factory=list)
    preferred_sources: Optional[List[str]] = Field(default_factory=list)
    notifications_enabled: Optional[bool] = True

class UserCreate(UserBase):
    """Create user with minimal required fields"""
    pass

class UserRegistrationRequest(BaseModel):
    """Unified user registration with device token for iOS app"""
    device_id: str = Field(..., description="Unique device identifier")
    device_token: str = Field(..., description="APNs device token")
    email: EmailStr = Field(..., description="User email")
    keywords: List[str] = Field(..., description="Notification keywords")
    preferred_sources: List[str] = Field(default_factory=list, description="Preferred job sources")
    device_info: Dict[str, Any] = Field(..., description="Device information")

class UserRegistrationResponse(BaseModel):
    """User registration response"""
    success: bool = True
    message: str = "User registered successfully"
    data: Dict[str, Any] = Field(default_factory=dict)

class UserUpdate(BaseModel):
    """Update user - all fields optional"""
    email: Optional[EmailStr] = None
    keywords: Optional[List[str]] = None
    preferred_sources: Optional[List[str]] = None
    notifications_enabled: Optional[bool] = None

class UserResponse(UserBase):
    """User response with metadata"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_notified_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Keyword management (simple)
class AddKeywordRequest(BaseModel):
    device_id: str
    keyword: str = Field(..., min_length=2, max_length=50)

class RemoveKeywordRequest(BaseModel):
    device_id: str
    keyword: str

class UpdateKeywordsRequest(BaseModel):
    device_id: str
    keywords: List[str] = Field(..., max_items=20)

# Job interaction (simple)
class SaveJobRequest(BaseModel):
    device_id: str
    job_id: int = Field(..., gt=0)

class JobViewRequest(BaseModel):
    device_id: str
    job_id: int = Field(..., gt=0)

# Email-based user lookup (matching your website approach)
class EmailUserRequest(BaseModel):
    email: EmailStr

class EmailKeywordRequest(BaseModel):
    email: EmailStr
    keyword: str = Field(..., min_length=2, max_length=50)

# Standard responses
class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None