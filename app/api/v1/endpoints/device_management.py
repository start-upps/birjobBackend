"""
Device-based management endpoints (replaces user management)
Works with minimal schema - no email dependencies
All operations are device-token based
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
import json

from app.core.database import db_manager
from app.services.privacy_analytics_service import privacy_analytics_service
# from app.utils.validation import validate_device_token

def validate_device_token(device_token: str) -> str:
    """Simple device token validation"""
    if not device_token or len(device_token) < 16:
        raise HTTPException(status_code=400, detail="Invalid device token")
    return device_token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status/{device_token}")
async def get_device_status(device_token: str):
    """Get device registration and setup status"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT 
                id,
                keywords,
                notifications_enabled,
                created_at
            FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            return {
                "success": False,
                "registered": False,
                "message": "Device not found - registration required"
            }
        
        device_data = device_result[0]
        keywords = device_data['keywords'] or []
        
        # Check if setup is complete
        has_keywords = len(keywords) > 0
        setup_complete = has_keywords and device_data['notifications_enabled']
        
        return {
            "success": True,
            "registered": True,
            "setup_complete": setup_complete,
            "requires_onboarding": not setup_complete,
            "data": {
                "device_id": str(device_data['id']),
                "device_token_preview": device_token[:16] + "...",
                "keywords": keywords,
                "keywords_count": len(keywords),
                "notifications_enabled": device_data['notifications_enabled'],
                "registered_at": device_data['created_at'].isoformat() if device_data['created_at'] else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking device status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check device status")

@router.put("/update/{device_token}")
async def update_device(device_token: str, update_data: Dict[str, Any]):
    """Update device settings (keywords, notifications)"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Extract update fields
        keywords = update_data.get("keywords")
        notifications_enabled = update_data.get("notifications_enabled")
        
        # Build dynamic update query
        update_fields = []
        params = []
        param_count = 0
        
        if keywords is not None:
            param_count += 1
            update_fields.append(f"keywords = ${param_count}")
            params.append(json.dumps(keywords))
        
        if notifications_enabled is not None:
            param_count += 1
            update_fields.append(f"notifications_enabled = ${param_count}")
            params.append(notifications_enabled)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Always update timestamp
        update_fields.append("created_at = NOW()")
        
        # Add device_id parameter
        param_count += 1
        params.append(device_id)
        
        update_query = f"""
            UPDATE iosapp.device_users
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING keywords, notifications_enabled, created_at
        """
        
        result = await db_manager.execute_query(update_query, *params)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update device")
        
        updated_device = result[0]
        updated_keywords = updated_device['keywords'] or []
        
        # Log the update (with consent check)
        metadata = {
            "updated_fields": list(update_data.keys()),
            "keywords_count": len(updated_keywords),
            "notifications_enabled": updated_device['notifications_enabled'],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await privacy_analytics_service.track_action_with_consent(
            device_id,
            'device_updated',
            metadata
        )
        
        return {
            "success": True,
            "message": "Device updated successfully",
            "data": {
                "device_id": str(device_id),
                "device_token_preview": device_token[:16] + "...",
                "keywords": updated_keywords,
                "keywords_count": len(updated_keywords),
                "notifications_enabled": updated_device['notifications_enabled'],
                "updated_at": updated_device['created_at'].isoformat() if updated_device['created_at'] else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device: {e}")
        raise HTTPException(status_code=500, detail="Failed to update device")

@router.delete("/delete/{device_token}")
async def delete_device(device_token: str):
    """Delete device and all associated data"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info before deletion
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Count associated data before deletion
        counts_query = """
            SELECT 
                (SELECT COUNT(*) FROM iosapp.notification_hashes WHERE device_id = $1) as notifications,
                (SELECT COUNT(*) FROM iosapp.user_analytics WHERE device_id = $1) as analytics
        """
        counts_result = await db_manager.execute_query(counts_query, device_id)
        counts = counts_result[0] if counts_result else {"notifications": 0, "analytics": 0}
        
        # Delete device (CASCADE will handle related records)
        delete_query = """
            DELETE FROM iosapp.device_users
            WHERE id = $1
            RETURNING device_token
        """
        
        delete_result = await db_manager.execute_query(delete_query, device_id)
        
        if not delete_result:
            raise HTTPException(status_code=500, detail="Failed to delete device")
        
        return {
            "success": True,
            "message": "Device and all associated data deleted successfully",
            "data": {
                "device_id": str(device_id),
                "device_token_preview": device_token[:16] + "...",
                "deleted_records": {
                    "notifications": counts['notifications'],
                    "analytics": counts['analytics']
                },
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete device")

@router.get("/analytics/{device_token}")
async def get_device_analytics(device_token: str, days: int = 30):
    """Get analytics for a device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id, created_at, keywords FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        device_created = device_result[0]['created_at']
        keywords = device_result[0]['keywords'] or []
        
        # Get notification analytics
        notification_stats_query = """
            SELECT 
                COUNT(*) as total_notifications,
                COUNT(DISTINCT DATE(sent_at)) as active_days,
                COUNT(*) FILTER (WHERE sent_at >= NOW() - INTERVAL '%s days') as recent_notifications,
                array_agg(DISTINCT job_source) FILTER (WHERE job_source IS NOT NULL) as sources,
                MIN(sent_at) as first_notification,
                MAX(sent_at) as last_notification
            FROM iosapp.notification_hashes
            WHERE device_id = $1
        """ % days
        
        notification_stats = await db_manager.execute_query(notification_stats_query, device_id)
        stats = notification_stats[0] if notification_stats else {}
        
        # Get daily notification breakdown
        daily_stats_query = """
            SELECT 
                DATE(sent_at) as date,
                COUNT(*) as notification_count,
                array_agg(DISTINCT job_source) as sources
            FROM iosapp.notification_hashes
            WHERE device_id = $1 AND sent_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(sent_at)
            ORDER BY date DESC
        """ % days
        
        daily_stats = await db_manager.execute_query(daily_stats_query, device_id)
        
        # Get user analytics events (only if user has consented)
        events_stats = []
        analytics_consent = await privacy_analytics_service.check_analytics_consent(device_id)
        
        if analytics_consent:
            events_query = """
                SELECT 
                    action,
                    COUNT(*) as count,
                    MAX(created_at) as last_event
                FROM iosapp.user_analytics
                WHERE device_id = $1 AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY action
                ORDER BY count DESC
            """ % days
            
            events_stats = await db_manager.execute_query(events_query, device_id)
        
        # Calculate days since registration
        days_since_registration = 0
        if device_created:
            days_since_registration = (datetime.now(timezone.utc) - device_created.replace(tzinfo=timezone.utc)).days
        
        return {
            "success": True,
            "data": {
                "device_info": {
                    "device_id": str(device_id),
                    "device_token_preview": device_token[:16] + "...",
                    "keywords": keywords,
                    "keywords_count": len(keywords),
                    "registered_at": device_created.isoformat() if device_created else None,
                    "days_since_registration": days_since_registration
                },
                "notification_stats": {
                    "total_notifications": stats.get('total_notifications', 0),
                    "recent_notifications": stats.get('recent_notifications', 0),
                    "active_days": stats.get('active_days', 0),
                    "sources": stats.get('sources', []),
                    "first_notification": stats['first_notification'].isoformat() if stats.get('first_notification') else None,
                    "last_notification": stats['last_notification'].isoformat() if stats.get('last_notification') else None
                },
                "daily_breakdown": [
                    {
                        "date": day['date'].isoformat() if day['date'] else None,
                        "notification_count": day['notification_count'],
                        "sources": day['sources'] or []
                    }
                    for day in daily_stats
                ],
                "activity_events": [
                    {
                        "action": event['action'],
                        "count": event['count'],
                        "last_event": event['last_event'].isoformat() if event['last_event'] else None
                    }
                    for event in events_stats
                ],
                "privacy_note": "Activity events only shown if analytics consent is granted" if not analytics_consent else "Activity tracking active with user consent",
                "period_days": days
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device analytics")

@router.post("/refresh-token/{old_device_token}")
async def refresh_device_token(old_device_token: str, new_token_data: Dict[str, str]):
    """Refresh device token (for when iOS generates new token)"""
    try:
        # Validate old device token
        old_device_token = validate_device_token(old_device_token)
        new_device_token = validate_device_token(new_token_data.get("new_device_token", ""))
        
        # Check if old device exists
        old_device_query = """
            SELECT id, keywords, notifications_enabled FROM iosapp.device_users
            WHERE device_token = $1
        """
        old_device_result = await db_manager.execute_query(old_device_query, old_device_token)
        
        if not old_device_result:
            raise HTTPException(status_code=404, detail="Old device not found")
        
        old_device = old_device_result[0]
        
        # Check if new token already exists
        new_device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        new_device_result = await db_manager.execute_query(new_device_query, new_device_token)
        
        if new_device_result:
            raise HTTPException(status_code=409, detail="New device token already exists")
        
        # Update device token
        update_query = """
            UPDATE iosapp.device_users
            SET device_token = $1, created_at = NOW()
            WHERE id = $2
            RETURNING id
        """
        
        update_result = await db_manager.execute_query(update_query, new_device_token, old_device['id'])
        
        if not update_result:
            raise HTTPException(status_code=500, detail="Failed to update device token")
        
        # Log token refresh (with consent check)
        metadata = {
            "old_token_preview": old_device_token[:16] + "...",
            "new_token_preview": new_device_token[:16] + "...",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await privacy_analytics_service.track_action_with_consent(
            old_device['id'],
            'token_refreshed',
            metadata
        )
        
        return {
            "success": True,
            "message": "Device token refreshed successfully",
            "data": {
                "device_id": str(old_device['id']),
                "old_token_preview": old_device_token[:16] + "...",
                "new_token_preview": new_device_token[:16] + "...",
                "keywords": old_device['keywords'] or [],
                "notifications_enabled": old_device['notifications_enabled'],
                "refreshed_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing device token: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh device token")

@router.post("/cleanup/test-data")
async def cleanup_test_data():
    """Clean up test/dummy device tokens for development"""
    try:
        # Delete devices with obviously fake tokens
        cleanup_query = """
            DELETE FROM iosapp.device_users
            WHERE device_token LIKE '%aaaa%' 
            OR device_token LIKE '%0000%'
            OR device_token LIKE '%ffff%'
            OR LENGTH(device_token) < 32
            OR device_token ~ '^(.)\1+$'  -- Regex for repeating characters
            RETURNING device_token
        """
        
        deleted_devices = await db_manager.execute_query(cleanup_query)
        
        logger.info(f"Cleaned up {len(deleted_devices)} test device tokens")
        
        return {
            "success": True,
            "message": f"Cleaned up {len(deleted_devices)} test device tokens",
            "data": {
                "deleted_count": len(deleted_devices),
                "deleted_tokens": [token['device_token'][:16] + "..." for token in deleted_devices]
            }
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up test data: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean up test data")

@router.post("/reset-throttling/{device_token}")
async def reset_notification_throttling(device_token: str):
    """Reset notification throttling for a device (development only)"""
    try:
        from app.core.redis_client import redis_client
        
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = str(device_result[0]['id'])
        
        # Reset Redis counters
        await redis_client.reset_notification_count(device_id, "hour")
        await redis_client.reset_notification_count(device_id, "day")
        
        logger.info(f"Reset notification throttling for device {device_id}")
        
        return {
            "success": True,
            "message": "Notification throttling reset successfully",
            "data": {
                "device_id": device_id,
                "device_token_preview": device_token[:16] + "...",
                "reset_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting throttling: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset throttling")

@router.get("/debug/list-all")
async def debug_list_all_devices():
    """Debug endpoint: List all devices with full tokens (development only)"""
    try:
        query = """
            SELECT 
                id,
                device_token,
                keywords,
                notifications_enabled,
                created_at
            FROM iosapp.device_users
            ORDER BY created_at DESC
            LIMIT 10
        """
        
        devices = await db_manager.execute_query(query)
        
        result = []
        for device in devices:
            # Get notification count for this device
            notification_query = """
                SELECT COUNT(*) as count
                FROM iosapp.notification_hashes
                WHERE device_id = $1
            """
            notification_result = await db_manager.execute_query(notification_query, device['id'])
            notification_count = notification_result[0]['count'] if notification_result else 0
            
            result.append({
                "device_id": str(device['id']),
                "device_token": device['device_token'],  # Full token for debugging
                "device_token_length": len(device['device_token']),
                "keywords": device['keywords'],
                "notifications_enabled": device['notifications_enabled'],
                "notification_count": notification_count,
                "created_at": device['created_at'].isoformat() if device['created_at'] else None
            })
        
        return {
            "success": True,
            "message": "Debug device list (development only)",
            "data": {
                "devices": result,
                "total_devices": len(result)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in debug list: {e}")
        raise HTTPException(status_code=500, detail="Failed to list devices")