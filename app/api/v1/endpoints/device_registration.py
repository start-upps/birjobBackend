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

async def update_user_activity(device_token: str):
    """Update last_activity timestamp for a device"""
    try:
        await db_manager.execute_command(
            "UPDATE iosapp.device_users SET last_activity = NOW() WHERE device_token = $1",
            device_token
        )
    except Exception as e:
        logger.warning(f"Failed to update last activity for device {device_token[:8]}...: {e}")

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
        
        # Single INSERT - device becomes user with last_activity tracking
        insert_query = """
            INSERT INTO iosapp.device_users (device_token, keywords, notifications_enabled, last_activity)
            VALUES ($1, $2, true, NOW())
            ON CONFLICT (device_token) 
            DO UPDATE SET 
                keywords = EXCLUDED.keywords,
                notifications_enabled = true,
                last_activity = NOW()
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
        
        # Update keywords and last_activity
        update_query = """
            UPDATE iosapp.device_users 
            SET keywords = $1, last_activity = NOW()
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
            SELECT id, keywords, notifications_enabled, created_at, last_activity
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
            "registered_at": device_data['created_at'].isoformat(),
            "last_activity": device_data['last_activity'].isoformat() if device_data.get('last_activity') else None
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

@router.get("/users-activity")
async def get_users_activity():
    """Get all users with their last activity for admin tracking"""
    try:
        query = """
            SELECT 
                SUBSTRING(device_token, 1, 8) || '...' as device_preview,
                id as device_id,
                JSON_ARRAY_LENGTH(keywords::json) as keywords_count,
                notifications_enabled,
                created_at,
                last_activity,
                CASE 
                    WHEN last_activity IS NULL THEN 'Never active'
                    WHEN last_activity > NOW() - INTERVAL '1 day' THEN 'Active today'
                    WHEN last_activity > NOW() - INTERVAL '7 days' THEN 'Active this week'
                    WHEN last_activity > NOW() - INTERVAL '30 days' THEN 'Active this month'
                    ELSE 'Inactive > 30 days'
                END as activity_status,
                EXTRACT(EPOCH FROM (NOW() - last_activity))/86400 as days_since_activity
            FROM iosapp.device_users
            ORDER BY last_activity DESC NULLS LAST, created_at DESC
        """
        
        result = await db_manager.execute_query(query)
        
        # Calculate activity summary
        activity_summary = {
            "total_users": len(result),
            "never_active": 0,
            "active_today": 0,
            "active_this_week": 0,
            "active_this_month": 0,
            "inactive_30_plus": 0
        }
        
        users_data = []
        for row in result:
            activity_status = row['activity_status']
            if activity_status == 'Never active':
                activity_summary["never_active"] += 1
            elif activity_status == 'Active today':
                activity_summary["active_today"] += 1
            elif activity_status == 'Active this week':
                activity_summary["active_this_week"] += 1
            elif activity_status == 'Active this month':
                activity_summary["active_this_month"] += 1
            else:
                activity_summary["inactive_30_plus"] += 1
            
            users_data.append({
                "device_preview": row['device_preview'],
                "device_id": str(row['device_id']),
                "keywords_count": row['keywords_count'] or 0,
                "notifications_enabled": row['notifications_enabled'],
                "registered_at": row['created_at'].isoformat(),
                "last_activity": row['last_activity'].isoformat() if row['last_activity'] else None,
                "activity_status": activity_status,
                "days_since_activity": round(row['days_since_activity'], 1) if row['days_since_activity'] else None
            })
        
        return {
            "success": True,
            "activity_summary": activity_summary,
            "users": users_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting users activity: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users activity: {str(e)}")