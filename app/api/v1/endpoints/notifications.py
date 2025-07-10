from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime, timezone

from app.core.database import db_manager
from app.services.job_notification_service import job_notification_service
from app.services.notification_scheduler import run_notifications_now
from app.schemas.notifications import (
    JobMatchRequest, JobMatchResponse,
    NotificationHistoryResponse,
    NotificationSettingsRequest, NotificationSettingsResponse,
    JobNotificationTriggerRequest, JobNotificationTriggerResponse,
    NotificationInboxResponse, MarkReadResponse, DeleteNotificationResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/job-match", response_model=JobMatchResponse)
async def send_job_match_notification(request: JobMatchRequest):
    """Send a job match notification to a specific user"""
    try:
        success = await job_notification_service.send_single_job_notification(
            device_id=request.device_id,
            job_id=request.job_id,
            job_title=request.job_title,
            job_company=request.job_company,
            job_source=request.job_source,
            matched_keywords=request.matched_keywords
        )
        
        return JobMatchResponse(
            notification_sent=success,
            message="Job match notification processed successfully" if success else "Notification not sent (duplicate or user not found)",
            data={
                "job_id": request.job_id,
                "device_id": request.device_id,
                "matched_keywords": request.matched_keywords
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending job match notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.get("/history/{device_id}", response_model=NotificationHistoryResponse)
async def get_notification_history(device_id: str, limit: int = 50):
    """Get notification history for a user"""
    try:
        if limit > 100:
            limit = 100
        
        history = await job_notification_service.get_user_notification_history(
            device_id=device_id,
            limit=limit
        )
        
        return NotificationHistoryResponse(
            user_id=history['user_id'] or "unknown",
            total_notifications=history['total_notifications'],
            recent_notifications=history['recent_notifications'],
            data={
                "device_id": device_id,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting notification history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification history")

@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(request: NotificationSettingsRequest):
    """Update notification settings for a user"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id as user_id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]['user_id']
        
        # Update user settings
        update_query = """
            UPDATE iosapp.users 
            SET notifications_enabled = $1, keywords = $2, updated_at = NOW()
            WHERE id = $3
        """
        
        import json
        await db_manager.execute_command(
            update_query,
            request.notifications_enabled,
            json.dumps(request.keywords),
            user_id
        )
        
        return NotificationSettingsResponse(
            message="Notification settings updated successfully",
            data={
                "user_id": str(user_id),
                "device_id": request.device_id,
                "notifications_enabled": request.notifications_enabled,
                "keywords": request.keywords
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update notification settings")

@router.post("/trigger", response_model=JobNotificationTriggerResponse)
async def trigger_job_notifications(
    request: JobNotificationTriggerRequest,
    background_tasks: BackgroundTasks
):
    """Trigger job matching notifications for all users"""
    try:
        # Run in background if not dry run
        if not request.dry_run:
            background_tasks.add_task(
                job_notification_service.process_job_notifications,
                source_filter=request.source_filter,
                limit=request.limit,
                dry_run=False
            )
            
            return JobNotificationTriggerResponse(
                message="Job notification processing started in background",
                processed_jobs=0,
                matched_users=0,
                notifications_sent=0,
                data={
                    "status": "processing",
                    "source_filter": request.source_filter,
                    "limit": request.limit
                }
            )
        else:
            # Run synchronously for dry run
            stats = await job_notification_service.process_job_notifications(
                source_filter=request.source_filter,
                limit=request.limit,
                dry_run=True
            )
            
            return JobNotificationTriggerResponse(
                message="Job notification processing completed (dry run)",
                processed_jobs=stats['processed_jobs'],
                matched_users=stats['matched_users'],
                notifications_sent=stats['notifications_sent'],
                data={
                    "status": "completed",
                    "errors": stats.get('errors', 0),
                    "source_filter": request.source_filter,
                    "limit": request.limit,
                    "dry_run": True
                }
            )
        
    except Exception as e:
        logger.error(f"Error triggering job notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger job notifications")

@router.get("/stats", response_model=Dict[str, Any])
async def get_notification_stats():
    """Get overall notification statistics"""
    try:
        # Get stats from last 24 hours
        stats_query = """
            SELECT 
                COUNT(*) as total_notifications,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT job_id) as unique_jobs
            FROM iosapp.job_notification_history
            WHERE notification_sent_at >= NOW() - INTERVAL '24 hours'
        """
        
        stats_result = await db_manager.execute_query(stats_query)
        
        # Get top keywords from recent notifications
        keywords_query = """
            SELECT 
                keyword,
                COUNT(*) as frequency
            FROM (
                SELECT jsonb_array_elements_text(matched_keywords) as keyword
                FROM iosapp.job_notification_history
                WHERE notification_sent_at >= NOW() - INTERVAL '7 days'
                    AND matched_keywords IS NOT NULL
            ) as keywords
            GROUP BY keyword
            ORDER BY frequency DESC
            LIMIT 10
        """
        
        keywords_result = await db_manager.execute_query(keywords_query)
        
        # Get top companies
        companies_query = """
            SELECT 
                job_company,
                COUNT(*) as notification_count
            FROM iosapp.job_notification_history
            WHERE notification_sent_at >= NOW() - INTERVAL '7 days'
                AND job_company IS NOT NULL
            GROUP BY job_company
            ORDER BY notification_count DESC
            LIMIT 10
        """
        
        companies_result = await db_manager.execute_query(companies_query)
        
        # Format results
        stats = stats_result[0] if stats_result else {}
        
        return {
            "last_24_hours": {
                "total_notifications": stats.get('total_notifications', 0),
                "unique_users": stats.get('unique_users', 0),
                "unique_jobs": stats.get('unique_jobs', 0)
            },
            "last_7_days": {
                "top_keywords": [
                    {"keyword": row['keyword'], "frequency": row['frequency']}
                    for row in keywords_result
                ],
                "top_companies": [
                    {"company": row['job_company'], "notifications": row['notification_count']}
                    for row in companies_result
                ]
            },
            "timestamp": "2024-01-01T00:00:00Z"  # Current timestamp would be better
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification stats")

@router.delete("/cleanup", response_model=Dict[str, Any])
async def cleanup_old_notifications(days_old: int = 30):
    """Clean up old notification history records"""
    try:
        if days_old < 1 or days_old > 365:
            raise HTTPException(status_code=400, detail="days_old must be between 1 and 365")
        
        deleted_count = await job_notification_service.cleanup_old_notifications(days_old)
        
        return {
            "success": True,
            "message": f"Cleaned up notification history older than {days_old} days",
            "deleted_records": deleted_count,
            "days_old": days_old
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to clean up notifications")

@router.post("/token")
async def register_push_token(request: dict):
    """Register push token for notifications"""
    try:
        device_token = request.get("device_token")
        device_info = request.get("device_info", {})
        
        if not device_token:
            raise HTTPException(status_code=400, detail="device_token is required")
        
        # Get device_id from request or generate one
        device_id = request.get("device_id")
        if not device_id:
            # If no device_id provided, look for existing device by token
            device_id = device_token  # Temporary fallback
        
        # Create or update device token - check both device_id and token
        device_query = """
            SELECT id, user_id FROM iosapp.device_tokens 
            WHERE device_id = $1 OR device_token = $2
        """
        device_result = await db_manager.execute_query(device_query, device_id, device_token)
        
        if device_result:
            # Update existing device
            update_query = """
                UPDATE iosapp.device_tokens 
                SET device_token = $1, device_info = $2, is_active = true, updated_at = NOW()
                WHERE id = $3
            """
            await db_manager.execute_command(
                update_query, device_token, json.dumps(device_info), device_result[0]['id']
            )
            user_id = device_result[0]['user_id']
            message = "Push token updated successfully"
        else:
            # Create new user and device
            user_query = "INSERT INTO iosapp.users DEFAULT VALUES RETURNING id"
            user_result = await db_manager.execute_query(user_query)
            user_id = user_result[0]['id']
            
            device_insert_query = """
                INSERT INTO iosapp.device_tokens (user_id, device_id, device_token, device_info)
                VALUES ($1, $2, $3, $4)
            """
            await db_manager.execute_command(
                device_insert_query, user_id, device_id, device_token, json.dumps(device_info)
            )
            message = "Push token registered successfully"
        
        return {
            "success": True,
            "data": {
                "device_id": device_id,
                "user_id": str(user_id),
                "message": message
            }
        }
        
    except Exception as e:
        logger.error(f"Error registering push token: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to register push token: {str(e)}")

@router.get("/quick-test/{device_id}")
async def quick_test_for_device(device_id: str):
    """Quick test endpoint to setup and send notifications for specific device"""
    try:
        # First setup the user with keywords if not set
        user_setup_query = """
            UPDATE iosapp.users 
            SET keywords = $1, notifications_enabled = true, updated_at = NOW()
            WHERE id = (
                SELECT u.id FROM iosapp.users u
                JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                WHERE dt.device_id = $2 AND dt.is_active = true
            )
        """
        
        keywords = ["iOS Developer", "Swift", "Mobile App", "iPhone", "React Native", "Apple"]
        import json
        await db_manager.execute_command(user_setup_query, json.dumps(keywords), device_id)
        
        # Now run the real notification processor
        stats = await run_notifications_now(dry_run=False)
        
        return {
            "success": True,
            "message": "Keywords setup and real notifications triggered!",
            "data": {
                "device_id": device_id,
                "keywords_set": keywords,
                "processed_jobs": stats.get('processed_jobs', 0),
                "matched_users": stats.get('matched_users', 0),
                "notifications_sent": stats.get('notifications_sent', 0),
                "mode": "REAL notifications"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in quick test: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Check server logs for details"
        }

@router.post("/test-run", response_model=JobNotificationTriggerResponse)
async def test_run_notifications(dry_run: bool = False):
    """Test run notifications immediately - LIVE MODE by default"""
    try:
        stats = await run_notifications_now(dry_run=dry_run)
        
        return JobNotificationTriggerResponse(
            message=f"Test notification run completed ({'dry run' if dry_run else 'live run'})",
            processed_jobs=stats.get('processed_jobs', 0),
            matched_users=stats.get('matched_users', 0),
            notifications_sent=stats.get('notifications_sent', 0),
            data={
                "status": "completed",
                "errors": stats.get('errors', 0),
                "dry_run": dry_run,
                "test_mode": True
            }
        )
        
    except Exception as e:
        logger.error(f"Error in test notification run: {e}")
        raise HTTPException(status_code=500, detail="Failed to run test notifications")

@router.get("/inbox/{device_id}", response_model=NotificationInboxResponse)
async def get_notification_inbox(device_id: str, limit: int = 50, offset: int = 0):
    """Get notification inbox for a device"""
    try:
        if limit > 100:
            limit = 100
            
        # Get user_id from device_id
        user_query = """
            SELECT u.id as user_id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]['user_id']
        
        # Get notification history with job details
        notifications_query = """
            SELECT 
                jnh.id,
                jnh.job_id,
                jnh.job_title,
                jnh.job_company,
                jnh.job_source,
                jnh.matched_keywords,
                jnh.notification_sent_at,
                jnh.is_read,
                -- Get job details from scraper database
                j.apply_link,
                j.created_at as job_posted_at
            FROM iosapp.job_notification_history jnh
            LEFT JOIN scraper.jobs_jobpost j ON jnh.job_id = j.id
            WHERE jnh.user_id = $1
            ORDER BY jnh.notification_sent_at DESC
            LIMIT $2 OFFSET $3
        """
        
        notifications_result = await db_manager.execute_query(notifications_query, user_id, limit, offset)
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total_count,
                   SUM(CASE WHEN is_read = false THEN 1 ELSE 0 END) as unread_count
            FROM iosapp.job_notification_history
            WHERE user_id = $1
        """
        count_result = await db_manager.execute_query(count_query, user_id)
        
        total_count = count_result[0]['total_count'] if count_result else 0
        unread_count = count_result[0]['unread_count'] if count_result else 0
        
        # Group notifications by similar jobs (same notification batch)
        notifications_map = {}
        
        for row in notifications_result:
            # Create a grouping key based on time and keywords (notifications sent within 1 hour with same keywords)
            notification_time = row['notification_sent_at']
            matched_keywords = row['matched_keywords'] or []
            
            # Simple grouping: use date + hour + keywords as key
            time_key = notification_time.strftime('%Y-%m-%d-%H')
            keywords_key = '_'.join(sorted(matched_keywords)) if matched_keywords else 'no_keywords'
            group_key = f"{time_key}_{keywords_key}"
            
            if group_key not in notifications_map:
                notifications_map[group_key] = {
                    'id': str(row['id']),
                    'type': 'job_match',
                    'title': f"{len([row])} New Job{'s' if len([row]) != 1 else ''} Found!",
                    'message': f"We found jobs matching your keywords: {', '.join(matched_keywords[:3]) if matched_keywords else 'N/A'}",
                    'matched_keywords': matched_keywords,
                    'job_count': 1,
                    'created_at': row['notification_sent_at'].isoformat(),
                    'is_read': row['is_read'] or False,
                    'jobs': []
                }
            else:
                notifications_map[group_key]['job_count'] += 1
                notifications_map[group_key]['title'] = f"{notifications_map[group_key]['job_count']} New Jobs Found!"
                # Use the most recent notification ID and read status
                # Compare timezone-aware datetimes
                existing_time = datetime.fromisoformat(notifications_map[group_key]['created_at'].replace('Z', '+00:00'))
                current_time = row['notification_sent_at']
                if hasattr(current_time, 'tzinfo') and current_time.tzinfo is None:
                    current_time = current_time.replace(tzinfo=timezone.utc)
                if current_time > existing_time:
                    notifications_map[group_key]['id'] = str(row['id'])
                    notifications_map[group_key]['created_at'] = row['notification_sent_at'].isoformat()
                    notifications_map[group_key]['is_read'] = row['is_read'] or False
            
            # Add job details
            job_item = {
                'id': row['job_id'],
                'title': row['job_title'] or 'Unknown Job',
                'company': row['job_company'] or 'Unknown Company', 
                'location': 'Remote',  # Default since location not stored
                'apply_link': row['apply_link'] or '',
                'posted_at': (row['job_posted_at'] or row['notification_sent_at']).isoformat(),
                'source': row['job_source'] or 'Unknown'
            }
            
            notifications_map[group_key]['jobs'].append(job_item)
        
        # Convert to list and sort by created_at
        notifications_list = list(notifications_map.values())
        notifications_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return NotificationInboxResponse(
            data={
                "notifications": notifications_list,
                "unread_count": unread_count,
                "total_count": total_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification inbox: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification inbox")

@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_as_read(notification_id: str):
    """Mark notification as read"""
    try:
        import uuid
        
        # Validate UUID format
        try:
            notification_uuid = uuid.UUID(notification_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification ID format")
        
        # Update notification as read
        update_query = """
            UPDATE iosapp.job_notification_history
            SET is_read = true, updated_at = NOW()
            WHERE id = $1
        """
        
        result = await db_manager.execute_command(update_query, notification_uuid)
        
        return MarkReadResponse(
            message="Notification marked as read"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark notification as read")

@router.delete("/{notification_id}", response_model=DeleteNotificationResponse)
async def delete_notification(notification_id: str):
    """Delete notification"""
    try:
        import uuid
        
        # Validate UUID format
        try:
            notification_uuid = uuid.UUID(notification_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification ID format")
        
        # Check if notification exists
        check_query = """
            SELECT id FROM iosapp.job_notification_history WHERE id = $1
        """
        check_result = await db_manager.execute_query(check_query, notification_uuid)
        
        if not check_result:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        # Delete notification (this will cascade to related records if foreign keys are set up)
        delete_query = """
            DELETE FROM iosapp.job_notification_history WHERE id = $1
        """
        await db_manager.execute_command(delete_query, notification_uuid)
        
        return DeleteNotificationResponse(
            message="Notification deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")

@router.get("/{notification_id}/jobs", response_model=Dict[str, Any])
async def get_jobs_for_notification(notification_id: str):
    """Get jobs for a specific notification"""
    try:
        import uuid
        
        # Validate UUID format
        try:
            notification_uuid = uuid.UUID(notification_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid notification ID format")
        
        # Get notification details and associated jobs
        jobs_query = """
            SELECT 
                jnh.id as notification_id,
                jnh.job_id,
                jnh.job_title,
                jnh.job_company,
                jnh.job_source,
                jnh.matched_keywords,
                jnh.notification_sent_at,
                j.apply_link,
                j.created_at as job_posted_at
            FROM iosapp.job_notification_history jnh
            LEFT JOIN scraper.jobs_jobpost j ON jnh.job_id = j.id
            WHERE jnh.id = $1
        """
        
        jobs_result = await db_manager.execute_query(jobs_query, notification_uuid)
        
        if not jobs_result:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification_data = jobs_result[0]
        
        # For grouped notifications, get all jobs with same keywords and similar time
        notification_time = notification_data['notification_sent_at']
        matched_keywords = notification_data['matched_keywords'] or []
        
        # Get jobs within 1 hour of this notification with same keywords
        related_jobs_query = """
            SELECT DISTINCT
                jnh.job_id,
                jnh.job_title,
                jnh.job_company,
                jnh.job_source,
                j.apply_link,
                j.created_at as job_posted_at
            FROM iosapp.job_notification_history jnh
            LEFT JOIN scraper.jobs_jobpost j ON jnh.job_id = j.id
            WHERE jnh.matched_keywords = $1
            AND jnh.notification_sent_at BETWEEN $2 - INTERVAL '1 hour' AND $2 + INTERVAL '1 hour'
            ORDER BY jnh.notification_sent_at DESC
        """
        
        related_jobs_result = await db_manager.execute_query(
            related_jobs_query, 
            json.dumps(matched_keywords),
            notification_time
        )
        
        # Format job items
        jobs = []
        for job_row in related_jobs_result:
            job_item = {
                'id': job_row['job_id'],
                'title': job_row['job_title'] or 'Unknown Job',
                'company': job_row['job_company'] or 'Unknown Company',
                'location': 'Remote',  # Default since location not stored
                'apply_link': job_row['apply_link'] or '',
                'posted_at': (job_row['job_posted_at'] or notification_time).isoformat(),
                'source': job_row['job_source'] or 'Unknown'
            }
            jobs.append(job_item)
        
        return {
            "success": True,
            "data": {
                "notification_id": notification_id,
                "matched_keywords": matched_keywords,
                "job_count": len(jobs),
                "jobs": jobs
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting jobs for notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jobs for notification")

@router.post("/test-push/{device_id}")
async def test_push_notification(device_id: str, message: str = "Test notification from backend!"):
    """Send immediate test push notification to device"""
    try:
        # Get device token for this device_id
        device_query = """
            SELECT dt.device_token, dt.user_id, u.keywords 
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or inactive")
        
        device_data = device_result[0]
        device_token = device_data['device_token']
        user_id = device_data['user_id']
        keywords = device_data['keywords'] or []
        
        # Create a fake job for testing
        test_job = {
            'id': 999999,
            'title': 'Test iOS Developer Position',
            'company': 'Test Company Inc.',
            'source': 'test',
            'apply_link': 'https://example.com/test-job'
        }
        
        # Use actual push notification service
        from app.services.push_notifications import PushNotificationService
        push_service = PushNotificationService()
        
        # Generate a test notification ID
        import uuid
        test_match_id = str(uuid.uuid4())
        
        # Record the test notification in database first
        insert_query = """
            INSERT INTO iosapp.job_notification_history 
            (user_id, job_id, job_title, job_company, job_source, job_unique_key, matched_keywords, notification_sent_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING id
        """
        
        notification_result = await db_manager.execute_query(
            insert_query,
            user_id,
            test_job['id'],
            test_job['title'],
            test_job['company'],
            test_job['source'],
            'test_' + test_match_id,
            json.dumps(keywords[:2]) if keywords else json.dumps(['Test'])
        )
        
        notification_id = str(notification_result[0]['id'])
        
        # Send the actual push notification
        success = await push_service.send_job_match_notification(
            device_token=device_token,
            device_id=device_id,
            job=test_job,
            matched_keywords=keywords[:2] if keywords else ['Test'],
            match_id=notification_id
        )
        
        return {
            "success": success,
            "message": "Test push notification sent!" if success else "Failed to send push notification",
            "data": {
                "device_id": device_id,
                "notification_id": notification_id,
                "job": test_job,
                "matched_keywords": keywords[:2] if keywords else ['Test'],
                "device_token_preview": device_token[:20] + "..." if device_token else "None"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test push notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

@router.post("/test-simple-push/{device_id}")
async def test_simple_push_notification(device_id: str):
    """Send simple test push notification without database recording"""
    try:
        # Get device token for this device_id
        device_query = """
            SELECT dt.device_token
            FROM iosapp.device_tokens dt
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or inactive")
        
        device_token = device_result[0]['device_token']
        
        # Use push notification service directly
        from app.services.push_notifications import PushNotificationService
        push_service = PushNotificationService()
        
        # Send a simple system notification
        success = await push_service.send_system_notification(
            device_token=device_token,
            device_id=device_id,
            title="🚀 Test Notification",
            message="Your push notifications are working!",
            data={"test": True, "timestamp": str(datetime.now())}
        )
        
        return {
            "success": success,
            "message": "Simple test notification sent!" if success else "Failed to send notification",
            "data": {
                "device_id": device_id,
                "device_token_preview": device_token[:20] + "..." if device_token else "None",
                "notification_type": "system_test"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending simple test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send simple test notification: {str(e)}")

@router.get("/test-devices")
async def get_test_devices():
    """Get list of registered devices for testing"""
    try:
        devices_query = """
            SELECT 
                dt.device_id,
                dt.device_token,
                dt.is_active,
                dt.registered_at,
                u.email,
                u.keywords,
                u.notifications_enabled
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.is_active = true
            ORDER BY dt.registered_at DESC
            LIMIT 20
        """
        
        devices_result = await db_manager.execute_query(devices_query)
        
        devices = []
        for device in devices_result:
            devices.append({
                "device_id": device['device_id'],
                "device_token_preview": device['device_token'][:20] + "..." if device['device_token'] else "None",
                "email": device['email'],
                "keywords": device['keywords'],
                "notifications_enabled": device['notifications_enabled'],
                "registered_at": device['registered_at'].isoformat() if device['registered_at'] else None
            })
        
        return {
            "success": True,
            "data": {
                "devices": devices,
                "total_count": len(devices)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting test devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get test devices")

@router.post("/run-real-notifications")
async def run_real_notifications_now():
    """Immediately run real job matching notifications for all active users"""
    try:
        # Import the job notification service
        from app.services.job_notification_service import job_notification_service
        
        # Run the actual notification processing (not dry run)
        stats = await job_notification_service.process_job_notifications(
            source_filter=None,  # Check all job sources
            limit=None,  # Check ALL jobs from last 24 hours
            dry_run=False  # REAL notifications
        )
        
        return {
            "success": True,
            "message": "Real job notifications processed and sent!",
            "data": {
                "processed_jobs": stats.get('processed_jobs', 0),
                "matched_users": stats.get('matched_users', 0),
                "notifications_sent": stats.get('notifications_sent', 0),
                "errors": stats.get('errors', 0),
                "mode": "LIVE - Real notifications sent"
            }
        }
        
    except Exception as e:
        logger.error(f"Error running real notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run real notifications: {str(e)}")

@router.post("/force-job-check/{device_id}")
async def force_job_check_for_device(device_id: str):
    """Force immediate job checking and notifications for a specific device"""
    try:
        # Get user info for this device
        user_query = """
            SELECT u.id as user_id, u.keywords, u.notifications_enabled, dt.device_token
            FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true AND u.notifications_enabled = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="Device not found or notifications disabled")
        
        user_data = user_result[0]
        user_id = user_data['user_id']
        keywords = user_data['keywords'] or []
        device_token = user_data['device_token']
        
        if not keywords:
            raise HTTPException(status_code=400, detail="No keywords set for user")
        
        # Get recent jobs from scraper database
        recent_jobs_query = """
            SELECT id, title, company, apply_link, source, created_at
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 100
        """
        
        jobs_result = await db_manager.execute_query(recent_jobs_query)
        
        if not jobs_result:
            return {
                "success": True,
                "message": "No recent jobs found to check against your keywords",
                "data": {
                    "device_id": device_id,
                    "keywords": keywords,
                    "jobs_checked": 0,
                    "matches_found": 0
                }
            }
        
        # Use the actual job notification service to process
        from app.services.job_notification_service import JobNotificationService
        notification_service = JobNotificationService()
        
        matches_found = 0
        notifications_sent = 0
        
        # Check each recent job against user's keywords
        for job in jobs_result:
            # Use the actual keyword matching logic
            matched_keywords = notification_service._match_keywords(job, keywords)
            
            if matched_keywords:
                # Check if already notified
                job_unique_key = notification_service._generate_job_unique_key(job['title'], job['company'])
                
                already_notified_query = """
                    SELECT id FROM iosapp.job_notification_history
                    WHERE user_id = $1 AND job_unique_key = $2
                """
                already_notified = await db_manager.execute_query(already_notified_query, user_id, job_unique_key)
                
                if not already_notified:
                    matches_found += 1
                    
                    # Record the notification
                    notification_id = await notification_service._record_notification(
                        user_id, job['id'], job['title'], job['company'], 
                        job.get('source'), job_unique_key, matched_keywords
                    )
                    
                    if notification_id:
                        # Send actual push notification
                        from app.services.push_notifications import PushNotificationService
                        push_service = PushNotificationService()
                        
                        success = await push_service.send_job_match_notification(
                            device_token=device_token,
                            device_id=device_id,
                            job=job,
                            matched_keywords=matched_keywords,
                            match_id=notification_id
                        )
                        
                        if success:
                            notifications_sent += 1
        
        return {
            "success": True,
            "message": f"Found {matches_found} new job matches! {notifications_sent} notifications sent.",
            "data": {
                "device_id": device_id,
                "keywords": keywords,
                "jobs_checked": len(jobs_result),
                "matches_found": matches_found,
                "notifications_sent": notifications_sent,
                "mode": "REAL job matching"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in force job check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check jobs: {str(e)}")

@router.get("/devices")
async def list_devices():
    """List all registered devices (simple version)"""
    try:
        devices_query = """
            SELECT 
                dt.device_id,
                dt.is_active,
                u.keywords,
                u.notifications_enabled
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.is_active = true
            ORDER BY dt.registered_at DESC
            LIMIT 10
        """
        
        devices_result = await db_manager.execute_query(devices_query)
        
        return {
            "success": True,
            "devices": [
                {
                    "device_id": device['device_id'],
                    "keywords": device['keywords'],
                    "notifications_enabled": device['notifications_enabled']
                }
                for device in devices_result
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list devices: {str(e)}")

@router.get("/device-info/{device_id}")
async def get_device_info(device_id: str):
    """Get detailed info for a specific device"""
    try:
        device_query = """
            SELECT 
                dt.device_id,
                dt.device_token,
                dt.is_active,
                u.id as user_id,
                u.email,
                u.keywords,
                u.notifications_enabled
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_data = device_result[0]
        
        return {
            "success": True,
            "data": {
                "device_id": device_data['device_id'],
                "user_id": str(device_data['user_id']),
                "email": device_data['email'],
                "keywords": device_data['keywords'],
                "notifications_enabled": device_data['notifications_enabled'],
                "is_active": device_data['is_active'],
                "has_device_token": bool(device_data['device_token']),
                "device_token_preview": device_data['device_token'][:20] + "..." if device_data['device_token'] else "None"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device info: {str(e)}")

@router.post("/refresh-token/{device_id}")
async def refresh_device_token(device_id: str, request: dict):
    """Refresh device token for a specific device (for fixing BadDeviceToken errors)"""
    try:
        new_device_token = request.get("device_token")
        
        if not new_device_token:
            raise HTTPException(status_code=400, detail="device_token is required")
        
        # Validate token format
        from app.services.push_notifications import PushNotificationService
        push_service = PushNotificationService()
        
        if not push_service._validate_device_token(new_device_token):
            raise HTTPException(status_code=400, detail="Invalid device token format")
        
        # Update device token
        update_query = """
            UPDATE iosapp.device_tokens 
            SET device_token = $1, updated_at = NOW()
            WHERE device_id = $2
        """
        
        await db_manager.execute_command(update_query, new_device_token, device_id)
        
        # Test the new token immediately
        test_success = await push_service.send_system_notification(
            device_token=new_device_token,
            device_id=device_id,
            title="🔄 Token Refreshed",
            message="Your device token has been updated successfully!",
            data={"type": "token_refresh_test"}
        )
        
        return {
            "success": True,
            "message": "Device token refreshed successfully",
            "data": {
                "device_id": device_id,
                "new_token_preview": new_device_token[:20] + "...",
                "test_notification_sent": test_success,
                "recommendation": "Check your device for the test notification" if test_success else "Token updated but test notification failed - check APNs logs"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing device token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh token: {str(e)}")

@router.delete("/invalid-tokens")
async def cleanup_invalid_tokens():
    """Mark devices with invalid tokens as inactive (for fixing BadDeviceToken issues)"""
    try:
        # Get all active device tokens
        tokens_query = """
            SELECT dt.id, dt.device_token, dt.device_id
            FROM iosapp.device_tokens dt
            WHERE dt.is_active = true AND dt.device_token IS NOT NULL
        """
        
        tokens_result = await db_manager.execute_query(tokens_query)
        
        from app.services.push_notifications import PushNotificationService
        push_service = PushNotificationService()
        
        invalid_tokens = []
        valid_tokens = []
        
        for token_data in tokens_result:
            device_token = token_data['device_token']
            device_id = token_data['device_id']
            
            # Validate token format first
            if not push_service._validate_device_token(device_token):
                invalid_tokens.append({
                    "device_id": device_id,
                    "reason": "Invalid format",
                    "token_preview": device_token[:20] + "..."
                })
                continue
            
            # Test with APNs (this will show in logs if token is bad)
            validation_result = await push_service.validate_device_token_with_apns(device_token)
            
            if not validation_result.get('valid', False):
                invalid_tokens.append({
                    "device_id": device_id,
                    "reason": validation_result.get('error', 'Unknown error'),
                    "token_preview": device_token[:20] + "..."
                })
            else:
                valid_tokens.append({
                    "device_id": device_id,
                    "token_preview": device_token[:20] + "..."
                })
        
        # Mark invalid tokens as inactive
        deactivated_count = 0
        if invalid_tokens:
            for invalid_token in invalid_tokens:
                deactivate_query = """
                    UPDATE iosapp.device_tokens 
                    SET is_active = false, updated_at = NOW()
                    WHERE device_id = $1
                """
                await db_manager.execute_command(deactivate_query, invalid_token['device_id'])
                deactivated_count += 1
        
        return {
            "success": True,
            "message": f"Token cleanup completed. {deactivated_count} invalid tokens deactivated.",
            "data": {
                "total_tokens_checked": len(tokens_result),
                "valid_tokens": len(valid_tokens),
                "invalid_tokens": len(invalid_tokens),
                "deactivated_count": deactivated_count,
                "valid_devices": valid_tokens,
                "invalid_devices": invalid_tokens
            }
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up invalid tokens: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup tokens: {str(e)}")

@router.post("/setup-keywords/{device_id}")
async def setup_keywords_for_device(device_id: str, keywords: list = None):
    """Setup keywords and enable notifications for a device"""
    try:
        if keywords is None:
            keywords = ["iOS Developer", "Swift", "Mobile App", "iPhone", "React Native"]
        
        # Get user for this device
        user_query = """
            SELECT u.id as user_id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        user_id = user_result[0]['user_id']
        
        # Update user with keywords and enable notifications
        update_query = """
            UPDATE iosapp.users 
            SET keywords = $1, notifications_enabled = true, updated_at = NOW()
            WHERE id = $2
        """
        
        import json
        await db_manager.execute_command(update_query, json.dumps(keywords), user_id)
        
        return {
            "success": True,
            "message": "Keywords setup complete! You can now receive job notifications.",
            "data": {
                "device_id": device_id,
                "user_id": str(user_id),
                "keywords": keywords,
                "notifications_enabled": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up keywords: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup keywords: {str(e)}")

@router.get("/apns-environment-check")
async def check_apns_environment():
    """Check APNs environment configuration and provide recommendations"""
    try:
        from app.services.push_notifications import PushNotificationService
        push_service = PushNotificationService()
        
        # Get diagnostics
        diagnostics = await push_service.get_apns_diagnostics()
        
        # Determine environment issues
        is_sandbox = diagnostics.get('configuration', {}).get('sandbox', False)
        
        environment_analysis = {
            "current_config": {
                "apns_environment": "sandbox" if is_sandbox else "production",
                "apns_server": "api.development.push.apple.com" if is_sandbox else "api.push.apple.com",
                "bundle_id": diagnostics.get('configuration', {}).get('bundle_id'),
                "key_id": diagnostics.get('configuration', {}).get('key_id'),
                "team_id": diagnostics.get('configuration', {}).get('team_id')
            },
            "troubleshooting": {
                "badDeviceToken_solutions": [
                    {
                        "scenario": "TestFlight App",
                        "issue": "TestFlight apps generate SANDBOX tokens but you're using PRODUCTION APNs",
                        "solution": "Use sandbox APNs for TestFlight apps",
                        "current_mismatch": not is_sandbox  # We're using production but TestFlight needs sandbox
                    },
                    {
                        "scenario": "App Store App", 
                        "issue": "App Store apps generate PRODUCTION tokens",
                        "solution": "Use production APNs for App Store apps",
                        "current_match": not is_sandbox  # We're using production which is correct
                    },
                    {
                        "scenario": "Development/Debug App",
                        "issue": "Development apps generate SANDBOX tokens",
                        "solution": "Use sandbox APNs for development apps", 
                        "current_mismatch": not is_sandbox
                    }
                ],
                "recommendations": []
            }
        }
        
        # Add specific recommendations based on current config
        if not is_sandbox:
            environment_analysis["troubleshooting"]["recommendations"] = [
                "✅ Currently configured for PRODUCTION APNs",
                "🎯 This works ONLY for App Store distributed apps",
                "⚠️  If using TestFlight, tokens will be INVALID (BadDeviceToken)",
                "⚠️  If using Development/Debug build, tokens will be INVALID",
                "💡 Verify your app distribution method:",
                "   - App Store: ✅ Current config is correct",
                "   - TestFlight: ❌ Need to use sandbox APNs",
                "   - Development: ❌ Need to use sandbox APNs"
            ]
        else:
            environment_analysis["troubleshooting"]["recommendations"] = [
                "✅ Currently configured for SANDBOX APNs",
                "🎯 This works for TestFlight and Development apps",
                "⚠️  App Store apps will get INVALID tokens with this config"
            ]
        
        return {
            "success": True,
            "data": environment_analysis
        }
        
    except Exception as e:
        logger.error(f"Error checking APNs environment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check environment: {str(e)}")

@router.get("/auto-setup-and-notify/{device_id}")
async def auto_setup_and_notify(device_id: str):
    """Automatically setup keywords and send real notifications (GET endpoint for easy testing)"""
    try:
        # Get user for this device
        user_query = """
            SELECT 
                dt.device_token,
                u.id as user_id,
                u.keywords,
                u.notifications_enabled
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="Device not found or inactive")
        
        user_data = user_result[0]
        user_id = user_data['user_id']
        device_token = user_data['device_token']
        current_keywords = user_data['keywords']
        
        # Setup keywords if not set
        keywords = ["iOS Developer", "Swift", "Mobile App", "iPhone", "React Native", "Apple"]
        
        if not current_keywords or not user_data['notifications_enabled']:
            # Update user with keywords and enable notifications
            update_query = """
                UPDATE iosapp.users 
                SET keywords = $1, notifications_enabled = true, updated_at = NOW()
                WHERE id = $2
            """
            
            import json
            await db_manager.execute_command(update_query, json.dumps(keywords), user_id)
        else:
            keywords = current_keywords
        
        # Get recent jobs and check for matches
        recent_jobs_query = """
            SELECT id, title, company, apply_link, source, created_at
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        jobs_result = await db_manager.execute_query(recent_jobs_query)
        
        if not jobs_result:
            return {
                "success": True,
                "message": "Setup complete, but no recent jobs found to check",
                "data": {
                    "device_id": device_id,
                    "keywords_set": keywords,
                    "jobs_checked": 0,
                    "matches_found": 0
                }
            }
        
        # Check for matches and send notifications
        from app.services.job_notification_service import JobNotificationService
        from app.services.push_notifications import PushNotificationService
        
        notification_service = JobNotificationService()
        push_service = PushNotificationService()
        
        matches_found = 0
        notifications_sent = 0
        job_matches = []
        
        for job in jobs_result:
            # Check if job matches keywords
            matched_keywords = notification_service._match_keywords(job, keywords)
            
            if matched_keywords:
                # Check if already notified
                job_unique_key = notification_service._generate_job_unique_key(job['title'], job['company'])
                
                already_notified_query = """
                    SELECT id FROM iosapp.job_notification_history
                    WHERE user_id = $1 AND job_unique_key = $2
                """
                already_notified = await db_manager.execute_query(already_notified_query, user_id, job_unique_key)
                
                if not already_notified:
                    matches_found += 1
                    job_matches.append({
                        "title": job['title'],
                        "company": job['company'],
                        "matched_keywords": matched_keywords
                    })
                    
                    # Record the notification
                    notification_id = await notification_service._record_notification(
                        user_id, job['id'], job['title'], job['company'], 
                        job.get('source'), job_unique_key, matched_keywords
                    )
                    
                    if notification_id:
                        # Send actual push notification
                        success = await push_service.send_job_match_notification(
                            device_token=device_token,
                            device_id=device_id,
                            job=job,
                            matched_keywords=matched_keywords,
                            match_id=notification_id
                        )
                        
                        if success:
                            notifications_sent += 1
                        
                        # Limit to 3 notifications at once
                        if notifications_sent >= 3:
                            break
        
        return {
            "success": True,
            "message": f"Setup complete! Found {matches_found} new job matches, sent {notifications_sent} notifications to your phone!",
            "data": {
                "device_id": device_id,
                "keywords_set": keywords,
                "jobs_checked": len(jobs_result),
                "matches_found": matches_found,
                "notifications_sent": notifications_sent,
                "job_matches": job_matches[:5],  # Show first 5 matches
                "mode": "REAL notifications sent to your phone!"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto setup and notify: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup and notify: {str(e)}")