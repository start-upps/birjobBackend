from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime, timezone

from app.core.database import db_manager
from app.core.redis_client import redis_client
from app.services.match_engine import JobMatchEngine

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", response_model=Dict[str, Any])
async def health_check():
    """System health check endpoint"""
    try:
        # Check database connection
        db_healthy = True
        try:
            await db_manager.execute_query("SELECT 1")
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_healthy = False
        
        # Check Redis connection
        redis_healthy = True
        try:
            await redis_client.set("health_check", "ok", expire=60)
            await redis_client.get("health_check")
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_healthy = False
        
        # Check APNs (simplified check - could be expanded)
        apns_healthy = True  # TODO: Implement actual APNs health check
        
        # Check scraper health (check if there are recent jobs)
        scraper_healthy = True
        try:
            recent_jobs = await db_manager.execute_query(
                "SELECT COUNT(*) as count FROM scraper.jobs_jobpost WHERE created_at > NOW() - INTERVAL '8 hours'"
            )
            if recent_jobs and recent_jobs[0]['count'] == 0:
                scraper_healthy = False
        except Exception as e:
            logger.error(f"Scraper health check failed: {e}")
            scraper_healthy = False
        
        # Get metrics
        metrics = await get_system_metrics()
        
        # Overall health status
        overall_healthy = all([db_healthy, redis_healthy, apns_healthy, scraper_healthy])
        status_text = "healthy" if overall_healthy else "unhealthy"
        
        return {
            "status": status_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "redis": "healthy" if redis_healthy else "unhealthy", 
                "apns": "healthy" if apns_healthy else "unhealthy",
                "scraper": "healthy" if scraper_healthy else "unhealthy"
            },
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@router.get("/status/scraper", response_model=Dict[str, Any])
async def scraper_status():
    """Detailed scraper status and statistics"""
    try:
        # Get scraper statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_jobs_24h,
                COUNT(DISTINCT source) as active_sources
            FROM scraper.jobs_jobpost 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """
        stats = await db_manager.execute_query(stats_query)
        
        # Get per-source statistics
        sources_query = """
            SELECT 
                source,
                COUNT(*) as jobs_count,
                MAX(created_at) as last_scrape
            FROM scraper.jobs_jobpost 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY source
            ORDER BY jobs_count DESC
        """
        sources = await db_manager.execute_query(sources_query)
        
        source_data = []
        for source in sources:
            source_data.append({
                "name": source["source"],
                "status": "healthy",  # Could be enhanced with actual health checks
                "last_successful_scrape": source["last_scrape"].isoformat() if source["last_scrape"] else None,
                "jobs_scraped_last_run": source["jobs_count"],
                "error_count_24h": 0  # TODO: Implement error tracking
            })
        
        return {
            "status": "running",
            "last_run": None,  # TODO: Add last run timestamp
            "next_run": None,  # TODO: Add next run timestamp
            "sources": source_data,
            "total_jobs_last_24h": stats[0]["total_jobs_24h"] if stats else 0,
            "errors_last_24h": 0  # TODO: Implement error tracking
        }
        
    except Exception as e:
        logger.error(f"Scraper status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scraper status"
        )

async def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics for health check"""
    try:
        # Get active devices count
        active_devices_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.device_tokens 
            WHERE is_active = true
        """
        active_devices = await db_manager.execute_query(active_devices_query)
        
        # Get active subscriptions count
        active_subs_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.keyword_subscriptions 
            WHERE is_active = true
        """
        active_subs = await db_manager.execute_query(active_subs_query)
        
        # Get matches in last 24h
        matches_24h_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.job_matches 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """
        matches_24h = await db_manager.execute_query(matches_24h_query)
        
        # Get notifications sent in last 24h
        notifications_24h_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.push_notifications 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            AND status = 'sent'
        """
        notifications_24h = await db_manager.execute_query(notifications_24h_query)
        
        return {
            "active_devices": active_devices[0]["count"] if active_devices else 0,
            "active_subscriptions": active_subs[0]["count"] if active_subs else 0,
            "matches_last_24h": matches_24h[0]["count"] if matches_24h else 0,
            "notifications_sent_last_24h": notifications_24h[0]["count"] if notifications_24h else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {
            "active_devices": 0,
            "active_subscriptions": 0,
            "matches_last_24h": 0,
            "notifications_sent_last_24h": 0
        }

@router.post("/trigger-matching")
async def trigger_match_engine():
    """Manually trigger the job matching engine for testing"""
    try:
        logger.info("Manually triggering match engine...")
        
        engine = JobMatchEngine()
        await engine.process_new_jobs()
        
        # Get updated match count
        matches_count = await db_manager.execute_query("""
            SELECT COUNT(*) as count 
            FROM iosapp.job_matches 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        
        recent_matches = matches_count[0]["count"] if matches_count else 0
        
        logger.info(f"Match engine completed. Recent matches: {recent_matches}")
        
        return {
            "message": "Match engine triggered successfully", 
            "matches_created_last_hour": recent_matches,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger match engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger match engine: {str(e)}"
        )

@router.get("/scheduler-status")
async def get_scheduler_status():
    """Check if the background scheduler is running"""
    try:
        from app.services.match_engine import job_scheduler
        
        return {
            "scheduler_running": job_scheduler.running,
            "interval_minutes": job_scheduler.interval_minutes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scheduler status: {str(e)}"
        )