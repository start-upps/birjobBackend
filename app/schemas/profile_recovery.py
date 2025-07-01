"""
Pydantic schemas for profile recovery functionality
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class ProfileRecoveryRequest(BaseModel):
    """Request schema for profile recovery"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # New device information
    new_device_id: str = Field(..., min_length=1, max_length=255, description="New device identifier")
    device_token: Optional[str] = Field(None, description="New APNS device token")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device characteristics for fingerprinting")
    
    # Recovery information
    email: Optional[EmailStr] = Field(None, description="Email address for recovery")
    phone: Optional[str] = Field(None, description="Phone number for recovery")
    
    # Profile information for similarity matching
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    linkedin_profile: Optional[str] = Field(None, description="LinkedIn profile URL")
    skills: Optional[List[str]] = Field(None, description="List of skills for matching")
    
    # Additional context
    approximate_registration_date: Optional[datetime] = Field(None, description="When the user originally registered")
    last_known_job_count: Optional[int] = Field(None, description="Last known saved job count")

class DeviceLinkRequest(BaseModel):
    """Request schema for manually linking device to existing profile"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    user_id: uuid.UUID = Field(..., description="Existing user ID to link to")
    new_device_id: str = Field(..., min_length=1, max_length=255, description="New device identifier")
    device_token: Optional[str] = Field(None, description="New APNS device token")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device characteristics")

class ProfileMergeRequest(BaseModel):
    """Request schema for merging duplicate profiles"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    primary_user_id: uuid.UUID = Field(..., description="User ID to keep as primary")
    secondary_user_id: uuid.UUID = Field(..., description="User ID to merge and remove")
    merge_strategy: str = Field(
        default="preserve_primary",
        description="How to handle conflicting data (preserve_primary, merge_all, manual)"
    )

class ProfilePreview(BaseModel):
    """Preview of a user profile for recovery confirmation"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    created_at: Optional[str] = None
    last_seen: Optional[str] = None
    profile_completeness: int = 0
    saved_jobs_count: Optional[int] = None
    applications_count: Optional[int] = None

class RecoveryOption(BaseModel):
    """Single recovery option with confidence level"""
    method: str = Field(..., description="Recovery method (email, phone, device_fingerprint, profile_similarity)")
    available: bool = Field(..., description="Whether this method found a match")
    confidence: str = Field(..., description="Confidence level (high, medium, low)")
    profile_preview: Optional[ProfilePreview] = Field(None, description="Preview of matched profile")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Method-specific additional information")

class RecoveryMethodResponse(BaseModel):
    """Response showing available recovery methods"""
    device_id: str = Field(..., description="Device ID that recovery is being attempted for")
    recovery_options: List[RecoveryOption] = Field(default_factory=list, description="Available recovery methods")
    total_options: int = Field(..., description="Total number of recovery options found")
    recommendation: str = Field(..., description="Recommended recovery method")
    manual_support_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Information for manual support if no automatic recovery available"
    )

class UserProfileSummary(BaseModel):
    """Summary of recovered user profile"""
    user_id: str
    device_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_completeness: int = 0
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    saved_jobs_count: Optional[int] = None
    applications_count: Optional[int] = None

class ProfileRecoveryResponse(BaseModel):
    """Response schema for profile recovery operations"""
    success: bool = Field(..., description="Whether recovery was successful")
    message: str = Field(..., description="Human-readable message about the recovery attempt")
    recovery_method: Optional[str] = Field(None, description="Method used for successful recovery")
    user_profile: Optional[UserProfileSummary] = Field(None, description="Recovered user profile data")
    
    # Additional context for failed recoveries
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested next steps if recovery failed")
    support_reference: Optional[str] = Field(None, description="Reference ID for customer support")

class DeviceRecoveryHistory(BaseModel):
    """Historical device recovery information"""
    device_token: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    last_seen: Optional[str] = None
    is_active: bool = True
    recovery_count: int = 0
    last_recovery_date: Optional[str] = None

class ProfileRecoveryStats(BaseModel):
    """Statistics about profile recovery"""
    total_recovery_attempts: int = 0
    successful_recoveries: int = 0
    recovery_by_method: Dict[str, int] = Field(default_factory=dict)
    average_recovery_confidence: float = 0.0
    most_common_failure_reason: Optional[str] = None

# Request schemas for enhanced device registration with recovery support
class EnhancedDeviceRegistrationRequest(BaseModel):
    """Enhanced device registration with recovery information"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    # Standard device registration
    device_token: str = Field(..., min_length=1, description="APNS device token")
    device_info: Dict[str, Any] = Field(..., description="Device information")
    
    # Recovery enhancement
    vendor_identifier: Optional[str] = Field(None, description="iOS vendor identifier for stable device ID")
    recovery_email: Optional[EmailStr] = Field(None, description="Email for future recovery")
    recovery_phone: Optional[str] = Field(None, description="Phone for future recovery")
    
    # Profile linking (for returning users)
    existing_profile_hint: Optional[Dict[str, Any]] = Field(
        None, 
        description="Hints about existing profile (email, phone, etc.)"
    )

class EnhancedDeviceRegistrationResponse(BaseModel):
    """Enhanced device registration response"""
    device_id: str
    user_id: str
    registered_at: str
    is_returning_user: bool = False
    profile_recovered: bool = False
    recovery_method: Optional[str] = None
    profile_completeness: int = 0
    
    # Guidance for the client
    requires_profile_setup: bool = True
    suggested_next_steps: List[str] = Field(default_factory=list)

# Validation schemas
class RecoveryValidationRequest(BaseModel):
    """Request to validate recovery information before attempting recovery"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    name_hint: Optional[str] = None
    
class RecoveryValidationResponse(BaseModel):
    """Response with validation results"""
    email_exists: bool = False
    phone_exists: bool = False
    name_matches: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    ready_for_recovery: bool = False