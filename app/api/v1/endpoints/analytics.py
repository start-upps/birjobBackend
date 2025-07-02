from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional
import logging
import json
from datetime import datetime, timedelta

from app.core.database import db_manager
from app.schemas.analytics import (
    AnalyticsEventRequest, AnalyticsEventResponse,
    UserAnalyticsResponse, AnalyticsStatsResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/event", response_model=AnalyticsEventResponse)
async def record_analytics_event(request: AnalyticsEventRequest):
    """Record a simple analytics event for a user"""
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
        
        # Insert analytics event
        insert_query = """
            INSERT INTO iosapp.user_analytics 
            (user_id, action_type, action_data, session_id, device_info)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, timestamp
        """
        
        result = await db_manager.execute_query(
            insert_query,
            user_id,
            request.action_type.value,
            json.dumps(request.action_data),
            request.session_id,
            json.dumps(request.device_info)
        )
        
        if result:
            event = result[0]
            return AnalyticsEventResponse(
                data={
                    "event_id": str(event["id"]),
                    "timestamp": event["timestamp"].isoformat(),
                    "user_id": str(user_id)
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to record analytics event")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording analytics event: {e}")
        raise HTTPException(status_code=500, detail="Failed to record analytics event")

@router.get("/user/{device_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    device_id: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
):
    """Get analytics summary for a specific user"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Get analytics summary for the user
        analytics_query = """
            SELECT 
                COUNT(*) as total_events,
                action_type,
                COUNT(*) as event_count,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM iosapp.user_analytics
            WHERE user_id = $1 
            AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
            GROUP BY action_type
            ORDER BY event_count DESC
        """ % days
        
        analytics_result = await db_manager.execute_query(analytics_query, user_id)
        
        # Process results
        total_events = 0
        events_by_type = {}
        first_event = None
        last_event = None
        
        for row in analytics_result:
            total_events += row["event_count"]
            events_by_type[row["action_type"]] = row["event_count"]
            
            if first_event is None or row["first_event"] < first_event:
                first_event = row["first_event"]
            if last_event is None or row["last_event"] > last_event:
                last_event = row["last_event"]
        
        return UserAnalyticsResponse(
            user_id=str(user_id),
            total_events=total_events,
            events_by_type=events_by_type,
            first_event=first_event,
            last_event=last_event,
            data={
                "analysis_period_days": days,
                "device_id": device_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user analytics")

@router.get("/stats", response_model=AnalyticsStatsResponse)
async def get_analytics_stats():
    """Get overall analytics statistics"""
    try:
        # Get overall stats
        stats_query = """
            SELECT 
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_events,
                action_type,
                COUNT(*) as action_count
            FROM iosapp.user_analytics
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            GROUP BY action_type
            ORDER BY action_count DESC
        """
        
        stats_result = await db_manager.execute_query(stats_query)
        
        total_events_24h = sum(row["action_count"] for row in stats_result)
        active_users_24h = stats_result[0]["active_users"] if stats_result else 0
        
        actions_24h = {}
        for row in stats_result:
            actions_24h[row["action_type"]] = row["action_count"]
        
        return AnalyticsStatsResponse(
            data={
                "last_24_hours": {
                    "active_users": active_users_24h,
                    "total_events": total_events_24h,
                    "events_by_type": actions_24h
                },
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics stats")

@router.delete("/user/{device_id}", response_model=AnalyticsEventResponse)
async def clear_user_analytics(device_id: str):
    """Clear analytics data for a specific user (GDPR compliance)"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found for device")
        
        user_id = user_result[0]["id"]
        
        # Delete analytics data
        delete_query = """
            DELETE FROM iosapp.user_analytics 
            WHERE user_id = $1
            RETURNING COUNT(*) as deleted_count
        """
        
        result = await db_manager.execute_query(delete_query, user_id)
        
        return AnalyticsEventResponse(
            message="User analytics data cleared successfully",
            data={"user_id": str(user_id), "device_id": device_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing user analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear user analytics")