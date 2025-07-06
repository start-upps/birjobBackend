from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict, Any, Optional
import logging

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
        
        # Use device token as device_id if no specific device_id provided
        device_id = device_token
        
        # Create or update device token
        device_query = """
            SELECT id, user_id FROM iosapp.device_tokens 
            WHERE device_token = $1 OR device_id = $2
        """
        device_result = await db_manager.execute_query(device_query, device_token, device_id)
        
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
        raise HTTPException(status_code=500, detail="Failed to register push token")

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
                if row['notification_sent_at'] > datetime.fromisoformat(notifications_map[group_key]['created_at'].replace('Z', '+00:00').replace('+00:00', '')):
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