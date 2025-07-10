from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import uuid
import logging
import re

from app.core.database import get_db
from app.models.device import DeviceToken
from app.schemas.device import DeviceRegisterRequest, DeviceRegisterResponse, APIResponse
from app.core.redis_client import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

def validate_device_token(token: str) -> bool:
    """Validate that device token is a valid APNs token format"""
    if not token:
        return False
    
    # Check for obvious placeholder patterns first
    placeholder_indicators = [
        'placeholder', 'test', 'fake', 'dummy', 'simulator',
        'B6BDBB52', '0B43E135', 'ABCDEF', 'abcdef',
        '1C1108D7', 'B71F57C9', 'xxxx', '____', '----', 'chars_min'
    ]
    
    token_lower = token.lower()
    for indicator in placeholder_indicators:
        if indicator.lower() in token_lower:
            return False
    
    # Remove any spaces, hyphens, underscores
    clean_token = token.replace(" ", "").replace("-", "").replace("_", "")
    
    # APNs tokens can be 64 hex characters (32 bytes) or 160 hex characters (80 bytes)
    # Some iOS configurations generate longer tokens
    if len(clean_token) not in [64, 160]:
        return False
    
    # Check if it's all hex characters
    if not re.match(r'^[0-9a-fA-F]+$', clean_token):
        return False
    
    # Check for common placeholder patterns
    placeholder_patterns = [
        r'^0+$',  # All zeros
        r'^1+$',  # All ones
        r'^[fF]+$',  # All Fs
        r'^(123456)+',  # Repeating 123456
        r'^(abcdef)+',  # Repeating abcdef
        r'^(fedcba)+',  # Repeating fedcba
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, clean_token):
            return False
    
    return True

