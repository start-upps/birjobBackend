from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime, timezone

from app.core.database import db_manager, check_db_health, engine, AsyncSessionLocal
from app.core.redis_client import redis_client
# from app.services.match_engine import JobMatchEngine  # Disabled - complex dependencies
from app.core.config import settings
from sqlalchemy import text

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=Dict[str, Any])
async def detailed_health_status():
    """Detailed system health status endpoint"""
    return await health_check()

@router.get("", response_model=Dict[str, Any])
async def health_check():
    """System health check endpoint"""
    try:
        # Check database connection using improved health check
        db_health_result = await check_db_health()
        db_healthy = db_health_result["status"] == "healthy"
        if not db_healthy:
            logger.error(f"Database health check failed: {db_health_result['message']}")
        
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
        
        # Overall health status - Core services only (scraper is external dependency)
        core_services_healthy = all([db_healthy, redis_healthy, apns_healthy])
        overall_healthy = core_services_healthy
        
        # Determine status text
        if overall_healthy:
            status_text = "healthy"
        elif core_services_healthy and not scraper_healthy:
            status_text = "healthy"  # Core services working, scraper issue doesn't affect backend
        else:
            status_text = "unhealthy"
        
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
            FROM iosapp.device_users 
            WHERE notifications_enabled = true
        """
        active_devices = await db_manager.execute_query(active_devices_query)
        
        # Get active subscriptions count (simplified - count users with keywords)
        active_subs_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.device_users 
            WHERE jsonb_array_length(keywords) > 0 AND notifications_enabled = true
        """
        active_subs = await db_manager.execute_query(active_subs_query)
        
        # Get notifications sent in last 24h (using notification_hashes table)
        notifications_24h_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.notification_hashes 
            WHERE sent_at > NOW() - INTERVAL '24 hours'
        """
        notifications_24h = await db_manager.execute_query(notifications_24h_query)
        
        # Get user analytics events in last 24h (simplified metrics)
        analytics_24h_query = """
            SELECT COUNT(*) as count 
            FROM iosapp.user_analytics 
            WHERE created_at > NOW() - INTERVAL '24 hours'
        """
        analytics_24h = await db_manager.execute_query(analytics_24h_query)
        
        return {
            "active_devices": active_devices[0]["count"] if active_devices else 0,
            "active_subscriptions": active_subs[0]["count"] if active_subs else 0,
            "matches_last_24h": analytics_24h[0]["count"] if analytics_24h else 0,
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

# Match engine endpoints disabled in simplified version
# @router.post("/trigger-matching")
# @router.get("/scheduler-status")


@router.post("/fix-device-token-length")
async def fix_device_token_length():
    """Fix device_token column to support longer tokens (64, 128, 160 chars)"""
    try:
        # Alter the device_token column to support longer tokens
        alter_query = """
            ALTER TABLE iosapp.device_users 
            ALTER COLUMN device_token TYPE VARCHAR(160);
        """
        
        await db_manager.execute_command(alter_query)
        
        return {
            "success": True,
            "message": "device_token column updated to support 160 characters",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating device_token column: {e}")
        return {
            "success": False,
            "message": f"Failed to update column: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/add-privacy-consent")
async def add_privacy_consent_fields():
    """Add privacy consent fields to device_users table for GDPR compliance"""
    try:
        # Add analytics consent fields
        alter_queries = [
            """
            ALTER TABLE iosapp.device_users 
            ADD COLUMN IF NOT EXISTS analytics_consent BOOLEAN DEFAULT false;
            """,
            """
            ALTER TABLE iosapp.device_users 
            ADD COLUMN IF NOT EXISTS consent_date TIMESTAMP WITH TIME ZONE;
            """,
            """
            ALTER TABLE iosapp.device_users 
            ADD COLUMN IF NOT EXISTS privacy_policy_version VARCHAR(10) DEFAULT '1.0';
            """
        ]
        
        for query in alter_queries:
            await db_manager.execute_command(query)
        
        return {
            "success": True,
            "message": "Privacy consent fields added successfully",
            "fields_added": [
                "analytics_consent (BOOLEAN DEFAULT false)",
                "consent_date (TIMESTAMP WITH TIME ZONE)",
                "privacy_policy_version (VARCHAR(10) DEFAULT '1.0')"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding privacy consent fields: {e}")
        return {
            "success": False,
            "message": f"Failed to add privacy fields: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/fix-privacy-policy-version-length")
async def fix_privacy_policy_version_length():
    """Fix privacy_policy_version column to support longer values like 'data_deleted'"""
    try:
        # Alter the privacy_policy_version column to support longer values
        alter_query = """
            ALTER TABLE iosapp.device_users 
            ALTER COLUMN privacy_policy_version TYPE VARCHAR(50);
        """
        
        await db_manager.execute_command(alter_query)
        
        return {
            "success": True,
            "message": "privacy_policy_version column updated to support 50 characters",
            "previous_limit": "10 characters",
            "new_limit": "50 characters",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating privacy_policy_version column: {e}")
        return {
            "success": False,
            "message": f"Failed to update column: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.get("/db-debug")
async def debug_database_connection():
    """Debug database connection issues with detailed information"""
    try:
        from app.core.database import engine, AsyncSessionLocal
        import sqlalchemy
        
        # Test engine connection
        engine_test = None
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test, NOW() as current_time"))
                row = result.fetchone()  # Remove await - fetchone() is not async for Result objects
                engine_test = {
                    "status": "success",
                    "test_value": row.test if row else None,
                    "server_time": row.current_time.isoformat() if row and row.current_time else None
                }
        except Exception as e:
            engine_test = {"status": "failed", "error": str(e), "error_type": type(e).__name__}
        
        # Test session creation
        session_test = None
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT version() as db_version"))
                row = result.fetchone()
                session_test = {
                    "status": "success",
                    "db_version": row.db_version if row else None
                }
        except Exception as e:
            session_test = {"status": "failed", "error": str(e), "error_type": type(e).__name__}
        
        # Get connection pool info
        pool_info = {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
        }
        
        return {
            "database_url_status": "configured" if settings.DATABASE_URL else "missing",
            "sqlalchemy_version": sqlalchemy.__version__,
            "engine_test": engine_test,
            "session_test": session_test,
            "pool_info": pool_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database debug failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database debug failed: {str(e)}"
        )