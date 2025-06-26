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
        # Check if device already exists
        stmt = select(DeviceToken).where(DeviceToken.device_token == request.device_token)
        result = await db.execute(stmt)
        existing_device = result.scalar_one_or_none()
        
        if existing_device:
            # Update existing device
            existing_device.device_info = request.device_info.model_dump()
            existing_device.is_active = True
            await db.commit()
            await db.refresh(existing_device)
            
            return DeviceRegisterResponse(
                data={
                    "device_id": str(existing_device.id),
                    "registered_at": existing_device.updated_at.isoformat(),
                    "message": "Device updated successfully"
                }
            )
        else:
            # Create new device
            device = DeviceToken(
                device_token=request.device_token,
                device_info=request.device_info.model_dump()
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
            
            logger.info(f"New device registered: {device.id}")
            
            return DeviceRegisterResponse(
                data={
                    "device_id": str(device.id),
                    "registered_at": device.created_at.isoformat()
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
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )
    
    try:
        # Find and deactivate device
        stmt = select(DeviceToken).where(DeviceToken.id == device_uuid)
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
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )
    
    try:
        stmt = select(DeviceToken).where(DeviceToken.id == device_uuid)
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
                "device_id": str(device.id),
                "is_active": device.is_active,
                "registered_at": device.created_at.isoformat(),
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
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