@router.post("/token", response_model=DeviceRegisterResponse)
async def register_push_token(
    request: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register or update push token for device"""
    try:
        # Validate device token format
        logger.info(f"Validating device token: {request.device_token}")
        if not validate_device_token(request.device_token):
            logger.warning(f"Invalid device token rejected: {request.device_token}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid device token format. Please ensure you're using a real APNs token from your iOS device."
            )
        logger.info(f"Device token validation passed: {request.device_token}")
        # Extract stable device identifier from device_info
        device_id_value = None
        device_info_dict = request.device_info.model_dump()
        
        # Log what we received to debug device_id issue
        logger.info(f"Device info received: {device_info_dict}")
        
        # Try to get a stable device identifier from device_info
        if 'device_id' in device_info_dict:
            device_id_value = device_info_dict['device_id']
        elif 'deviceId' in device_info_dict:
            device_id_value = device_info_dict['deviceId']
        elif 'identifier' in device_info_dict:
            device_id_value = device_info_dict['identifier']
        elif 'uuid' in device_info_dict:
            device_id_value = device_info_dict['uuid']
        
        logger.info(f"Extracted device_id: {device_id_value}")
        
        # If no stable device_id provided, check if we can link to existing user profile first
        if not device_id_value:
            # WORKAROUND: Try to find existing user profile without device token
            # This handles the case where iOS app doesn't send device_id in device_info
            from app.models.user import User
            
            # Get email from device info if provided
            email = None
            if hasattr(request.device_info, 'email') and request.device_info.email:
                email = request.device_info.email
            elif isinstance(request.device_info.model_dump(), dict):
                email = request.device_info.model_dump().get('email')
            
            # Try to find user profile that exists but has no device token
            existing_user = None
            from app.core.database import db_manager
            
            # First try by email if provided
            if email:
                user_without_token_query = """
                    SELECT u.id, ud.device_id FROM iosapp.users u
                    JOIN iosapp.user_devices ud ON u.id = ud.user_id
                    LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                    WHERE u.email = $1 AND dt.id IS NULL AND ud.is_active = true
                    LIMIT 1
                """
                result = await db_manager.execute_query(user_without_token_query, email)
                if result:
                    existing_user = {'id': result[0]['id'], 'device_id': result[0]['device_id']}
                    logger.info(f"Found existing user profile without device token by email: {existing_user}")
            
            # If no email match, try to find any user with keywords but no device token
            # This handles the case where user created profile but iOS doesn't send email
            if not existing_user:
                any_user_without_token_query = """
                    SELECT u.id, ud.device_id FROM iosapp.users u
                    JOIN iosapp.user_devices ud ON u.id = ud.user_id
                    LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                    WHERE dt.id IS NULL AND ud.is_active = true
                        AND u.keywords IS NOT NULL 
                        AND jsonb_array_length(u.keywords) > 0
                    ORDER BY u.created_at DESC
                    LIMIT 1
                """
                result = await db_manager.execute_query(any_user_without_token_query)
                if result:
                    existing_user = {'id': result[0]['id'], 'device_id': result[0]['device_id']}
                    logger.info(f"Found existing user profile without device token by keywords: {existing_user}")
            
            if existing_user:
                # Link this device token to the existing user profile
                device_id_value = existing_user['device_id']
                logger.info(f"Linking device token to existing profile with device_id: {device_id_value}")
            else:
                # Fall back to generating device_id as before
                import hashlib
                device_model = device_info_dict.get('deviceModel', 'unknown')
                timezone = device_info_dict.get('timezone', 'unknown') 
                os_version = device_info_dict.get('os_version', 'unknown')
                # Create a stable identifier without using token (which can change)
                stable_id = f"{device_model}_{timezone}_{os_version}"
                device_id_value = hashlib.md5(stable_id.encode()).hexdigest()
                logger.info(f"Generated stable device ID: {device_id_value} from {stable_id}")
            
        # Find existing device by device_id first (this should be unique per device)
        device_stmt = select(DeviceToken).where(DeviceToken.device_id == device_id_value)
        device_result = await db.execute(device_stmt)
        existing_device = device_result.scalar_one_or_none()
        
        if existing_device:
            # Update existing device token and device info
            existing_device.device_token = request.device_token
            existing_device.device_info = request.device_info.model_dump()
            existing_device.is_active = True
            
            # Get email from device info if provided
            email = None
            if hasattr(request.device_info, 'email') and request.device_info.email:
                email = request.device_info.email
            elif isinstance(request.device_info.model_dump(), dict):
                email = request.device_info.model_dump().get('email')
            
            # Update user email if provided and not already set
            if email and existing_device.user_id:
                from app.models.user import User
                user_stmt = select(User).where(User.id == existing_device.user_id)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                if user and not user.email:
                    user.email = email
                    logger.info(f"Updated user email for device: {device_id_value}")
            
            await db.commit()
            await db.refresh(existing_device)
            
            logger.info(f"Updated push token for existing device: {device_id_value}")
            
            return DeviceRegisterResponse(
                data={
                    "device_id": existing_device.device_id,
                    "user_id": str(existing_device.user_id),
                    "message": "Push token updated successfully"
                }
            )
        else:
            # Create new device and link to existing user if possible
            from app.models.user import User
            
            # Get email from device info if provided
            email = None
            if hasattr(request.device_info, 'email') and request.device_info.email:
                email = request.device_info.email
            elif isinstance(request.device_info.model_dump(), dict):
                email = request.device_info.model_dump().get('email')
            
            # Try to find existing user by email first
            user = None
            if email:
                user_stmt = select(User).where(User.email == email)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                logger.info(f"Found existing user by email {email}: {user.id if user else 'None'}")
            
            # Special case: If we're using an existing profile's device_id, find that user
            if not user:
                # Check if this device_id belongs to an existing user profile
                from app.core.database import db_manager
                profile_check_query = """
                    SELECT u.id FROM iosapp.users u
                    JOIN iosapp.user_devices ud ON u.id = ud.user_id
                    WHERE ud.device_id = $1 AND ud.is_active = true
                """
                profile_result = await db_manager.execute_query(profile_check_query, device_id_value)
                if profile_result:
                    user_stmt = select(User).where(User.id == profile_result[0]['id'])
                    user_result = await db.execute(user_stmt)
                    user = user_result.scalar_one_or_none()
                    logger.info(f"Found existing user profile for device_id {device_id_value}: {user.id if user else 'None'}")
            
            # Create new user only if no existing user found
            if not user:
                user = User(email=email if email else None)
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"Created new user with email: {email}")
            else:
                logger.info(f"Linking device to existing user: {user.id}")
            
            # Create new device
            device = DeviceToken(
                user_id=user.id,
                device_id=device_id_value,
                device_token=request.device_token,
                device_info=request.device_info.model_dump()
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
            
            logger.info(f"New device and user created for device: {device_id_value}")
            
            return DeviceRegisterResponse(
                data={
                    "device_id": device.device_id,
                    "user_id": str(user.id),
                    "message": "Push token registered successfully"
                }
            )
            
    except Exception as e:
        logger.error(f"Error registering push token: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register push token: {str(e)}"
        )

@router.post("/register", response_model=DeviceRegisterResponse)
async def register_device(
    request: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new iOS device for push notifications"""
    try:
        # Validate device token format
        logger.info(f"Validating device token: {request.device_token}")
        if not validate_device_token(request.device_token):
            logger.warning(f"Invalid device token rejected: {request.device_token}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid device token format. Please ensure you're using a real APNs token from your iOS device."
            )
        logger.info(f"Device token validation passed: {request.device_token}")
        from app.models.user import User  # Import here to avoid circular imports
        
        # Extract device_id from device_info - this should be a stable device identifier
        device_id_value = None
        device_info_dict = request.device_info.model_dump()
        
        # Log what we received to debug device_id issue
        logger.info(f"Device info received: {device_info_dict}")
        
        # Try to get a stable device identifier from device_info
        if 'device_id' in device_info_dict:
            device_id_value = device_info_dict['device_id']
        elif 'deviceId' in device_info_dict:
            device_id_value = device_info_dict['deviceId']
        elif 'identifier' in device_info_dict:
            device_id_value = device_info_dict['identifier']
        elif 'uuid' in device_info_dict:
            device_id_value = device_info_dict['uuid']
        
        logger.info(f"Extracted device_id: {device_id_value}")
        
        # If no stable device_id provided, check if we can link to existing user profile first
        if not device_id_value:
            # WORKAROUND: Try to find existing user profile without device token
            # This handles the case where iOS app doesn't send device_id in device_info
            
            # Get email from device info if provided
            email = None
            if hasattr(request.device_info, 'email') and request.device_info.email:
                email = request.device_info.email
            elif isinstance(request.device_info.model_dump(), dict):
                email = request.device_info.model_dump().get('email')
            
            # Try to find user profile that exists but has no device token
            existing_user = None
            if email:
                # Look for user with email but no device token using db_manager
                from app.core.database import db_manager
                user_without_token_query = """
                    SELECT u.id, ud.device_id FROM iosapp.users u
                    JOIN iosapp.user_devices ud ON u.id = ud.user_id
                    LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                    WHERE u.email = $1 AND dt.id IS NULL AND ud.is_active = true
                    LIMIT 1
                """
                result = await db_manager.execute_query(user_without_token_query, email)
                if result:
                    existing_user = {'id': result[0]['id'], 'device_id': result[0]['device_id']}
                    logger.info(f"Found existing user profile without device token: {existing_user}")
            
            if existing_user:
                # Link this device token to the existing user profile
                device_id_value = existing_user['device_id']
                logger.info(f"Linking device token to existing profile with device_id: {device_id_value}")
            else:
                # Fall back to generating device_id as before
                import hashlib
                device_model = device_info_dict.get('deviceModel', 'unknown')
                timezone = device_info_dict.get('timezone', 'unknown')
                # Create a more stable identifier
                stable_id = f"{device_model}_{timezone}_{request.device_token[:16]}"
                device_id_value = hashlib.md5(stable_id.encode()).hexdigest()
            
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
            # First check if there's an existing user with email (if provided)
            email = None
            if hasattr(request.device_info, 'email') and request.device_info.email:
                email = request.device_info.email
            elif isinstance(request.device_info.model_dump(), dict):
                email = request.device_info.model_dump().get('email')
            
            if email:
                # Look for existing user by email
                user_stmt = select(User).where(User.email == email)
                user_result = await db.execute(user_stmt)
                user = user_result.scalar_one_or_none()
            
            if not user:
                # Create a basic user profile for device registration
                user = User(email=email if email else None)
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"Created new user for device registration: {user.id}")
        
        # Check if device already exists by device_id
        device_stmt = select(DeviceToken).where(DeviceToken.device_id == device_id_value)
        device_result = await db.execute(device_stmt)
        existing_device = device_result.scalar_one_or_none()
        
        if existing_device:
            # Update existing device
            existing_device.device_token = request.device_token  # Update token (it may change)
            existing_device.device_info = request.device_info.model_dump()
            existing_device.is_active = True
            existing_device.user_id = user.id  # Ensure user_id is set
            await db.commit()
            await db.refresh(existing_device)
            
            return DeviceRegisterResponse(
                data={
                    "device_id": existing_device.device_id,
                    "user_id": str(user.id),
                    "registered_at": existing_device.updated_at.isoformat(),
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