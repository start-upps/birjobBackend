"""
Minimal notification endpoints for device-based system
Hash-based deduplication for scraped jobs
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime

from app.core.database import db_manager
from app.services.minimal_notification_service import minimal_notification_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-all")
async def process_all_job_notifications(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Process ALL current jobs in database for notifications
    Efficient backend-based processing for GitHub Actions
    """
    try:
        trigger_source = request.get("trigger_source", "manual")
        run_in_background = request.get("background", True)
        
        logger.info(f"Processing all jobs for notifications (triggered by: {trigger_source})")
        
        # Get all jobs from database efficiently
        jobs_query = """
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at as posted_at
            FROM scraper.jobs_jobpost
            ORDER BY created_at DESC
        """
        
        jobs_result = await db_manager.execute_query(jobs_query)
        jobs_count = len(jobs_result)
        
        if jobs_count == 0:
            return {
                "success": True,
                "message": "No jobs found in database",
                "stats": {
                    "processed_jobs": 0,
                    "matched_devices": 0,
                    "notifications_sent": 0,
                    "errors": 0
                }
            }
        
        # Convert to format expected by notification service
        jobs_data = []
        for job in jobs_result:
            jobs_data.append({
                "id": job['id'],
                "title": job['title'] or "No Title",
                "company": job['company'] or "Unknown Company",
                "apply_link": job['apply_link'] or "",
                "source": job['source'] or "Unknown",
                "posted_at": job['posted_at'].isoformat() if job['posted_at'] else None
            })
        
        logger.info(f"Found {jobs_count} jobs to process")
        
        if run_in_background:
            # Run in background
            background_tasks.add_task(
                minimal_notification_service.process_job_notifications,
                jobs_data, None, False
            )
            
            return {
                "success": True,
                "message": f"Processing {jobs_count} jobs in background",
                "stats": {
                    "processed_jobs": jobs_count,
                    "matched_devices": "processing",
                    "notifications_sent": "processing",
                    "errors": 0
                }
            }
        else:
            # Run synchronously for GitHub Actions
            stats = await minimal_notification_service.process_job_notifications(
                jobs_data, None, False
            )
            
            return {
                "success": True,
                "message": f"Processed {jobs_count} jobs successfully",
                "stats": stats
            }
            
    except Exception as e:
        logger.error(f"Error processing all job notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process notifications: {str(e)}")

