"""
Profile Recovery API Endpoints
Handles user profile recovery after app reinstall or device changes
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timezone
import hashlib
import json

from app.core.database import get_db
from app.models.user import User
from app.models.device import DeviceToken
from app.schemas.profile_recovery import (
    ProfileRecoveryRequest,
    ProfileRecoveryResponse,
    DeviceLinkRequest,
    ProfileMergeRequest,
    RecoveryMethodResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

class ProfileRecoveryService:
    """Service for handling profile recovery operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_device_fingerprint(self, device_info: Dict[str, Any]) -> str:
        """Generate a stable device fingerprint from device info"""
        # Create fingerprint from stable device characteristics
        fingerprint_data = {
            "model": device_info.get("device_model", ""),
            "os_version": device_info.get("os_version", "").split(".")[0],  # Major version only
            "screen_resolution": device_info.get("screen_resolution", ""),
            "timezone": device_info.get("timezone", ""),
            "locale": device_info.get("locale", "")
        }
        
        # Sort keys for consistent hashing
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]
    
    async def find_user_by_email(self, email: str) -> Optional[User]:
        """Find user by email address"""
        if not email:
            return None
            
        query = select(User).where(
            and_(
                User.email.ilike(email),
                User.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def find_user_by_phone(self, phone: str) -> Optional[User]:
        """Find user by phone number"""
        if not phone:
            return None
            
        # Normalize phone number (remove spaces, dashes, etc.)
        normalized_phone = ''.join(filter(str.isdigit, phone))
        
        query = select(User).where(
            and_(
                User.phone.like(f"%{normalized_phone}%"),
                User.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def find_user_by_device_fingerprint(self, fingerprint: str) -> Optional[User]:
        """Find user by device fingerprint"""
        # Look for users with similar device characteristics
        query = select(User).join(DeviceToken).where(
            DeviceToken.device_info.op("->>")(f'fingerprint') == fingerprint
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def find_users_by_profile_similarity(
        self, 
        name: Optional[str] = None,
        linkedin: Optional[str] = None,
        skills: Optional[list] = None
    ) -> list[User]:
        """Find users by profile similarity for manual verification"""
        conditions = []
        
        if name:
            # Split name and search for parts
            name_parts = name.lower().split()
            for part in name_parts:
                conditions.append(
                    or_(
                        User.first_name.ilike(f"%{part}%"),
                        User.last_name.ilike(f"%{part}%")
                    )
                )
        
        if linkedin:
            conditions.append(User.linkedin_profile.ilike(f"%{linkedin}%"))
        
        if skills and len(skills) > 0:
            # Check for skill overlap in JSONB array
            for skill in skills[:3]:  # Limit to first 3 skills
                conditions.append(User.skills.op("@>")(f'["{skill}"]'))
        
        if not conditions:
            return []
        
        query = select(User).where(
            and_(
                User.is_active == True,
                or_(*conditions)
            )
        ).limit(5)  # Limit potential matches
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_device_id(self, user: User, new_device_id: str) -> bool:
        """Update user's device_id to new value"""
        try:
            # Check if new device_id is already taken
            existing_query = select(User).where(User.device_id == new_device_id)
            existing_result = await self.db.execute(existing_query)
            existing_user = existing_result.scalar_one_or_none()
            
            if existing_user and existing_user.id != user.id:
                # Device ID conflict - need to merge or handle specially
                logger.warning(f"Device ID conflict: {new_device_id} already exists for user {existing_user.id}")
                return False
            
            # Update device_id
            user.device_id = new_device_id
            user.updated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device_id: {str(e)}")
            await self.db.rollback()
            return False

@router.post("/profile/check-recovery-options", response_model=RecoveryMethodResponse)
async def check_recovery_options(
    request: ProfileRecoveryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Check available recovery options for a user
    Returns possible recovery methods without actually performing recovery
    """
    try:
        service = ProfileRecoveryService(db)
        recovery_options = []
        
        # Check email recovery
        if request.email:
            user = await service.find_user_by_email(request.email)
            if user:
                recovery_options.append({
                    "method": "email",
                    "available": True,
                    "confidence": "high",
                    "profile_preview": {
                        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                        "email": user.email,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "profile_completeness": user.profile_completeness or 0
                    }
                })
        
        # Check phone recovery
        if request.phone:
            user = await service.find_user_by_phone(request.phone)
            if user:
                recovery_options.append({
                    "method": "phone",
                    "available": True,
                    "confidence": "high",
                    "profile_preview": {
                        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                        "phone": user.phone,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "profile_completeness": user.profile_completeness or 0
                    }
                })
        
        # Check device fingerprint recovery
        if request.device_info:
            fingerprint = await service.generate_device_fingerprint(request.device_info)
            user = await service.find_user_by_device_fingerprint(fingerprint)
            if user:
                recovery_options.append({
                    "method": "device_fingerprint",
                    "available": True,
                    "confidence": "medium",
                    "profile_preview": {
                        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                        "last_seen": user.updated_at.isoformat() if user.updated_at else None,
                        "profile_completeness": user.profile_completeness or 0
                    }
                })
        
        # Check profile similarity
        if request.first_name or request.last_name or request.linkedin_profile:
            full_name = f"{request.first_name or ''} {request.last_name or ''}".strip()
            similar_users = await service.find_users_by_profile_similarity(
                name=full_name,
                linkedin=request.linkedin_profile,
                skills=request.skills
            )
            
            for user in similar_users:
                recovery_options.append({
                    "method": "profile_similarity",
                    "available": True,
                    "confidence": "low",
                    "profile_preview": {
                        "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                        "email": user.email if user.email else None,
                        "linkedin": user.linkedin_profile if user.linkedin_profile else None,
                        "profile_completeness": user.profile_completeness or 0
                    }
                })
        
        return RecoveryMethodResponse(
            device_id=request.new_device_id,
            recovery_options=recovery_options,
            total_options=len(recovery_options),
            recommendation="email" if any(opt["method"] == "email" for opt in recovery_options) else 
                         ("phone" if any(opt["method"] == "phone" for opt in recovery_options) else 
                          ("device_fingerprint" if any(opt["method"] == "device_fingerprint" for opt in recovery_options) else 
                           "manual_support"))
        )
        
    except Exception as e:
        logger.error(f"Error checking recovery options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check recovery options"
        )

@router.post("/profile/recover", response_model=ProfileRecoveryResponse)
async def recover_profile(
    request: ProfileRecoveryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Attempt to recover user profile using provided information
    Updates device_id to link existing profile to new device
    """
    try:
        service = ProfileRecoveryService(db)
        recovered_user = None
        recovery_method = None
        
        # Try email recovery first (highest confidence)
        if request.email and not recovered_user:
            user = await service.find_user_by_email(request.email)
            if user:
                recovered_user = user
                recovery_method = "email"
        
        # Try phone recovery
        if request.phone and not recovered_user:
            user = await service.find_user_by_phone(request.phone)
            if user:
                recovered_user = user
                recovery_method = "phone"
        
        # Try device fingerprint recovery
        if request.device_info and not recovered_user:
            fingerprint = await service.generate_device_fingerprint(request.device_info)
            user = await service.find_user_by_device_fingerprint(fingerprint)
            if user:
                recovered_user = user
                recovery_method = "device_fingerprint"
        
        if not recovered_user:
            return ProfileRecoveryResponse(
                success=False,
                message="No matching profile found. Consider creating a new profile or contact support.",
                recovery_method=None,
                user_profile=None
            )
        
        # Update device_id for recovered user
        success = await service.update_device_id(recovered_user, request.new_device_id)
        
        if not success:
            return ProfileRecoveryResponse(
                success=False,
                message="Profile found but could not update device link. Contact support for manual recovery.",
                recovery_method=recovery_method,
                user_profile=None
            )
        
        # Return successful recovery
        return ProfileRecoveryResponse(
            success=True,
            message=f"Profile successfully recovered using {recovery_method}",
            recovery_method=recovery_method,
            user_profile={
                "user_id": str(recovered_user.id),
                "device_id": recovered_user.device_id,
                "name": f"{recovered_user.first_name or ''} {recovered_user.last_name or ''}".strip(),
                "email": recovered_user.email,
                "phone": recovered_user.phone,
                "profile_completeness": recovered_user.profile_completeness or 0,
                "created_at": recovered_user.created_at.isoformat() if recovered_user.created_at else None,
                "last_updated": recovered_user.updated_at.isoformat() if recovered_user.updated_at else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error during profile recovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile recovery failed due to internal error"
        )

@router.post("/profile/link-device", response_model=ProfileRecoveryResponse)
async def link_device_to_profile(
    request: DeviceLinkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually link a new device to an existing user profile
    Requires user_id and new device_id for explicit linking
    """
    try:
        # Find user by user_id
        query = select(User).where(
            and_(
                User.id == request.user_id,
                User.is_active == True
            )
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        service = ProfileRecoveryService(db)
        success = await service.update_device_id(user, request.new_device_id)
        
        if not success:
            return ProfileRecoveryResponse(
                success=False,
                message="Could not link device to profile. Device ID may already be in use.",
                recovery_method="manual_link",
                user_profile=None
            )
        
        return ProfileRecoveryResponse(
            success=True,
            message="Device successfully linked to profile",
            recovery_method="manual_link",
            user_profile={
                "user_id": str(user.id),
                "device_id": user.device_id,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                "email": user.email,
                "phone": user.phone,
                "profile_completeness": user.profile_completeness or 0,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_updated": user.updated_at.isoformat() if user.updated_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking device to profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link device to profile"
        )

@router.get("/profile/recovery-history/{user_id}")
async def get_recovery_history(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get recovery history for a user (for debugging/support)
    """
    try:
        # This would require a recovery_history table to be implemented
        # For now, return basic user information
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get associated device tokens
        device_query = select(DeviceToken).where(DeviceToken.user_id == user.id)
        device_result = await db.execute(device_query)
        devices = device_result.scalars().all()
        
        return {
            "user_id": str(user.id),
            "device_id": user.device_id,
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_updated": user.updated_at.isoformat() if user.updated_at else None,
            "associated_devices": [
                {
                    "device_token": device.device_token[:20] + "..." if device.device_token else None,
                    "device_info": device.device_info,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                    "is_active": device.is_active
                }
                for device in devices
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recovery history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recovery history"
        )