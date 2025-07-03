from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import uuid
import logging

from app.core.database import get_db
from app.models.device import DeviceToken
from app.schemas.device import DeviceRegisterRequest, DeviceRegisterResponse, APIResponse
from app.core.redis_client import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=DeviceRegisterResponse)
async def register_device(
    request: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new iOS device for push notifications"""
    try:
        from app.models.user import User  # Import here to avoid circular imports
        
        # Extract device_id from device_info if available, otherwise use device_token
        device_id_value = None
        if hasattr(request.device_info, 'device_id'):
            device_id_value = request.device_info.device_id
        elif isinstance(request.device_info.model_dump(), dict):
            device_id_value = request.device_info.model_dump().get('device_id')
        
        # If no device_id in device_info, use the device_token as device_id
        if not device_id_value:
            device_id_value = request.device_token
            
        # First, find or create user based on device_id (now in device_tokens table)
        device_stmt = select(DeviceToken).where(DeviceToken.device_id == device_id_value)
        device_result = await db.execute(device_stmt)
        existing_device = device_result.scalar_one_or_none()
        
        user = None
        if existing_device:
            # Get existing user
            user_stmt = select(User).where(User.id == existing_device.user_id)
            user_result = await db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
        
        if not user:
            # Create a basic user profile for device registration
            user = User()  # No device_id field in users table anymore
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created new user for device registration: {user.id}")
        
        # Check if device token already exists (different from device_id check above)
        token_stmt = select(DeviceToken).where(DeviceToken.device_token == request.device_token)
        token_result = await db.execute(token_stmt)
        existing_token_device = token_result.scalar_one_or_none()
        
        if existing_token_device:
            # Update existing device
            existing_token_device.device_info = request.device_info.model_dump()
            existing_token_device.is_active = True
            existing_token_device.user_id = user.id  # Ensure user_id is set
            existing_token_device.device_id = device_id_value  # Update device_id if needed
            await db.commit()
            await db.refresh(existing_token_device)
            
            return DeviceRegisterResponse(
                data={
                    "device_id": existing_token_device.device_id,
                    "user_id": str(user.id),
                    "registered_at": existing_token_device.updated_at.isoformat(),
                    "message": "Device updated successfully"
                }
            )
        else:
            # Create new device
            device = DeviceToken(
                user_id=user.id,  # Required field in new schema
                device_id=device_id_value,  # Store device_id for linking
                device_token=request.device_token,
                device_info=request.device_info.model_dump()
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
            
            logger.info(f"New device registered: {device.id} for user: {user.id}")
            
            return DeviceRegisterResponse(
                data={
                    "device_id": device.device_id,
                    "user_id": str(user.id),
                    "registered_at": device.registered_at.isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        logger.error(f"Device token: {request.device_token}")
        logger.error(f"Device info: {request.device_info}")
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        
        # Check if it's a connection error
        error_msg = str(e).lower()
        if "connection" in error_msg and ("closed" in error_msg or "lost" in error_msg):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection temporarily unavailable. Please try again."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register device: {str(e)}"
            )

@router.delete("/{device_id}", response_model=APIResponse)
async def unregister_device(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Unregister a device from push notifications"""
    try:
        # Try UUID format first, then fallback to device_id string lookup
        try:
            device_uuid = uuid.UUID(device_id)
            stmt = select(DeviceToken).where(DeviceToken.id == device_uuid)
        except ValueError:
            # Use device_id field instead of UUID
            stmt = select(DeviceToken).where(DeviceToken.device_id == device_id)
        
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        device.is_active = False
        await db.commit()
        
        # Clear cached data
        await redis_client.delete(f"device_keywords:{device_id}")
        
        logger.info(f"Device unregistered: {device_id}")
        
        return APIResponse(message="Device unregistered successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering device: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device"
        )

@router.get("/{device_id}/status", response_model=Dict[str, Any])
async def get_device_status(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get device registration status and basic info"""
    try:
        # Try UUID format first, then fallback to device_id string lookup
        try:
            device_uuid = uuid.UUID(device_id)
            stmt = select(DeviceToken).where(DeviceToken.id == device_uuid)
        except ValueError:
            # Use device_id field instead of UUID
            stmt = select(DeviceToken).where(DeviceToken.device_id == device_id)
        
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return {
            "success": True,
            "data": {
                "device_id": device.device_id,  # Return the string device_id, not UUID
                "uuid": str(device.id),  # Include UUID for reference
                "is_active": device.is_active,
                "registered_at": device.registered_at.isoformat(),
                "last_updated": device.updated_at.isoformat(),
                "device_info": device.device_info
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get device status"
        )