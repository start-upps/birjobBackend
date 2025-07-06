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
    JobNotificationTriggerRequest, JobNotificationTriggerResponse
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