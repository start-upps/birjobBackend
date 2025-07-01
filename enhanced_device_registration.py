"""
Enhanced Device Registration with Profile Recovery
Add this to your devices.py endpoint file or create as a separate enhancement
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, Any, Optional
import uuid
import logging
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.device import DeviceToken
from app.models.user import User
from app.schemas.profile_recovery import (
    EnhancedDeviceRegistrationRequest, 
    EnhancedDeviceRegistrationResponse,
    ProfileRecoveryRequest
)
from app.api.v1.endpoints.profile_recovery import ProfileRecoveryService

logger = logging.getLogger(__name__)

class EnhancedDeviceRegistration:
    """Enhanced device registration with automatic profile recovery"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.recovery_service = ProfileRecoveryService(db)
    
    def generate_stable_device_id(self, request: EnhancedDeviceRegistrationRequest) -> str:
        """Generate a stable device ID preferring vendor identifier"""
        # Priority order for device ID generation:
        # 1. iOS vendor identifier (most stable)
        # 2. Device ID from device_info
        # 3. Device token as fallback
        
        if request.vendor_identifier:
            return f"vendor_{request.vendor_identifier}"
        
        if request.device_info.get('device_id'):
            return request.device_info['device_id']
        
        # Use device token but warn about instability
        logger.warning("Using device_token as device_id - this may cause profile loss on app reinstall")
        return request.device_token
    
    async def attempt_profile_recovery(
        self, 
        device_id: str, 
        request: EnhancedDeviceRegistrationRequest
    ) -> tuple[Optional[User], Optional[str]]:
        """Attempt to recover existing profile during registration"""
        
        # Check if existing profile hints are provided
        if not request.existing_profile_hint:
            return None, None
        
        hints = request.existing_profile_hint
        recovered_user = None
        recovery_method = None
        
        # Try email recovery
        if hints.get('email'):
            user = await self.recovery_service.find_user_by_email(hints['email'])
            if user:
                recovered_user = user
                recovery_method = "email"
        
        # Try phone recovery
        if not recovered_user and hints.get('phone'):
            user = await self.recovery_service.find_user_by_phone(hints['phone'])
            if user:
                recovered_user = user
                recovery_method = "phone"
        
        # Try device fingerprint
        if not recovered_user and request.device_info:
            fingerprint = await self.recovery_service.generate_device_fingerprint(request.device_info)
            user = await self.recovery_service.find_user_by_device_fingerprint(fingerprint)
            if user:
                recovered_user = user
                recovery_method = "device_fingerprint"
        
        # If we found a user, update their device_id
        if recovered_user:
            success = await self.recovery_service.update_device_id(recovered_user, device_id)
            if success:
                logger.info(f"Successfully recovered profile for user {recovered_user.id} using {recovery_method}")
                return recovered_user, recovery_method
            else:
                logger.warning(f"Found profile but failed to update device_id for user {recovered_user.id}")
        
        return None, None
    
    async def register_or_recover_device(
        self, 
        request: EnhancedDeviceRegistrationRequest
    ) -> EnhancedDeviceRegistrationResponse:
        """Main registration/recovery logic"""
        
        device_id = self.generate_stable_device_id(request)
        is_returning_user = False
        profile_recovered = False
        recovery_method = None
        
        # First, check if device_id already exists
        existing_user_stmt = select(User).where(User.device_id == device_id)
        existing_user_result = await self.db.execute(existing_user_stmt)
        user = existing_user_result.scalar_one_or_none()
        
        # If no user found, attempt recovery
        if not user:
            user, recovery_method = await self.attempt_profile_recovery(device_id, request)
            if user:
                is_returning_user = True
                profile_recovered = True
        else:
            # User already exists with this device_id
            is_returning_user = True
            logger.info(f"Found existing user {user.id} for device_id {device_id}")
        
        # If still no user, create new one
        if not user:
            user = User(device_id=device_id)
            
            # Pre-populate with recovery information if provided
            if request.recovery_email:
                user.email = request.recovery_email
            if request.recovery_phone:
                user.phone = request.recovery_phone
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Created new user {user.id} for device_id {device_id}")
        
        # Register or update device token
        device_token = await self.register_device_token(user, request)
        
        # Determine suggested next steps
        suggested_steps = []
        requires_profile_setup = True
        
        if is_returning_user:
            if user.profile_completeness and user.profile_completeness > 50:
                requires_profile_setup = False
                suggested_steps.append("Review and update your profile if needed")
                suggested_steps.append("Check your saved jobs and applications")
            else:
                suggested_steps.append("Complete your profile setup")
                suggested_steps.append("Add your skills and job preferences")
        else:
            suggested_steps.append("Complete your profile setup")
            suggested_steps.append("Add your email and phone for account recovery")
            suggested_steps.append("Set up your job preferences and skills")
        
        return EnhancedDeviceRegistrationResponse(
            device_id=device_id,
            user_id=str(user.id),
            registered_at=datetime.now(timezone.utc).isoformat(),
            is_returning_user=is_returning_user,
            profile_recovered=profile_recovered,
            recovery_method=recovery_method,
            profile_completeness=user.profile_completeness or 0,
            requires_profile_setup=requires_profile_setup,
            suggested_next_steps=suggested_steps
        )
    
    async def register_device_token(
        self, 
        user: User, 
        request: EnhancedDeviceRegistrationRequest
    ) -> DeviceToken:
        """Register or update device token for user"""
        
        # Check if device token already exists
        existing_token_stmt = select(DeviceToken).where(
            DeviceToken.device_token == request.device_token
        )
        existing_token_result = await self.db.execute(existing_token_stmt)
        device_token = existing_token_result.scalar_one_or_none()
        
        # Enhance device_info with fingerprint
        enhanced_device_info = request.device_info.copy()
        if request.device_info:
            fingerprint = await self.recovery_service.generate_device_fingerprint(request.device_info)
            enhanced_device_info['fingerprint'] = fingerprint
        
        if device_token:
            # Update existing device token
            device_token.user_id = user.id
            device_token.device_info = enhanced_device_info
            device_token.is_active = True
            device_token.last_seen = datetime.now(timezone.utc)
            device_token.updated_at = datetime.now(timezone.utc)
        else:
            # Create new device token
            device_token = DeviceToken(
                user_id=user.id,
                device_token=request.device_token,
                device_info=enhanced_device_info,
                is_active=True,
                last_seen=datetime.now(timezone.utc)
            )
            self.db.add(device_token)
        
        await self.db.commit()
        await self.db.refresh(device_token)
        
        return device_token

