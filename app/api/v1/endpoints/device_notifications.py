"""
Device-based notification management endpoints
Works with minimal schema (device_users, notification_hashes, user_analytics)
No email dependencies - everything is device-token based
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
import json

from app.core.database import db_manager
# from app.utils.validation import validate_device_token

def validate_device_token(device_token: str) -> str:
    """Simple device token validation"""
    if not device_token or len(device_token) < 16:
        raise HTTPException(status_code=400, detail="Invalid device token")
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
                sent_at
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
                "job_hash": notification['job_hash']
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
                    MAX(sent_at) as latest_sent_at,
                    array_agg(id ORDER BY sent_at DESC) as notification_ids
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
                    "matched_keywords": matched_keywords,
                    "notification_date": group['notification_date'].isoformat() if group['notification_date'] else None,
                    "latest_sent_at": group['latest_sent_at'].isoformat() if group['latest_sent_at'] else None,
                    "jobs": [
                        {
                            "title": title,
                            "company": company,
                            "source": source
                        }
                        for title, company, source in zip(
                            group['job_titles'][:5],  # Show first 5 jobs
                            group['job_companies'][:5],
                            group['job_sources'][:5]
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
                    matched_keywords,
                    sent_at
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
                    "jobs": [{
                        "title": notification['job_title'],
                        "company": notification['job_company'],
                        "source": notification['job_source']
                    }]
                })
        
        # Get total unread count (all notifications from last 7 days)
        unread_query = """
            SELECT COUNT(*) as unread_count
            FROM iosapp.notification_hashes
            WHERE device_id = $1 AND sent_at >= NOW() - INTERVAL '7 days'
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
                test_job["company"], "test", keywords[:2] if keywords else ["Test"]
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
        
        # Log settings change
        analytics_query = """
            INSERT INTO iosapp.user_analytics (device_id, action, metadata)
            VALUES ($1, 'settings_updated', $2)
        """
        
        metadata = {
            "notifications_enabled": notifications_enabled,
            "keywords_count": len(keywords),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db_manager.execute_command(
            analytics_query,
            device_id,
            json.dumps(metadata)
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
            all_notifications_query = """
                SELECT id FROM iosapp.notification_hashes
                WHERE device_id = $1
            """
            all_notifications = await db_manager.execute_query(all_notifications_query, device_id)
            
            # Record bulk read event
            bulk_read_query = """
                INSERT INTO iosapp.user_analytics (device_id, action, metadata)
                VALUES ($1, 'notifications_all_read', $2)
            """
            metadata = {
                "notification_count": len(all_notifications),
                "read_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db_manager.execute_command(
                bulk_read_query,
                device_id,
                json.dumps(metadata)
            )
            
            marked_count = len(all_notifications)
            message = f"Marked all {marked_count} notifications as read"
        else:
            # Mark specific notifications as read
            marked_count = 0
            for notification_id in notification_ids:
                # Record read event in analytics
                read_query = """
                    INSERT INTO iosapp.user_analytics (device_id, action, metadata)
                    VALUES ($1, 'notification_read', $2)
                """
                metadata = {
                    "notification_id": str(notification_id),
                    "read_at": datetime.now(timezone.utc).isoformat()
                }
                
                try:
                    await db_manager.execute_command(
                        read_query, 
                        device_id, 
                        json.dumps(metadata)
                    )
                    marked_count += 1
                except:
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
            
            # Log deletion
            delete_log_query = """
                INSERT INTO iosapp.user_analytics (device_id, action, metadata)
                VALUES ($1, 'notifications_all_deleted', $2)
            """
            metadata = {
                "deleted_count": deleted_count,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db_manager.execute_command(
                delete_log_query,
                device_id,
                json.dumps(metadata)
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
            
            # Log deletion
            delete_log_query = """
                INSERT INTO iosapp.user_analytics (device_id, action, metadata)
                VALUES ($1, 'notifications_deleted', $2)
            """
            metadata = {
                "notification_ids": [str(nid) for nid in notification_ids],
                "deleted_count": deleted_count,
                "deleted_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db_manager.execute_command(
                delete_log_query,
                device_id,
                json.dumps(metadata)
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