from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import json

from app.core.database import db_manager
from app.schemas.analytics import (
    SessionStartRequest, SessionEndRequest, SessionResponse,
    UserActionRequest, UserActionResponse,
    SearchRequest, SearchResultsRequest, SearchClickRequest, SearchResponse,
    JobEngagementRequest, JobApplicationRequest, JobEngagementResponse,
    NotificationRequest, NotificationDeliveryRequest, NotificationEngagementRequest, NotificationResponse,
    AnalyticsOverviewResponse, UserEngagementResponse, JobAnalyticsResponse,
    SearchAnalyticsResponse, NotificationAnalyticsResponse, RealTimeResponse,
    DashboardMetrics, UserEngagementMetrics, JobEngagementMetrics,
    SearchAnalyticsMetrics, NotificationMetrics, RealTimeMetrics
)

router = APIRouter()
logger = logging.getLogger(__name__)

# =====================================
# Session Management (RDBMS with JOINs)
# =====================================

@router.post("/sessions/start", response_model=SessionResponse)
async def start_session(request: SessionStartRequest):
    """Start a new user session with RDBMS foreign key relationships"""
    try:
        # Find user via device_tokens relationship (RDBMS JOIN)
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Create session with foreign key relationship
        session_query = """
            INSERT INTO iosapp.user_sessions 
            (user_id, device_id, app_version, os_version)
            VALUES ($1, $2, $3, $4)
            RETURNING id, session_start
        """
        session_result = await db_manager.execute_query(
            session_query, user_id, request.device_id, request.app_version, request.os_version
        )
        
        if session_result:
            session = session_result[0]
            return SessionResponse(data={
                "session_id": str(session["id"]),
                "session_start": session["session_start"].isoformat(),
                "user_id": str(user_id)
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to start session")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")

@router.post("/sessions/end", response_model=SessionResponse)
async def end_session(request: SessionEndRequest):
    """End user session and calculate metrics with RDBMS relationships"""
    try:
        # Update session with end time and metrics
        update_query = """
            UPDATE iosapp.user_sessions 
            SET session_end = CURRENT_TIMESTAMP,
                duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - session_start)),
                actions_count = $1,
                jobs_viewed_count = $2,
                jobs_saved_count = $3,
                searches_performed = $4
            WHERE id = $5
            RETURNING id, session_end, duration_seconds
        """
        result = await db_manager.execute_query(
            update_query,
            request.actions_count,
            request.jobs_viewed_count,
            request.jobs_saved_count,
            request.searches_performed,
            request.session_id
        )
        
        if result:
            session = result[0]
            return SessionResponse(data={
                "session_id": request.session_id,
                "session_end": session["session_end"].isoformat(),
                "duration_seconds": int(session["duration_seconds"]) if session["duration_seconds"] else 0
            })
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")

# =====================================
# User Action Tracking (RDBMS with JOINs)
# =====================================

@router.post("/actions", response_model=UserActionResponse)
async def record_user_action(request: UserActionRequest):
    """Record user action with RDBMS foreign key relationships"""
    try:
        # Find user via device_tokens relationship (RDBMS JOIN)
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Record action with foreign key relationships
        action_query = """
            INSERT INTO iosapp.user_actions 
            (user_id, session_id, action_type, action_details, job_id, search_query, page_url, duration_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        action_result = await db_manager.execute_query(
            action_query,
            user_id,
            request.session_id,
            request.action_type.value,
            json.dumps(request.action_details),
            request.job_id,
            request.search_query,
            request.page_url,
            request.duration_seconds
        )
        
        if action_result:
            # Update session action count if session provided
            if request.session_id:
                await db_manager.execute_query(
                    "UPDATE iosapp.user_sessions SET actions_count = actions_count + 1 WHERE id = $1",
                    request.session_id
                )
            
            return UserActionResponse()
        else:
            raise HTTPException(status_code=500, detail="Failed to record action")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording user action: {e}")
        raise HTTPException(status_code=500, detail="Failed to record action")

# =====================================
# Search Analytics (RDBMS with JOINs)
# =====================================

@router.post("/search/start", response_model=SearchResponse)
async def record_search_start(request: SearchRequest):
    """Record search initiation with RDBMS relationships"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Normalize query (simple cleaning)
        normalized_query = request.search_query.lower().strip()
        
        # Record search with foreign key relationship
        search_query = """
            INSERT INTO iosapp.search_analytics 
            (user_id, search_query, normalized_query, filters_applied)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        search_result = await db_manager.execute_query(
            search_query,
            user_id,
            request.search_query,
            normalized_query,
            json.dumps(request.filters_applied)
        )
        
        if search_result:
            return SearchResponse(data={"search_id": str(search_result[0]["id"])})
        else:
            raise HTTPException(status_code=500, detail="Failed to record search")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording search: {e}")
        raise HTTPException(status_code=500, detail="Failed to record search")

@router.post("/search/results", response_model=SearchResponse)
async def record_search_results(request: SearchResultsRequest):
    """Update search with results information"""
    try:
        # Find and update the most recent search for this user and query
        update_query = """
            UPDATE iosapp.search_analytics sa
            SET results_count = $1,
                result_job_ids = $2,
                time_to_first_click = $3
            FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE sa.user_id = u.id 
            AND dt.device_id = $4 
            AND sa.search_query = $5
            AND sa.search_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY sa.search_timestamp DESC
            LIMIT 1
            RETURNING sa.id
        """
        
        result = await db_manager.execute_query(
            update_query,
            request.results_count,
            json.dumps(request.result_job_ids),
            request.time_to_first_click,
            request.device_id,
            request.search_query
        )
        
        if result:
            return SearchResponse(data={"updated": True})
        else:
            return SearchResponse(data={"updated": False, "message": "No recent search found"})
            
    except Exception as e:
        logger.error(f"Error updating search results: {e}")
        raise HTTPException(status_code=500, detail="Failed to update search results")

@router.post("/search/clicks", response_model=SearchResponse)
async def record_search_clicks(request: SearchClickRequest):
    """Record search result clicks with RDBMS relationships"""
    try:
        # Update search with click information
        update_query = """
            UPDATE iosapp.search_analytics sa
            SET clicked_results = $1,
                clicked_job_ids = $2,
                total_session_time = $3
            FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE sa.user_id = u.id 
            AND dt.device_id = $4 
            AND sa.search_query = $5
            AND sa.search_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
            ORDER BY sa.search_timestamp DESC
            LIMIT 1
            RETURNING sa.id
        """
        
        result = await db_manager.execute_query(
            update_query,
            len(request.clicked_job_ids),
            json.dumps(request.clicked_job_ids),
            request.total_session_time,
            request.device_id,
            request.search_query
        )
        
        if result:
            return SearchResponse(data={"updated": True})
        else:
            return SearchResponse(data={"updated": False, "message": "No recent search found"})
            
    except Exception as e:
        logger.error(f"Error updating search clicks: {e}")
        raise HTTPException(status_code=500, detail="Failed to update search clicks")

# =====================================
# Job Engagement Analytics (RDBMS with JOINs)
# =====================================

@router.post("/jobs/engagement", response_model=JobEngagementResponse)
async def record_job_engagement(request: JobEngagementRequest):
    """Record/update job engagement with RDBMS foreign key relationships"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Upsert job engagement record
        upsert_query = """
            INSERT INTO iosapp.job_engagement 
            (user_id, job_id, job_title, job_company, job_source, job_location, 
             total_view_time, view_count, first_viewed_at, last_viewed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, job_id) 
            DO UPDATE SET
                total_view_time = job_engagement.total_view_time + $7,
                view_count = job_engagement.view_count + 1,
                last_viewed_at = CURRENT_TIMESTAMP,
                job_title = COALESCE($3, job_engagement.job_title),
                job_company = COALESCE($4, job_engagement.job_company),
                job_source = COALESCE($5, job_engagement.job_source),
                job_location = COALESCE($6, job_engagement.job_location),
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, view_count, total_view_time
        """
        
        result = await db_manager.execute_query(
            upsert_query,
            user_id,
            request.job_id,
            request.job_title,
            request.job_company,
            request.job_source,
            request.job_location,
            request.view_duration_seconds
        )
        
        if result:
            engagement = result[0]
            
            # Calculate engagement score (simple algorithm)
            view_time_score = min(engagement["total_view_time"] / 60, 50)  # Max 50 points for view time
            view_count_score = min(engagement["view_count"] * 5, 30)       # Max 30 points for view count
            engagement_score = int(view_time_score + view_count_score)
            
            # Update engagement score
            await db_manager.execute_query(
                "UPDATE iosapp.job_engagement SET engagement_score = $1, last_calculated_at = CURRENT_TIMESTAMP WHERE id = $2",
                engagement_score, engagement["id"]
            )
            
            return JobEngagementResponse(data={
                "engagement_id": str(engagement["id"]),
                "view_count": engagement["view_count"],
                "total_view_time": engagement["total_view_time"],
                "engagement_score": engagement_score
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to record job engagement")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording job engagement: {e}")
        raise HTTPException(status_code=500, detail="Failed to record job engagement")

@router.post("/jobs/application", response_model=JobEngagementResponse)
async def record_job_application(request: JobApplicationRequest):
    """Record job application with RDBMS relationships"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Update job engagement with application info
        update_query = """
            UPDATE iosapp.job_engagement 
            SET applied = true,
                applied_at = CURRENT_TIMESTAMP,
                application_source = $1,
                engagement_score = LEAST(engagement_score + 20, 100),
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $2 AND job_id = $3
            RETURNING id, engagement_score
        """
        
        result = await db_manager.execute_query(
            update_query, request.application_source, user_id, request.job_id
        )
        
        if result:
            return JobEngagementResponse(data={
                "engagement_id": str(result[0]["id"]),
                "applied": True,
                "engagement_score": result[0]["engagement_score"]
            })
        else:
            # Create engagement record if it doesn't exist
            create_query = """
                INSERT INTO iosapp.job_engagement 
                (user_id, job_id, applied, applied_at, application_source, engagement_score)
                VALUES ($1, $2, true, CURRENT_TIMESTAMP, $3, 20)
                RETURNING id, engagement_score
            """
            create_result = await db_manager.execute_query(
                create_query, user_id, request.job_id, request.application_source
            )
            
            if create_result:
                return JobEngagementResponse(data={
                    "engagement_id": str(create_result[0]["id"]),
                    "applied": True,
                    "engagement_score": create_result[0]["engagement_score"]
                })
            else:
                raise HTTPException(status_code=500, detail="Failed to record job application")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording job application: {e}")
        raise HTTPException(status_code=500, detail="Failed to record job application")

# =====================================
# Analytics Dashboard (RDBMS JOINs)
# =====================================

@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview():
    """Get comprehensive analytics overview using RDBMS JOINs"""
    try:
        # Total users
        total_users_query = "SELECT COUNT(*) as count FROM iosapp.users"
        total_users_result = await db_manager.execute_query(total_users_query)
        total_users = total_users_result[0]["count"] if total_users_result else 0
        
        # Active users (last 24h, 7d, 30d) using JOINs
        active_users_query = """
            SELECT 
                COUNT(DISTINCT CASE WHEN us.session_start >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN u.id END) as active_24h,
                COUNT(DISTINCT CASE WHEN us.session_start >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN u.id END) as active_7d,
                COUNT(DISTINCT CASE WHEN us.session_start >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN u.id END) as active_30d
            FROM iosapp.users u
            LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
        """
        active_users_result = await db_manager.execute_query(active_users_query)
        active_users = active_users_result[0] if active_users_result else {
            "active_24h": 0, "active_7d": 0, "active_30d": 0
        }
        
        # Session metrics (last 24h)
        session_metrics_query = """
            SELECT 
                COUNT(*) as total_sessions,
                AVG(duration_seconds) as avg_duration
            FROM iosapp.user_sessions 
            WHERE session_start >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """
        session_result = await db_manager.execute_query(session_metrics_query)
        session_metrics = session_result[0] if session_result else {
            "total_sessions": 0, "avg_duration": 0
        }
        
        # Job interaction metrics (last 24h) using JOINs
        job_metrics_query = """
            SELECT 
                COUNT(DISTINCT jv.id) as total_views,
                COUNT(DISTINCT sj.id) as total_saves,
                COUNT(DISTINCT sa.id) as total_searches
            FROM iosapp.users u
            LEFT JOIN iosapp.job_views jv ON u.id = jv.user_id AND jv.viewed_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id AND sj.created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id AND sa.search_timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """
        job_result = await db_manager.execute_query(job_metrics_query)
        job_metrics = job_result[0] if job_result else {
            "total_views": 0, "total_saves": 0, "total_searches": 0
        }
        
        # Notification delivery rate (last 24h) using JOINs
        notification_query = """
            SELECT 
                COUNT(*) as total_sent,
                COUNT(CASE WHEN delivery_status = 'delivered' THEN 1 END) as delivered
            FROM iosapp.notification_analytics 
            WHERE sent_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """
        notification_result = await db_manager.execute_query(notification_query)
        notification_data = notification_result[0] if notification_result else {
            "total_sent": 0, "delivered": 0
        }
        
        delivery_rate = (notification_data["delivered"] / notification_data["total_sent"] * 100) if notification_data["total_sent"] > 0 else 0
        
        metrics = DashboardMetrics(
            total_users=total_users,
            active_users_24h=active_users["active_24h"],
            active_users_7d=active_users["active_7d"],
            active_users_30d=active_users["active_30d"],
            total_sessions_24h=session_metrics["total_sessions"],
            avg_session_duration=float(session_metrics["avg_duration"] or 0),
            total_job_views_24h=job_metrics["total_views"],
            total_job_saves_24h=job_metrics["total_saves"],
            total_searches_24h=job_metrics["total_searches"],
            notification_delivery_rate=round(delivery_rate, 2)
        )
        
        return AnalyticsOverviewResponse(data=metrics)
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics overview")

@router.get("/users/engagement", response_model=UserEngagementResponse)
async def get_user_engagement_analytics(
    limit: int = Query(default=50, ge=1, le=500),
    min_sessions: int = Query(default=1, ge=0)
):
    """Get user engagement analytics using RDBMS JOINs"""
    try:
        # Complex JOIN query for user engagement metrics
        query = """
            SELECT 
                u.id as user_id,
                u.email,
                u.created_at as user_since,
                COUNT(DISTINCT us.id) as total_sessions,
                COALESCE(SUM(us.duration_seconds), 0) as total_time_spent,
                COUNT(DISTINCT je.job_id) as unique_jobs_viewed,
                COUNT(DISTINCT sj.id) as total_jobs_saved,
                COUNT(DISTINCT sa.id) as total_searches,
                AVG(je.engagement_score) as avg_engagement_score,
                MAX(us.session_start) as last_active
            FROM iosapp.users u
            LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
            LEFT JOIN iosapp.job_engagement je ON u.id = je.user_id
            LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
            LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id
            GROUP BY u.id, u.email, u.created_at
            HAVING COUNT(DISTINCT us.id) >= $1
            ORDER BY total_time_spent DESC, total_sessions DESC
            LIMIT $2
        """
        
        result = await db_manager.execute_query(query, min_sessions, limit)
        
        engagement_data = []
        for row in result:
            engagement_data.append(UserEngagementMetrics(
                user_id=str(row["user_id"]),
                email=row["email"],
                user_since=row["user_since"],
                total_sessions=row["total_sessions"] or 0,
                total_time_spent=row["total_time_spent"] or 0,
                unique_jobs_viewed=row["unique_jobs_viewed"] or 0,
                total_jobs_saved=row["total_jobs_saved"] or 0,
                total_searches=row["total_searches"] or 0,
                avg_engagement_score=float(row["avg_engagement_score"]) if row["avg_engagement_score"] else None,
                last_active=row["last_active"]
            ))
        
        return UserEngagementResponse(data=engagement_data)
        
    except Exception as e:
        logger.error(f"Error getting user engagement analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user engagement analytics")

@router.get("/user/{device_id}", response_model=Dict[str, Any])
async def get_user_analytics(device_id: str):
    """Get detailed analytics for specific user using RDBMS JOINs"""
    try:
        # Find user and get comprehensive analytics using JOINs
        analytics_query = """
            SELECT 
                u.id as user_id,
                u.email,
                u.created_at as user_since,
                u.keywords,
                u.preferred_sources,
                COUNT(DISTINCT us.id) as total_sessions,
                COALESCE(SUM(us.duration_seconds), 0) as total_time_spent,
                COUNT(DISTINCT je.job_id) as unique_jobs_viewed,
                COUNT(DISTINCT sj.id) as total_jobs_saved,
                COUNT(DISTINCT sa.id) as total_searches,
                AVG(je.engagement_score) as avg_engagement_score,
                MAX(us.session_start) as last_active,
                COUNT(DISTINCT CASE WHEN je.applied = true THEN je.job_id END) as applications_submitted
            FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
            LEFT JOIN iosapp.job_engagement je ON u.id = je.user_id
            LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id
            LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
            GROUP BY u.id, u.email, u.created_at, u.keywords, u.preferred_sources
        """
        
        result = await db_manager.execute_query(analytics_query, device_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = result[0]
        
        # Get recent activity (last 7 days) using JOINs
        recent_activity_query = """
            SELECT 
                DATE(us.session_start) as date,
                COUNT(DISTINCT us.id) as sessions,
                SUM(us.duration_seconds) as time_spent,
                SUM(us.jobs_viewed_count) as jobs_viewed,
                SUM(us.jobs_saved_count) as jobs_saved,
                SUM(us.searches_performed) as searches_performed
            FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            JOIN iosapp.user_sessions us ON u.id = us.user_id
            WHERE dt.device_id = $1 
            AND dt.is_active = true
            AND us.session_start >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(us.session_start)
            ORDER BY date DESC
        """
        
        activity_result = await db_manager.execute_query(recent_activity_query, device_id)
        
        recent_activity = []
        for row in activity_result:
            recent_activity.append({
                "date": row["date"].isoformat(),
                "sessions": row["sessions"],
                "time_spent": row["time_spent"] or 0,
                "jobs_viewed": row["jobs_viewed"] or 0,
                "jobs_saved": row["jobs_saved"] or 0,
                "searches_performed": row["searches_performed"] or 0
            })
        
        # Get top engaged jobs using JOINs
        top_jobs_query = """
            SELECT 
                je.job_id,
                je.job_title,
                je.job_company,
                je.total_view_time,
                je.view_count,
                je.engagement_score,
                je.is_saved,
                je.applied
            FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            JOIN iosapp.job_engagement je ON u.id = je.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
            ORDER BY je.engagement_score DESC, je.total_view_time DESC
            LIMIT 10
        """
        
        top_jobs_result = await db_manager.execute_query(top_jobs_query, device_id)
        
        top_jobs = []
        for row in top_jobs_result:
            top_jobs.append({
                "job_id": row["job_id"],
                "job_title": row["job_title"],
                "job_company": row["job_company"],
                "total_view_time": row["total_view_time"],
                "view_count": row["view_count"],
                "engagement_score": row["engagement_score"],
                "is_saved": row["is_saved"],
                "applied": row["applied"]
            })
        
        return {
            "success": True,
            "data": {
                "user_profile": {
                    "user_id": str(user_data["user_id"]),
                    "email": user_data["email"],
                    "user_since": user_data["user_since"].isoformat(),
                    "keywords": user_data["keywords"] or [],
                    "preferred_sources": user_data["preferred_sources"] or [],
                    "account_age_days": (datetime.now() - user_data["user_since"]).days
                },
                "engagement_summary": {
                    "total_sessions": user_data["total_sessions"] or 0,
                    "total_time_spent": user_data["total_time_spent"] or 0,
                    "unique_jobs_viewed": user_data["unique_jobs_viewed"] or 0,
                    "total_jobs_saved": user_data["total_jobs_saved"] or 0,
                    "total_searches": user_data["total_searches"] or 0,
                    "applications_submitted": user_data["applications_submitted"] or 0,
                    "avg_engagement_score": float(user_data["avg_engagement_score"]) if user_data["avg_engagement_score"] else 0,
                    "last_active": user_data["last_active"].isoformat() if user_data["last_active"] else None
                },
                "recent_activity": recent_activity,
                "top_engaged_jobs": top_jobs
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analytics")

@router.get("/realtime", response_model=RealTimeResponse)
async def get_realtime_metrics():
    """Get real-time analytics metrics using RDBMS JOINs"""
    try:
        # Real-time metrics using JOINs
        realtime_query = """
            SELECT 
                COUNT(DISTINCT CASE WHEN us.session_start >= CURRENT_TIMESTAMP - INTERVAL '15 minutes' AND us.session_end IS NULL THEN u.id END) as active_users_now,
                COUNT(DISTINCT CASE WHEN us.session_start >= CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN us.id END) as sessions_last_hour,
                COUNT(DISTINCT CASE WHEN jv.viewed_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN jv.id END) as job_views_last_hour,
                COUNT(DISTINCT CASE WHEN sa.search_timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN sa.id END) as searches_last_hour,
                COUNT(DISTINCT CASE WHEN na.sent_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN na.id END) as notifications_sent_last_hour
            FROM iosapp.users u
            LEFT JOIN iosapp.user_sessions us ON u.id = us.user_id
            LEFT JOIN iosapp.job_views jv ON u.id = jv.user_id
            LEFT JOIN iosapp.search_analytics sa ON u.id = sa.user_id
            LEFT JOIN iosapp.notification_analytics na ON u.id = na.user_id
        """
        
        result = await db_manager.execute_query(realtime_query)
        
        if result:
            data = result[0]
            metrics = RealTimeMetrics(
                active_users_now=data["active_users_now"] or 0,
                sessions_last_hour=data["sessions_last_hour"] or 0,
                job_views_last_hour=data["job_views_last_hour"] or 0,
                searches_last_hour=data["searches_last_hour"] or 0,
                notifications_sent_last_hour=data["notifications_sent_last_hour"] or 0
            )
        else:
            metrics = RealTimeMetrics(
                active_users_now=0,
                sessions_last_hour=0,
                job_views_last_hour=0,
                searches_last_hour=0,
                notifications_sent_last_hour=0
            )
        
        return RealTimeResponse(data=metrics, timestamp=datetime.utcnow())
        
    except Exception as e:
        logger.error(f"Error getting realtime metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get realtime metrics")

# Legacy job analytics endpoints (simplified versions)
@router.get("/jobs/overview", response_model=Dict[str, Any])
async def get_jobs_overview():
    """Get overall job statistics from scraper database"""
    try:
        total_query = "SELECT COUNT(*) as count FROM scraper.jobs_jobpost"
        total_result = await db_manager.execute_query(total_query)
        total_jobs = total_result[0]["count"] if total_result else 0
        
        return {
            "total_jobs": total_jobs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting jobs overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jobs overview")