# Enhanced endpoint to add to devices.py router
async def register_device_enhanced(
    request: EnhancedDeviceRegistrationRequest,
    db: AsyncSession = Depends(get_db)
) -> EnhancedDeviceRegistrationResponse:
    """
    Enhanced device registration with automatic profile recovery
    
    This endpoint:
    1. Uses stable device identifiers (vendor ID preferred)
    2. Attempts automatic profile recovery using provided hints
    3. Pre-populates recovery information for future use
    4. Provides guidance for next steps based on user status
    """
    try:
        registration_service = EnhancedDeviceRegistration(db)
        return await registration_service.register_or_recover_device(request)
        
    except Exception as e:
        logger.error(f"Enhanced device registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Device registration failed"
        )

# Usage example for client applications:
"""
iOS Swift Example:

// Generate stable device ID using vendor identifier
let vendorID = UIDevice.current.identifierForVendor?.uuidString

// Prepare registration request
let registrationRequest = [
    "device_token": deviceToken,
    "vendor_identifier": vendorID,
    "device_info": [
        "device_model": UIDevice.current.model,
        "os_version": UIDevice.current.systemVersion,
        "timezone": TimeZone.current.identifier,
        "screen_resolution": "\(Int(UIScreen.main.bounds.width))x\(Int(UIScreen.main.bounds.height))"
    ],
    "recovery_email": userEmail, // If available from previous session
    "recovery_phone": userPhone, // If available from previous session
    "existing_profile_hint": [ // If user indicates they had an account
        "email": userProvidedEmail,
        "phone": userProvidedPhone
    ]
]

// Call enhanced registration endpoint
let response = await apiClient.post("/api/v1/devices/register-enhanced", data: registrationRequest)

if response.profile_recovered {
    // Show "Welcome back!" message
    // Skip onboarding, go to main app
} else if response.is_returning_user {
    // Show profile completion prompt
} else {
    // Show full onboarding flow
}
"""