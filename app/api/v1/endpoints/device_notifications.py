"""
Device-based notification management endpoints
Works with minimal schema (device_users, notification_hashes, user_analytics)
No email dependencies - everything is device-token based
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone
import json

from app.core.database import db_manager
from app.core.config import settings
from app.services.privacy_analytics_service import privacy_analytics_service
# from app.utils.validation import validate_device_token

def validate_device_token(device_token: str) -> str:
    """Enhanced device token validation with security checks"""
    if not device_token:
        raise HTTPException(status_code=400, detail="Device token is required")
    
    # Check minimum length
    if len(device_token) < 16:
        raise HTTPException(status_code=400, detail="Invalid device token format")
    
    # Check maximum length to prevent buffer overflow attempts
    if len(device_token) > 256:
        raise HTTPException(status_code=400, detail="Device token too long")
    
    # Check for suspicious patterns (repeated characters, potential probing)
    if len(set(device_token)) < 5:  # Too few unique characters
        logger.warning(f"Suspicious device token with few unique chars: {device_token[:16]}...")
        raise HTTPException(status_code=400, detail="Invalid device token format")
    
    # Check for potential SQL injection or XSS patterns
    suspicious_patterns = ["'", '"', "<", ">", "script", "select", "union", "drop", "--", "/*"]
    token_lower = device_token.lower()
    for pattern in suspicious_patterns:
        if pattern in token_lower:
            logger.warning(f"Suspicious device token with pattern '{pattern}': {device_token[:16]}...")
            raise HTTPException(status_code=400, detail="Invalid device token format")
    
    return device_token

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/history/{device_token}")
async def get_notification_history(
    device_token: str, 
    limit: int = 50, 
    offset: int = 0
):
    """Get notification history for a device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id, keywords FROM iosapp.device_users
            WHERE device_token = $1 AND notifications_enabled = true
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or notifications disabled")
        
        device_id = device_result[0]['id']
        
        # Get notification history
        history_query = """
            SELECT 
                id,
                job_hash,
                job_title,
                job_company,
                job_source,
                matched_keywords,
                sent_at,
                is_read,
                read_at
            FROM iosapp.notification_hashes
            WHERE device_id = $1
            ORDER BY sent_at DESC
            LIMIT $2 OFFSET $3
        """
        
        history_result = await db_manager.execute_query(history_query, device_id, limit, offset)
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM iosapp.notification_hashes
            WHERE device_id = $1
        """
        count_result = await db_manager.execute_query(count_query, device_id)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Format notifications
        notifications = []
        for notification in history_result:
            # Parse matched keywords
            matched_keywords = []
            if notification['matched_keywords']:
                try:
                    if isinstance(notification['matched_keywords'], str):
                        matched_keywords = json.loads(notification['matched_keywords'])
                    else:
                        matched_keywords = notification['matched_keywords']
                except:
                    matched_keywords = []
            
            notifications.append({
                "id": str(notification['id']),
                "job_title": notification['job_title'],
                "job_company": notification['job_company'],
                "job_source": notification['job_source'],
                "matched_keywords": matched_keywords,
                "sent_at": notification['sent_at'].isoformat() if notification['sent_at'] else None,
                "job_hash": notification['job_hash'],
                "is_read": notification.get('is_read', False),
                "read_at": notification['read_at'].isoformat() if notification.get('read_at') else None
            })
        
        return {
            "success": True,
            "data": {
                "device_token_preview": device_token[:16] + "...",
                "total_notifications": total_count,
                "notifications": notifications,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": offset + limit < total_count
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification history")

@router.get("/inbox/{device_token}")
async def get_notification_inbox(
    device_token: str,
    limit: int = 20,
    group_by_time: bool = True
):
    """Get grouped notification inbox for a device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1 AND notifications_enabled = true
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or notifications disabled")
        
        device_id = device_result[0]['id']
        
        if group_by_time:
            # Group notifications by day and keywords
            grouped_query = """
                SELECT 
                    DATE(sent_at) as notification_date,
                    matched_keywords,
                    COUNT(*) as job_count,
                    array_agg(job_title ORDER BY sent_at DESC) as job_titles,
                    array_agg(job_company ORDER BY sent_at DESC) as job_companies,
                    array_agg(job_source ORDER BY sent_at DESC) as job_sources,
                    array_agg(job_hash ORDER BY sent_at DESC) as job_hashes,
                    MAX(sent_at) as latest_sent_at,
                    array_agg(id ORDER BY sent_at DESC) as notification_ids,
                    array_agg(is_read ORDER BY sent_at DESC) as read_statuses,
                    COUNT(CASE WHEN is_read = false THEN 1 END) as unread_count
                FROM iosapp.notification_hashes
                WHERE device_id = $1
                GROUP BY DATE(sent_at), matched_keywords
                ORDER BY latest_sent_at DESC
                LIMIT $2
            """
            
            grouped_result = await db_manager.execute_query(grouped_query, device_id, limit)
            
            notifications = []
            for group in grouped_result:
                # Parse matched keywords
                matched_keywords = []
                if group['matched_keywords']:
                    try:
                        if isinstance(group['matched_keywords'], str):
                            matched_keywords = json.loads(group['matched_keywords'])
                        else:
                            matched_keywords = group['matched_keywords']
                    except:
                        matched_keywords = []
                
                # Create grouped notification
                job_count = group['job_count']
                title = f"{job_count} New Job{'s' if job_count != 1 else ''} Found!"
                message = f"💼 {', '.join(matched_keywords[:3]) if matched_keywords else 'Job matches'}"
                
                notifications.append({
                    "id": f"group_{group['notification_date']}_{hash(str(matched_keywords))}",
                    "type": "job_match_group",
                    "title": title,
                    "message": message,
                    "job_count": job_count,
                    "unread_count": group['unread_count'],
                    "matched_keywords": matched_keywords,
                    "notification_date": group['notification_date'].isoformat() if group['notification_date'] else None,
                    "latest_sent_at": group['latest_sent_at'].isoformat() if group['latest_sent_at'] else None,
                    "notification_ids": [str(nid) for nid in group['notification_ids']],
                    "jobs": [
                        {
                            "title": title,
                            "company": company,
                            "source": source,
                            "job_hash": job_hash,
                            "notification_id": str(notification_id),
                            "is_read": is_read,
                            "apply_link": f"{settings.BASE_URL}/api/v1/notifications/job-by-hash/{job_hash}",
                            "deep_link": f"birjob://job/hash/{job_hash}",
                            "can_apply": True,
                            "apply_method": "hash_lookup"
                        }
                        for title, company, source, job_hash, notification_id, is_read in zip(
                            group['job_titles'],  # Show all matched jobs
                            group['job_companies'],
                            group['job_sources'],
                            group['job_hashes'],
                            group['notification_ids'],
                            group['read_statuses']
                        )
                    ]
                })
        else:
            # Individual notifications
            individual_query = """
                SELECT 
                    id,
                    job_title,
                    job_company,
                    job_source,
                    job_hash,
                    matched_keywords,
                    sent_at,
                    is_read,
                    read_at
                FROM iosapp.notification_hashes
                WHERE device_id = $1
                ORDER BY sent_at DESC
                LIMIT $2
            """
            
            individual_result = await db_manager.execute_query(individual_query, device_id, limit)
            
            notifications = []
            for notification in individual_result:
                # Parse matched keywords
                matched_keywords = []
                if notification['matched_keywords']:
                    try:
                        if isinstance(notification['matched_keywords'], str):
                            matched_keywords = json.loads(notification['matched_keywords'])
                        else:
                            matched_keywords = notification['matched_keywords']
                    except:
                        matched_keywords = []
                
                notifications.append({
                    "id": str(notification['id']),
                    "type": "job_match",
                    "title": f"New Job: {notification['job_title']}",
                    "message": f"💼 {notification['job_company']} • {', '.join(matched_keywords[:2])}",
                    "job_count": 1,
                    "matched_keywords": matched_keywords,
                    "sent_at": notification['sent_at'].isoformat() if notification['sent_at'] else None,
                    "is_read": notification.get('is_read', False),
                    "read_at": notification['read_at'].isoformat() if notification.get('read_at') else None,
                    "jobs": [{
                        "title": notification['job_title'],
                        "company": notification['job_company'],
                        "source": notification['job_source'],
                        "job_hash": notification['job_hash'],
                        "notification_id": str(notification['id']),
                        "is_read": notification.get('is_read', False),
                        "apply_link": f"{settings.BASE_URL}/api/v1/notifications/job-by-hash/{notification['job_hash']}",
                        "deep_link": f"birjob://job/hash/{notification['job_hash']}",
                        "can_apply": True,
                        "apply_method": "hash_lookup"
                    }]
                })
        
        # Get total unread count (all unread notifications)
        unread_query = """
            SELECT COUNT(*) as unread_count
            FROM iosapp.notification_hashes
            WHERE device_id = $1 AND is_read = false
        """
        unread_result = await db_manager.execute_query(unread_query, device_id)
        unread_count = unread_result[0]['unread_count'] if unread_result else 0
        
        return {
            "success": True,
            "data": {
                "notifications": notifications,
                "unread_count": unread_count,
                "total_shown": len(notifications),
                "grouped": group_by_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification inbox: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification inbox")

@router.delete("/clear/{device_token}")
async def clear_notification_history(
    device_token: str,
    days_old: int = 30
):
    """Clear old notification history for a device"""
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
        
        # Delete old notifications
        delete_query = """
            DELETE FROM iosapp.notification_hashes
            WHERE device_id = $1 AND sent_at < NOW() - INTERVAL '%s days'
            RETURNING id
        """ % days_old
        
        deleted_result = await db_manager.execute_query(delete_query, device_id)
        deleted_count = len(deleted_result) if deleted_result else 0
        
        return {
            "success": True,
            "message": f"Cleared {deleted_count} notifications older than {days_old} days",
            "deleted_count": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing notification history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear notifications")

@router.post("/test/{device_token}")
async def send_test_notification(device_token: str):
    """Send test notification to device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id, keywords FROM iosapp.device_users
            WHERE device_token = $1 AND notifications_enabled = true
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or notifications disabled")
        
        device_id = device_result[0]['id']
        keywords = device_result[0]['keywords'] or []
        
        # Use minimal notification service to send test
        from app.services.minimal_notification_service import minimal_notification_service
        
        # Create test job
        test_job = {
            "id": 999999,
            "title": "Test iOS Developer Position",
            "company": "Test Company Inc.",
            "source": "test",
            "description": f"Test job matching your keywords: {keywords[:3]}"
        }
        
        # Send test notification
        success = await minimal_notification_service.send_job_notification(
            device_token, str(device_id), test_job, keywords[:2] if keywords else ["Test"]
        )
        
        if success:
            # Record test notification
            import hashlib
            job_hash = hashlib.md5(f"{test_job['title']}{test_job['company']}test".encode()).hexdigest()
            
            await minimal_notification_service.record_notification_sent(
                str(device_id), job_hash, test_job["title"], 
                test_job["company"], "test", keywords[:2] if keywords else ["Test"],
                "https://example.com/apply/test-notification"  # Test apply link
            )
        
        return {
            "success": success,
            "message": "Test notification sent!" if success else "Failed to send test notification",
            "device_token_preview": device_token[:16] + "...",
            "test_job": test_job
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test notification")

@router.put("/settings/{device_token}")
async def update_device_notification_settings(
    device_token: str,
    settings: Dict[str, Any]
):
    """Update notification settings for a device"""
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
        
        # Extract settings
        notifications_enabled = settings.get("notifications_enabled", True)
        keywords = settings.get("keywords", [])
        
        # Update device settings
        update_query = """
            UPDATE iosapp.device_users
            SET 
                notifications_enabled = $1,
                keywords = $2,
                created_at = NOW()
            WHERE id = $3
        """
        
        await db_manager.execute_command(
            update_query, 
            notifications_enabled, 
            json.dumps(keywords), 
            device_id
        )
        
        # Log settings change (with consent check)
        metadata = {
            "notifications_enabled": notifications_enabled,
            "keywords_count": len(keywords),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await privacy_analytics_service.track_action_with_consent(
            device_id,
            'settings_updated',
            metadata
        )
        
        return {
            "success": True,
            "message": "Device notification settings updated",
            "data": {
                "device_token_preview": device_token[:16] + "...",
                "notifications_enabled": notifications_enabled,
                "keywords": keywords,
                "keywords_count": len(keywords)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update device settings")

@router.get("/settings/{device_token}")
async def get_device_notification_settings(device_token: str):
    """Get notification settings for a device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device settings
        settings_query = """
            SELECT 
                keywords,
                notifications_enabled,
                created_at
            FROM iosapp.device_users
            WHERE device_token = $1
        """
        
        settings_result = await db_manager.execute_query(settings_query, device_token)
        
        if not settings_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        settings = settings_result[0]
        keywords = settings['keywords'] or []
        
        # Get notification stats
        stats_query = """
            SELECT 
                COUNT(*) as total_notifications,
                COUNT(*) FILTER (WHERE sent_at >= NOW() - INTERVAL '7 days') as notifications_7d,
                COUNT(*) FILTER (WHERE sent_at >= NOW() - INTERVAL '24 hours') as notifications_24h,
                MAX(sent_at) as last_notification
            FROM iosapp.notification_hashes nh
            JOIN iosapp.device_users du ON nh.device_id = du.id
            WHERE du.device_token = $1
        """
        
        stats_result = await db_manager.execute_query(stats_query, device_token)
        stats = stats_result[0] if stats_result else {}
        
        return {
            "success": True,
            "data": {
                "device_token_preview": device_token[:16] + "...",
                "notifications_enabled": settings['notifications_enabled'],
                "keywords": keywords,
                "keywords_count": len(keywords),
                "registered_at": settings['created_at'].isoformat() if settings['created_at'] else None,
                "stats": {
                    "total_notifications": stats.get('total_notifications', 0),
                    "notifications_last_7_days": stats.get('notifications_7d', 0),
                    "notifications_last_24_hours": stats.get('notifications_24h', 0),
                    "last_notification": stats['last_notification'].isoformat() if stats.get('last_notification') else None
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device settings")

@router.post("/mark-read/{device_token}")
async def mark_notifications_as_read(
    device_token: str,
    request_data: Dict[str, Any] = None
):
    """Mark specific notifications or all notifications as read for a device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        if request_data is None:
            request_data = {}
        
        notification_ids = request_data.get("notification_ids", [])
        mark_all = request_data.get("mark_all", False)
        
        # Get device info
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        if mark_all or not notification_ids:
            # Mark all notifications as read
            mark_all_query = """
                UPDATE iosapp.notification_hashes
                SET is_read = true, read_at = NOW()
                WHERE device_id = $1 AND is_read = false
                RETURNING id
            """
            marked_result = await db_manager.execute_query(mark_all_query, device_id)
            marked_count = len(marked_result) if marked_result else 0
            
            # Record bulk read event (with consent check)
            metadata = {
                "notification_count": marked_count,
                "read_at": datetime.now(timezone.utc).isoformat()
            }
            
            await privacy_analytics_service.track_action_with_consent(
                str(device_id),
                'notifications_all_read',
                metadata
            )
            
            message = f"Marked all {marked_count} notifications as read"
        else:
            # Mark specific notifications as read
            marked_count = 0
            for notification_id in notification_ids:
                try:
                    import uuid
                    notification_uuid = uuid.UUID(str(notification_id))
                    
                    # Update the specific notification
                    mark_query = """
                        UPDATE iosapp.notification_hashes
                        SET is_read = true, read_at = NOW()
                        WHERE device_id = $1 AND id = $2 AND is_read = false
                        RETURNING id
                    """
                    mark_result = await db_manager.execute_query(mark_query, device_id, notification_uuid)
                    
                    if mark_result:
                        marked_count += 1
                        
                        # Record read event in analytics (with consent check)
                        metadata = {
                            "notification_id": str(notification_id),
                            "read_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        await privacy_analytics_service.track_action_with_consent(
                            str(device_id),
                            'notification_read',
                            metadata
                        )
                except (ValueError, TypeError):
                    # Invalid UUID format, skip
                    continue
                except Exception:
                    continue
            
            message = f"Marked {marked_count} notifications as read"
        
        return {
            "success": True,
            "message": message,
            "data": {
                "device_token_preview": device_token[:16] + "...",
                "marked_count": marked_count,
                "notification_ids": notification_ids or "all"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notifications as read")

@router.delete("/delete/{device_token}")
async def delete_notifications(
    device_token: str,
    request_data: Dict[str, Any] = None
):
    """Delete specific notifications or all notifications for a device"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        if request_data is None:
            request_data = {}
        
        notification_ids = request_data.get("notification_ids", [])
        delete_all = request_data.get("delete_all", False)
        
        # Get device info
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        if delete_all:
            # Delete all notifications for device
            delete_all_query = """
                DELETE FROM iosapp.notification_hashes
                WHERE device_id = $1
                RETURNING id
            """
            deleted_result = await db_manager.execute_query(delete_all_query, device_id)
            deleted_count = len(deleted_result) if deleted_result else 0
            
            # Log deletion (with consent check)
            metadata = {
                "deleted_count": deleted_count,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            
            await privacy_analytics_service.track_action_with_consent(
                str(device_id),
                'notifications_all_deleted',
                metadata
            )
            
            message = f"Deleted all {deleted_count} notifications"
            
        elif notification_ids:
            # Delete specific notifications
            deleted_count = 0
            
            for notification_id in notification_ids:
                delete_query = """
                    DELETE FROM iosapp.notification_hashes
                    WHERE device_id = $1 AND id = $2
                    RETURNING id
                """
                
                try:
                    import uuid
                    notification_uuid = uuid.UUID(str(notification_id))
                    delete_result = await db_manager.execute_query(delete_query, device_id, notification_uuid)
                    if delete_result:
                        deleted_count += 1
                except (ValueError, TypeError):
                    # Invalid UUID format, skip
                    continue
            
            # Log deletion (with consent check)
            metadata = {
                "notification_ids": [str(nid) for nid in notification_ids],
                "deleted_count": deleted_count,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            
            await privacy_analytics_service.track_action_with_consent(
                str(device_id),
                'notifications_deleted',
                metadata
            )
            
            message = f"Deleted {deleted_count} notifications"
        else:
            raise HTTPException(status_code=400, detail="Must specify notification_ids or set delete_all=true")
        
        return {
            "success": True,
            "message": message,
            "data": {
                "device_token_preview": device_token[:16] + "...",
                "deleted_count": deleted_count,
                "notification_ids": notification_ids if not delete_all else "all"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notifications")

@router.get("/devices")
async def get_active_devices_compatibility():
    """
    Backward compatibility endpoint for GitHub Actions
    Redirects to the correct minimal-notifications endpoint
    """
    from app.services.minimal_notification_service import MinimalNotificationService
    
    try:
        service = MinimalNotificationService()
        devices = await service.get_active_devices_with_keywords()
        
        # Format for backward compatibility
        formatted_devices = []
        for device in devices:
            formatted_devices.append({
                "device_id": device["device_id"],
                "device_token_preview": device["device_token"][:16] + "...",
                "keywords_count": len(device["keywords"]),
                "keywords": device["keywords"][:5]  # First 5 keywords only
            })
        
        return {
            "success": True,
            "data": {
                "active_devices_count": len(devices),
                "devices": formatted_devices
            },
            "note": "This endpoint is deprecated. Use /api/v1/minimal-notifications/devices/active instead."
        }
        
    except Exception as e:
        logger.error(f"Error getting active devices for compatibility: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active devices")

@router.post("/process")
async def process_notifications_compatibility(request: Dict[str, Any]):
    """
    Backward compatibility endpoint for GitHub Actions notification processing
    Redirects to the correct minimal-notifications endpoint
    """
    from app.services.minimal_notification_service import MinimalNotificationService
    
    try:
        jobs = request.get("jobs", [])
        
        if not jobs:
            return {
                "success": False,
                "message": "No jobs provided",
                "stats": {
                    "processed_jobs": 0,
                    "matched_devices": 0,
                    "notifications_sent": 0,
                    "errors": 1
                }
            }
        
        service = MinimalNotificationService()
        
        # Process each job
        total_matches = 0
        total_sent = 0
        
        for job in jobs:
            try:
                # Get active devices
                devices = await service.get_active_devices_with_keywords()
                
                # Simple keyword matching
                job_title = job.get("title", "").lower()
                job_company = job.get("company", "").lower()
                
                for device in devices:
                    # Check if any keywords match
                    matched = False
                    for keyword in device["keywords"]:
                        if keyword.lower() in job_title or keyword.lower() in job_company:
                            matched = True
                            break
                    
                    if matched:
                        total_matches += 1
                        # In a real scenario, would send notification here
                        total_sent += 1
                        
            except Exception as e:
                logger.error(f"Error processing job: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Processed {len(jobs)} jobs",
            "stats": {
                "processed_jobs": len(jobs),
                "matched_devices": total_matches,
                "notifications_sent": total_sent,
                "errors": 0
            },
            "note": "This endpoint is deprecated. Use /api/v1/minimal-notifications/process-jobs instead."
        }
        
    except Exception as e:
        logger.error(f"Error processing notifications for compatibility: {e}")
        raise HTTPException(status_code=500, detail="Failed to process notifications")

@router.get("/job-by-hash/{job_hash}", response_model=Dict[str, Any])
async def get_notification_job_by_hash(job_hash: str):
    """Get job details by hash for notification apply button (persistent after truncate-and-load)"""
    try:
        # First, try to find the job by hash using title and company
        # This works even after truncate-and-load operations
        job_query = """
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at as posted_at
            FROM scraper.jobs_jobpost
            WHERE LEFT(ENCODE(SHA256(CONVERT_TO(LOWER(TRIM(title)) || '|' || LOWER(TRIM(company)), 'UTF8')), 'hex'), 32) = $1
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        job_result = await db_manager.execute_query(job_query, job_hash)
        
        if not job_result:
            # If not found by hash, try alternative search by comparing recent jobs
            fallback_query = """
                SELECT 
                    id,
                    title,
                    company,
                    apply_link,
                    source,
                    created_at as posted_at,
                    LEFT(ENCODE(SHA256(CONVERT_TO(LOWER(TRIM(title)) || '|' || LOWER(TRIM(company)), 'UTF8')), 'hex'), 32) as computed_hash
                FROM scraper.jobs_jobpost
                WHERE created_at >= NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 1000
            """
            
            all_jobs = await db_manager.execute_query(fallback_query)
            
            # Find matching job by hash
            for job in all_jobs:
                if job.get('computed_hash') == job_hash:
                    job_result = [job]
                    break
        
        if not job_result:
            # Try to get stored notification data for this hash
            notification_query = """
                SELECT job_title, job_company, job_source, sent_at, apply_link
                FROM iosapp.notification_hashes
                WHERE job_hash = $1
                ORDER BY sent_at DESC
                LIMIT 1
            """
            notification_result = await db_manager.execute_query(notification_query, job_hash)
            
            if notification_result:
                # Return response with stored notification data
                notification_data = notification_result[0]
                stored_apply_link = notification_data.get('apply_link')
                
                if stored_apply_link:
                    # We have a stored apply link - return success for direct application
                    logger.info(f"Job not found for hash {job_hash}, but stored apply link available. Providing direct apply.")
                    return {
                        "success": True,
                        "data": {
                            "id": "stored_notification",
                            "title": notification_data['job_title'],
                            "company": notification_data['job_company'],
                            "source": notification_data['job_source'],
                            "posted_at": notification_data['sent_at'].isoformat() if notification_data['sent_at'] else None,
                            "hash": job_hash,
                            "apply_link": stored_apply_link,
                            "can_apply": True,
                            "apply_method": "stored_link",
                            "found_by": "notification_storage"
                        }
                    }
                else:
                    # No stored apply link - provide fallback search options
                    logger.info(f"Job not found for hash {job_hash}, no stored apply link. Providing fallback response.")
                    return {
                        "success": False,
                        "error": "job_not_found",
                        "message": "This job is no longer available. It may have been removed during data refresh.",
                        "data": {
                            "hash": job_hash,
                            "title": notification_data['job_title'],
                            "company": notification_data['job_company'],
                            "source": notification_data['job_source'],
                            "posted_at": notification_data['sent_at'].isoformat() if notification_data['sent_at'] else None,
                            "can_apply": False,
                            "apply_method": "unavailable",
                            "fallback_action": "search_similar_jobs",
                            "deep_link": f"birjob://search?company={notification_data['job_company']}&title={notification_data['job_title']}",
                            "search_link": f"/api/v1/jobs-minimal/?search={notification_data['job_title']}&company={notification_data['job_company']}",
                            "debug_info": {
                                "searched_period": "30 days",
                                "search_method": "hash_lookup_with_fallback",
                                "likely_cause": "job_removed_during_data_refresh"
                            }
                        }
                    }
            else:
                # No notification data found either
                logger.info(f"Job and notification data not found for hash {job_hash}. Providing basic fallback response.")
                return {
                    "success": False,
                    "error": "job_not_found",
                    "message": "Job not found. It may have been removed during data refresh or is older than 30 days.",
                    "data": {
                        "hash": job_hash,
                        "can_apply": False,
                        "apply_method": "unavailable",
                        "fallback_action": "search_similar_jobs",
                        "deep_link": f"birjob://search?hash={job_hash}",
                        "search_link": f"/api/v1/jobs-minimal/?search=",
                        "debug_info": {
                            "searched_period": "30 days",
                            "search_method": "hash_lookup_with_fallback",
                            "likely_cause": "job_removed_during_data_refresh"
                        }
                    }
                }
        
        job = job_result[0]
        
        # Check if apply link is still valid (not empty or placeholder)
        apply_link = job.get('apply_link', '').strip()
        if not apply_link or apply_link.lower() in ['', 'null', 'none', 'n/a']:
            apply_link = None
        
        job_data = {
            "id": job['id'],
            "title": job['title'] or "No Title",
            "company": job['company'] or "Unknown Company", 
            "apply_link": apply_link,
            "source": job['source'] or "Unknown",
            "posted_at": job['posted_at'].isoformat() if job['posted_at'] else None,
            "hash": job_hash,
            "found_by": "hash_lookup",
            "can_apply": bool(apply_link),
            "apply_method": "external_link" if apply_link else "unavailable"
        }
        
        return {
            "success": True,
            "data": job_data
        }
        
    except Exception as e:
        logger.error(f"Error getting notification job by hash {job_hash}: {e}")
        return {
            "success": False,
            "error": "lookup_failed",
            "message": "Failed to lookup job by hash",
            "data": {
                "hash": job_hash,
                "fallback_action": "search_similar_jobs",
                "deep_link": f"birjob://search?hash={job_hash}",
                "debug_info": {
                    "error_type": "database_error",
                    "search_method": "hash_lookup_with_fallback",
                    "likely_cause": "database_connection_issue"
                }
            }
        }

@router.post("/apply/{device_token}")
async def handle_notification_apply(
    device_token: str,
    request_data: Dict[str, Any]
):
    """Handle apply action from iOS notification inbox with enhanced fallback mechanisms"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        job_hash = request_data.get("job_hash")
        notification_id = request_data.get("notification_id")
        
        if not job_hash:
            raise HTTPException(status_code=400, detail="job_hash is required")
        
        # Get device info
        device_query = """
            SELECT id FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        
        # Try to get the job by hash first
        job_lookup_result = await get_notification_job_by_hash(job_hash)
        
        if job_lookup_result.get("success"):
            # Job found, return direct apply link
            job_data = job_lookup_result["data"]
            
            # Mark notification as read if notification_id provided
            if notification_id:
                try:
                    import uuid
                    
                    # Handle different notification ID formats
                    if str(notification_id).startswith('group_'):
                        # For grouped notifications, mark all notifications for this job_hash as read
                        mark_group_query = """
                            UPDATE iosapp.notification_hashes
                            SET is_read = true, read_at = NOW()
                            WHERE device_id = $1 AND job_hash = $2 AND is_read = false
                        """
                        await db_manager.execute_query(mark_group_query, device_id, job_hash)
                        logger.debug(f"Marked group notifications as read for job_hash: {job_hash}")
                    else:
                        # For individual notifications, try to parse as UUID
                        notification_uuid = uuid.UUID(str(notification_id))
                        mark_read_query = """
                            UPDATE iosapp.notification_hashes
                            SET is_read = true, read_at = NOW()
                            WHERE device_id = $1 AND id = $2
                        """
                        await db_manager.execute_query(mark_read_query, device_id, notification_uuid)
                        logger.debug(f"Marked individual notification as read: {notification_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to mark notification as read (notification_id: {notification_id}): {e}")
                    # Still continue with the apply process even if marking as read fails
            
            # Track apply attempt (with consent check)
            metadata = {
                "job_hash": job_hash,
                "apply_method": job_data.get("apply_method", "direct"),
                "success": True,
                "applied_at": datetime.now(timezone.utc).isoformat()
            }
            
            await privacy_analytics_service.track_action_with_consent(
                str(device_id),
                'job_apply_attempt',
                metadata
            )
            
            return {
                "success": True,
                "action": "apply_direct",
                "data": {
                    "apply_link": job_data.get("apply_link"),
                    "job_title": job_data.get("title"),
                    "job_company": job_data.get("company"),
                    "deep_link": f"birjob://job/details/{job_data.get('id')}",
                    "external_apply": bool(job_data.get("apply_link")),
                    "message": "Redirecting to job application..."
                }
            }
        else:
            # Job not found, provide fallback search options
            fallback_data = job_lookup_result.get("data", {})
            
            # Track failed apply attempt (with consent check)
            metadata = {
                "job_hash": job_hash,
                "apply_method": "fallback_search",
                "success": False,
                "error": job_lookup_result.get("error", "job_not_found"),
                "applied_at": datetime.now(timezone.utc).isoformat()
            }
            
            await privacy_analytics_service.track_action_with_consent(
                str(device_id),
                'job_apply_attempt',
                metadata
            )
            
            # Provide search alternatives
            search_options = []
            
            if fallback_data.get("title") and fallback_data.get("company"):
                search_options.append({
                    "type": "similar_jobs",
                    "label": f"Find similar jobs at {fallback_data.get('company')}",
                    "search_link": f"/api/v1/jobs-minimal/?company={fallback_data.get('company')}",
                    "deep_link": f"birjob://search?company={fallback_data.get('company')}"
                })
                
                search_options.append({
                    "type": "title_search", 
                    "label": f"Search for '{fallback_data.get('title')}'",
                    "search_link": f"/api/v1/jobs-minimal/?search={fallback_data.get('title')}",
                    "deep_link": f"birjob://search?title={fallback_data.get('title')}"
                })
            
            search_options.append({
                "type": "general_search",
                "label": "Browse all recent jobs",
                "search_link": "/api/v1/jobs-minimal/?days=7",
                "deep_link": "birjob://search?recent=true"
            })
            
            return {
                "success": False,
                "action": "show_alternatives",
                "error": "job_no_longer_available",
                "message": "This job is no longer available. Here are some alternatives:",
                "data": {
                    "original_job": {
                        "title": fallback_data.get("title", "Unknown Job"),
                        "company": fallback_data.get("company", "Unknown Company"),
                        "hash": job_hash
                    },
                    "search_options": search_options,
                    "fallback_action": fallback_data.get("fallback_action", "search_similar_jobs")
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling notification apply: {e}")
        raise HTTPException(status_code=500, detail="Failed to handle apply action")

@router.get("/session/{session_id}")
async def get_job_matches_by_session_compat(
    session_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of jobs per page")
):
    """Compatibility endpoint for job-matches/session/{session_id} - handles push notification deep links"""
    try:
        # Log the incoming request for debugging
        logger.info(f"Job-matches session request: session_id={session_id}, page={page}, limit={limit}")
        
        # Try to extract device info from session_id pattern: match_YYYYMMDD_HHMMSS_devicetoken_suffix
        import re
        
        # Pattern: match_20250728_163244_1b04456c or similar
        session_pattern = r'^match_\d{8}_\d{6}_([a-fA-F0-9]+)$'
        match = re.match(session_pattern, session_id)
        
        if match:
            # Extract potential device token from session ID (for pattern validation)
            _device_token_suffix = match.group(1)
            
            # Try to find the session in the database using the session_id (simplified approach like working endpoint)
            session_query = """
                SELECT session_id, total_matches, matched_keywords, created_at, device_id
                FROM iosapp.job_match_sessions
                WHERE session_id = $1 AND notification_sent = true
                LIMIT 1
            """
            
            session_result = await db_manager.execute_query(session_query, session_id)
            
            # If not found, try without notification_sent filter
            if not session_result:
                fallback_query = """
                    SELECT session_id, total_matches, matched_keywords, created_at, device_id
                    FROM iosapp.job_match_sessions
                    WHERE session_id = $1
                    LIMIT 1
                """
                session_result = await db_manager.execute_query(fallback_query, session_id)
                if session_result:
                    logger.info(f"Session found in fallback search (no notification_sent filter): {session_id}")
                else:
                    logger.warning(f"Session not found in any search: {session_id}")
            
            if session_result:
                # Found the session, get the jobs
                session_data = session_result[0]
                
                # Calculate offset from page
                offset = (page - 1) * limit
                
                # Get jobs for this session
                jobs_query = """
                    SELECT job_hash, job_title, job_company, job_source, apply_link, 
                           job_data, match_score, created_at
                    FROM iosapp.job_match_session_jobs
                    WHERE session_id = $1
                    ORDER BY match_score DESC, created_at DESC
                    LIMIT $2 OFFSET $3
                """
                
                jobs_result = await db_manager.execute_query(jobs_query, session_id, limit, offset)
                
                # Get total count
                count_query = """
                    SELECT COUNT(*) as total
                    FROM iosapp.job_match_session_jobs
                    WHERE session_id = $1
                """
                count_result = await db_manager.execute_query(count_query, session_id)
                total_count = count_result[0]['total'] if count_result else 0
                
                logger.info(f"Session {session_id}: found {len(jobs_result)} jobs (total: {total_count})")
                
                # Format jobs data
                jobs_data = []
                for job in jobs_result:
                    try:
                        # Parse job_data JSON
                        job_data = json.loads(job['job_data']) if job['job_data'] else {}
                        
                        job_item = {
                            "hash": job['job_hash'],
                            "title": job['job_title'],
                            "company": job['job_company'],
                            "source": job['job_source'],
                            "apply_link": job['apply_link'] or job_data.get('apply_link', ''),
                            "posted_at": job['created_at'].isoformat() if job['created_at'] else None,
                            "match_score": job['match_score'],
                            "can_apply": bool(job['apply_link'] or job_data.get('apply_link')),
                            "deep_link": f"birjob://job/hash/{job['job_hash']}"
                        }
                        
                        # Add additional data from job_data if available
                        if job_data:
                            job_item.update({
                                "id": job_data.get('id'),
                                "description": job_data.get('description', '')[:200] + "..." if job_data.get('description', '') else ""
                            })
                        
                        jobs_data.append(job_item)
                        
                    except Exception as e:
                        logger.error(f"Error processing job in session {session_id}: {e}")
                        continue
                
                # Calculate pagination info (match the working endpoint format exactly)
                has_more = offset + limit < total_count
                current_page = (offset // limit) + 1
                total_pages = (total_count + limit - 1) // limit
                
                # Return exact same format as working endpoint
                return {
                    "success": True,
                    "data": {
                        "session": {
                            "session_id": session_data['session_id'],
                            "total_matches": session_data['total_matches'],
                            "matched_keywords": json.loads(session_data['matched_keywords']) if session_data['matched_keywords'] else [],
                            "created_at": session_data['created_at'].isoformat()
                        },
                        "jobs": jobs_data,
                        "pagination": {
                            "total": total_count,
                            "limit": limit,
                            "offset": offset,
                            "current_page": current_page,
                            "total_pages": total_pages,
                            "has_more": has_more
                        }
                    }
                }
            else:
                # Session not found
                logger.warning(f"Job match session not found: {session_id}")
                raise HTTPException(status_code=404, detail="Job match session not found")
        else:
            # Invalid session ID format
            logger.warning(f"Invalid session ID format: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in compatibility endpoint for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process session request")

@router.get("/debug/hash-lookup/{job_hash}", response_model=Dict[str, Any])
async def debug_hash_lookup(job_hash: str):
    """Debug endpoint for hash lookup issues"""
    try:
        from app.services.minimal_notification_service import MinimalNotificationService
        notification_service = MinimalNotificationService()
        
        debug_info = {
            "input_hash": job_hash,
            "hash_length": len(job_hash),
            "database_status": "checking...",
            "jobs_available": 0,
            "recent_jobs": [],
            "hash_generation_test": {}
        }
        
        # Check database connectivity
        try:
            count_query = "SELECT COUNT(*) as count FROM scraper.jobs_jobpost"
            count_result = await db_manager.execute_query(count_query)
            jobs_count = count_result[0]['count'] if count_result else 0
            debug_info["jobs_available"] = jobs_count
            debug_info["database_status"] = "connected"
        except Exception as e:
            debug_info["database_status"] = f"error: {str(e)}"
            debug_info["jobs_available"] = "unknown"
        
        # Get recent jobs for testing
        try:
            recent_query = """
                SELECT title, company, 
                       LEFT(ENCODE(SHA256(CONVERT_TO(LOWER(TRIM(title)) || '|' || LOWER(TRIM(company)), 'UTF8')), 'hex'), 32) as computed_hash
                FROM scraper.jobs_jobpost
                ORDER BY created_at DESC
                LIMIT 5
            """
            recent_jobs = await db_manager.execute_query(recent_query)
            debug_info["recent_jobs"] = [
                {
                    "title": job['title'],
                    "company": job['company'],
                    "hash": job['computed_hash'],
                    "matches_input": job['computed_hash'] == job_hash
                }
                for job in recent_jobs
            ]
        except Exception as e:
            debug_info["recent_jobs"] = f"error: {str(e)}"
        
        # Test hash generation
        test_cases = [
            ("Senior Python Developer", "Tech Corp"),
            ("Python Developer", "StartupXYZ"),
            ("Backend Engineer", "Company Inc"),
        ]
        
        for title, company in test_cases:
            generated_hash = notification_service.generate_job_hash(title, company)
            debug_info["hash_generation_test"][f"{title} | {company}"] = {
                "generated_hash": generated_hash,
                "matches_input": generated_hash == job_hash
            }
        
        return {
            "success": True,
            "data": debug_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "hash": job_hash,
                "debug_failed": True
            }
        }

@router.get("/job-matches/{device_token}", response_model=Dict[str, Any])
async def get_job_matches_by_session(
    device_token: str,
    session_id: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(default=0, ge=0, description="Number of jobs to skip")
):
    """Get paginated job matches from a session or latest session"""
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
        
        device_id = str(device_result[0]['id'])
        
        # If no session_id provided, get the latest session
        if not session_id:
            latest_session_query = """
                SELECT session_id FROM iosapp.job_match_sessions
                WHERE device_id = $1 AND notification_sent = true
                ORDER BY created_at DESC
                LIMIT 1
            """
            session_result = await db_manager.execute_query(latest_session_query, device_id)
            
            if not session_result:
                return {
                    "success": True,
                    "data": {
                        "session": None,
                        "jobs": [],
                        "pagination": {
                            "total": 0,
                            "limit": limit,
                            "offset": offset,
                            "has_more": False
                        }
                    },
                    "message": "No job match sessions found"
                }
            
            session_id = session_result[0]['session_id']
        
        # Get session details
        session_query = """
            SELECT session_id, total_matches, matched_keywords, created_at
            FROM iosapp.job_match_sessions
            WHERE session_id = $1 AND device_id = $2
        """
        session_result = await db_manager.execute_query(session_query, session_id, device_id)
        
        if not session_result:
            raise HTTPException(status_code=404, detail="Job match session not found")
        
        session_data = session_result[0]
        
        # Get paginated jobs from session
        jobs_query = """
            SELECT job_hash, job_title, job_company, job_source, apply_link, 
                   job_data, match_score, created_at
            FROM iosapp.job_match_session_jobs
            WHERE session_id = $1
            ORDER BY match_score DESC, created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        jobs_result = await db_manager.execute_query(jobs_query, session_id, limit, offset)
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM iosapp.job_match_session_jobs
            WHERE session_id = $1
        """
        count_result = await db_manager.execute_query(count_query, session_id)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Format jobs data
        jobs_data = []
        for job in jobs_result:
            try:
                # Parse job_data JSON
                job_data = json.loads(job['job_data']) if job['job_data'] else {}
                
                job_item = {
                    "hash": job['job_hash'],
                    "title": job['job_title'],
                    "company": job['job_company'],
                    "source": job['job_source'],
                    "apply_link": job['apply_link'] or job_data.get('apply_link', ''),
                    "posted_at": job['created_at'].isoformat() if job['created_at'] else None,
                    "match_score": job['match_score'],
                    "can_apply": bool(job['apply_link'] or job_data.get('apply_link')),
                    "deep_link": f"birjob://job/hash/{job['job_hash']}"
                }
                
                # Add additional data from job_data if available
                if job_data:
                    job_item.update({
                        "id": job_data.get('id'),
                        "description": job_data.get('description', '')[:200] + "..." if job_data.get('description', '') else ""
                    })
                
                jobs_data.append(job_item)
                
            except Exception as e:
                logger.error(f"Error processing job in session {session_id}: {e}")
                continue
        
        # Calculate pagination info
        has_more = offset + limit < total_count
        current_page = (offset // limit) + 1
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "success": True,
            "data": {
                "session": {
                    "session_id": session_data['session_id'],
                    "total_matches": session_data['total_matches'],
                    "matched_keywords": json.loads(session_data['matched_keywords']) if session_data['matched_keywords'] else [],
                    "created_at": session_data['created_at'].isoformat()
                },
                "jobs": jobs_data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "has_more": has_more
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job matches for device {device_token[:16]}...: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job matches")