"""
Device-based minimal registration for iOS app
Ultra-simple: device_token + keywords only
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
import logging
import json
import hashlib
from datetime import datetime

from app.core.database import db_manager
from app.utils.validation import validate_device_token, validate_keywords
from app.services.privacy_analytics_service import privacy_analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register")
async def register_device_minimal(request: Dict[str, Any]):
    """
    Ultra-minimal device registration
    Only requires: device_token + keywords
    """
    try:
        # Validate inputs
        device_token = request.get("device_token")
        keywords = request.get("keywords", [])
        
        if not device_token:
            raise HTTPException(status_code=400, detail="device_token is required")
        
        # Validate device token (64 hex chars)
        try:
            device_token = validate_device_token(device_token)
            keywords = validate_keywords(keywords)
        except HTTPException as e:
            # Log validation failures to distinguish between legitimate errors and security probes
            if "repeating patterns" in str(e.detail) or len(device_token) > 200:
                logger.warning(f"Security probe in device registration: token_length={len(device_token)}, unique_chars={len(set(device_token)) if device_token else 0}")
            else:
                logger.info(f"Legitimate validation error in device registration: {e.detail}")
            raise
        
        # Single INSERT - device becomes user
        insert_query = """
            INSERT INTO iosapp.device_users (device_token, keywords, notifications_enabled)
            VALUES ($1, $2, true)
            ON CONFLICT (device_token) 
            DO UPDATE SET 
                keywords = EXCLUDED.keywords,
                notifications_enabled = true
            RETURNING id, created_at
        """
        
        result = await db_manager.execute_query(
            insert_query, 
            device_token, 
            json.dumps(keywords)
        )
        
        if not result:
            raise Exception("Failed to register device")
        
        device_id = result[0]['id']
        created_at = result[0]['created_at']
        
        # Create user profile if it doesn't exist (using device_id as foreign key)
        user_profile_query = """
            INSERT INTO iosapp.users (
                device_id, 
                job_matches_enabled,
                application_reminders_enabled,
                weekly_digest_enabled,
                market_insights_enabled,
                created_at,
                updated_at
            )
            VALUES ($1, true, true, true, true, NOW(), NOW())
            ON CONFLICT (device_id) 
            DO UPDATE SET 
                job_matches_enabled = EXCLUDED.job_matches_enabled,
                updated_at = NOW()
            RETURNING id
        """
        
        user_result = await db_manager.execute_query(
            user_profile_query,
            device_id
        )
        
        if user_result:
            logger.info(f"User profile created/updated for device {device_id}")
        
        # Record analytics (with consent check)
        await privacy_analytics_service.track_action_with_consent(
            str(device_id), 
            'registration', 
            {
                "keywords_count": len(keywords),
                "keywords": keywords[:5],  # First 5 keywords for analytics
                "registration_method": "minimal"
            }
        )
        
        return {
            "success": True,
            "data": {
                "device_id": str(device_id),
                "device_token_preview": device_token[:16] + "...",
                "keywords_count": len(keywords),
                "notifications_enabled": True,
                "registered_at": created_at.isoformat(),
                "message": "Device registered successfully - ready for job notifications!"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in minimal device registration: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.put("/keywords")
async def update_keywords(request: Dict[str, Any]):
    """Update keywords for existing device"""
    try:
        device_token = request.get("device_token")
        keywords = request.get("keywords", [])
        
        if not device_token:
            raise HTTPException(status_code=400, detail="device_token is required")
        
        device_token = validate_device_token(device_token)
        keywords = validate_keywords(keywords)
        
        # Update keywords
        update_query = """
            UPDATE iosapp.device_users 
            SET keywords = $1
            WHERE device_token = $2
            RETURNING id
        """
        
        result = await db_manager.execute_query(update_query, json.dumps(keywords), device_token)
        
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = result[0]['id']
        
        # Record analytics (with consent check)
        await privacy_analytics_service.track_action_with_consent(
            str(device_id), 
            'keywords_update', 
            {
                "keywords_count": len(keywords),
                "new_keywords": keywords[:5]
            }
        )
        
        return {
            "success": True,
            "message": "Keywords updated successfully",
            "keywords_count": len(keywords)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating keywords: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update keywords: {str(e)}")

@router.get("/status/{device_token}")
async def get_device_status(device_token: str):
    """Get device registration status"""
    try:
        device_token = validate_device_token(device_token)
        
        query = """
            SELECT id, keywords, notifications_enabled, created_at
            FROM iosapp.device_users
            WHERE device_token = $1
        """
        
        result = await db_manager.execute_query(query, device_token)
        
        if not result:
            return {
                "registered": False,
                "message": "Device not found - registration required"
            }
        
        device_data = result[0]
        keywords = json.loads(device_data['keywords']) if device_data['keywords'] else []
        
        return {
            "registered": True,
            "device_id": str(device_data['id']),
            "keywords_count": len(keywords),
            "keywords": keywords,
            "notifications_enabled": device_data['notifications_enabled'],
            "has_keywords": len(keywords) > 0,
            "setup_complete": len(keywords) > 0,
            "requires_onboarding": len(keywords) == 0,
            "registered_at": device_data['created_at'].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device status: {str(e)}")

@router.post("/analytics/track")
async def track_user_action(request: Dict[str, Any]):
    """Track user actions for analytics"""
    try:
        device_token = request.get("device_token")
        action = request.get("action")
        metadata = request.get("metadata", {})
        
        if not device_token or not action:
            raise HTTPException(status_code=400, detail="device_token and action are required")
        
        device_token = validate_device_token(device_token)
        
        # Get device_id
        device_query = "SELECT id FROM iosapp.device_users WHERE device_token = $1"
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Track action (with consent check)
        await privacy_analytics_service.track_action_with_consent(
            str(device_id), 
            action, 
            metadata
        )
        
        return {
            "success": True,
            "message": f"Action '{action}' tracked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking action: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track action: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary():
    """Get basic analytics summary"""
    try:
        summary = await db_manager.execute_query("SELECT * FROM iosapp.analytics_summary")
        keywords = await db_manager.execute_query("SELECT * FROM iosapp.popular_keywords LIMIT 10")
        
        return {
            "success": True,
            "data": {
                "summary": dict(summary[0]) if summary else {},
                "top_keywords": [dict(k) for k in keywords]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.delete("/device/{device_token}")
async def delete_device(device_token: str):
    """Delete device and all associated data (GDPR compliance)"""
    try:
        device_token = validate_device_token(device_token)
        
        # Delete device (CASCADE will handle related records)
        delete_query = """
            DELETE FROM iosapp.device_users 
            WHERE device_token = $1 
            RETURNING id
        """
        
        result = await db_manager.execute_query(delete_query, device_token)
        
        if not result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        return {
            "success": True,
            "message": "Device and all associated data deleted successfully",
            "deleted_device_id": str(result[0]['id'])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete device: {str(e)}")