@router.post("/process-jobs")
async def process_job_notifications(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Process job notifications from scraper data
    Works with truncate/load approach
    """
    try:
        jobs = request.get("jobs", [])
        source_filter = request.get("source_filter")  # Optional: 'linkedin', 'indeed', etc.
        dry_run = request.get("dry_run", False)
        run_in_background = request.get("background", True)
        
        if not jobs:
            raise HTTPException(status_code=400, detail="jobs array is required")
        
        if not isinstance(jobs, list):
            raise HTTPException(status_code=400, detail="jobs must be an array")
        
        logger.info(f"Received {len(jobs)} jobs for notification processing")
        
        if run_in_background and not dry_run:
            # Run in background
            background_tasks.add_task(
                minimal_notification_service.process_job_notifications,
                jobs, source_filter, dry_run
            )
            
            return {
                "success": True,
                "message": f"Processing {len(jobs)} jobs in background",
                "jobs_queued": len(jobs),
                "dry_run": dry_run,
                "source_filter": source_filter
            }
        else:
            # Run synchronously (for dry runs or immediate results)
            stats = await minimal_notification_service.process_job_notifications(
                jobs, source_filter, dry_run
            )
            
            return {
                "success": True,
                "message": "Job notification processing completed",
                "stats": stats,
                "dry_run": dry_run
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_job_notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process jobs: {str(e)}")

@router.post("/send-single")
async def send_single_job_notification(request: Dict[str, Any]):
    """Send notification for a single job to matching devices"""
    try:
        job = request.get("job")
        if not job:
            raise HTTPException(status_code=400, detail="job object is required")
        
        # Process single job
        stats = await minimal_notification_service.process_job_notifications([job])
        
        return {
            "success": True,
            "message": "Single job notification processed",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending single notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.get("/stats")
async def get_notification_statistics():
    """Get notification system statistics"""
    try:
        stats = await minimal_notification_service.get_notification_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/test-device/{device_token}")
async def test_device_notification(device_token: str):
    """Send test notification to specific device"""
    try:
        from app.utils.validation import validate_device_token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id, keywords FROM iosapp.device_users
            WHERE device_token = $1 AND notifications_enabled = true
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or notifications disabled")
        
        device_id = str(device_result[0]['id'])
        keywords = device_result[0]['keywords']
        
        # Create test job
        test_job = {
            "id": 999999,
            "title": "Test iOS Developer Position",
            "company": "Test Company Inc.",
            "source": "test",
            "description": f"Test job matching your keywords: {keywords}"
        }
        
        # Send test notification
        success = await minimal_notification_service.send_job_notification(
            device_token, device_id, test_job, ["test"]
        )
        
        if success:
            # Record test notification
            job_hash = minimal_notification_service.generate_job_hash(
                test_job["title"], test_job["company"]
            )
            await minimal_notification_service.record_notification_sent(
                device_id, job_hash, test_job["title"], 
                test_job["company"], "test", ["test"]
            )
        
        return {
            "success": success,
            "message": "Test notification sent!" if success else "Failed to send test notification",
            "device_id": device_id,
            "test_job": test_job
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test: {str(e)}")

@router.delete("/cleanup")
async def cleanup_old_notifications(days_old: int = 30):
    """Clean up old notification hashes"""
    try:
        if days_old < 1 or days_old > 365:
            raise HTTPException(status_code=400, detail="days_old must be between 1 and 365")
        
        deleted_count = await minimal_notification_service.cleanup_old_notification_hashes(days_old)
        
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
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")

@router.get("/hash/{job_title}/{company}")
async def generate_job_hash_endpoint(job_title: str, company: str):
    """Generate job hash for testing deduplication"""
    try:
        job_hash = minimal_notification_service.generate_job_hash(job_title, company)
        
        return {
            "success": True,
            "data": {
                "job_title": job_title,
                "company": company,
                "hash": job_hash,
                "hash_length": len(job_hash)
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating hash: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate hash: {str(e)}")

@router.get("/devices/active")
async def get_active_devices():
    """Get list of active devices for testing"""
    try:
        devices = await minimal_notification_service.get_active_devices_with_keywords()
        
        # Sanitize device tokens for security
        sanitized_devices = []
        for device in devices:
            sanitized_devices.append({
                "device_id": device["device_id"],
                "device_token_preview": device["device_token"][:16] + "...",
                "keywords_count": len(device["keywords"]),
                "keywords": device["keywords"][:5]  # First 5 keywords only
            })
        
        return {
            "success": True,
            "data": {
                "active_devices_count": len(devices),
                "devices": sanitized_devices
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting active devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get devices: {str(e)}")

@router.post("/scraper-webhook")
async def scraper_webhook(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint for scraper to trigger notifications
    Called after scraper finishes truncate/load cycle
    """
    try:
        # Get jobs from scraper database
        source = request.get("source")  # linkedin, indeed, etc.
        limit = request.get("limit", 1000)  # Limit for testing
        
        logger.info(f"Scraper webhook triggered for source: {source}")
        
        # Query recent jobs from scraper schema
        jobs_query = """
            SELECT id, title, company, source, created_at
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '1 day'
        """
        
        # Add source filter if specified
        if source:
            jobs_query += f" AND source = '{source}'"
        
        jobs_query += f" ORDER BY created_at DESC LIMIT {limit}"
        
        jobs_result = await db_manager.execute_query(jobs_query)
        
        if not jobs_result:
            return {
                "success": True,
                "message": "No recent jobs found to process",
                "jobs_found": 0
            }
        
        # Convert to list of dicts
        jobs = [dict(job) for job in jobs_result]
        
        # Process in background
        background_tasks.add_task(
            minimal_notification_service.process_job_notifications,
            jobs, source, False  # Not dry run
        )
        
        return {
            "success": True,
            "message": f"Processing {len(jobs)} recent jobs from {source or 'all sources'}",
            "jobs_queued": len(jobs),
            "source": source
        }
        
    except Exception as e:
        logger.error(f"Error in scraper webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook failed: {str(e)}")