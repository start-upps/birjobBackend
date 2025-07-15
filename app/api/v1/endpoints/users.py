"""
User management endpoints for device-based iOS app
Provides user profile, preferences, and account management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.core.database import db_manager
from app.utils.validation import validate_device_token, validate_keywords, validate_email
from app.services.analytics_service import analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class UserProfile(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    experience_level: Optional[str] = Field(None, description="Entry, Mid, Senior, Executive")
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    remote_preference: Optional[str] = Field(None, description="Remote, Hybrid, Onsite, Any")

class UserPreferences(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    preferred_sources: List[str] = Field(default_factory=list)
    notifications_enabled: bool = True
    notification_frequency: str = Field(default="real_time", description="real_time, daily, weekly")
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)

class UpdateProfileRequest(BaseModel):
    device_token: str
    profile: UserProfile

class UpdatePreferencesRequest(BaseModel):
    device_token: str
    preferences: UserPreferences

class DeleteAccountRequest(BaseModel):
    device_token: str
    confirmation: str  # User must type "DELETE" to confirm

@router.get("/profile/{device_token}")
async def get_user_profile(device_token: str):
    """Get user profile and preferences by device token"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device user
        device_query = """
            SELECT id, device_token, keywords, notifications_enabled, created_at
            FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(
                status_code=404,
                detail="Device not found. Please register first."
            )
        
        device_user = device_result[0]
        
        # Check if user has extended profile in users table (using JOIN)
        user_query = """
            SELECT u.id, u.email, u.first_name, u.last_name, u.phone, u.location, 
                   u.current_job_title, u.years_of_experience, u.linkedin_profile, 
                   u.portfolio_url, u.bio, u.desired_job_types, u.remote_work_preference,
                   u.skills, u.preferred_locations, u.min_salary, u.max_salary,
                   u.salary_currency, u.salary_negotiable, u.job_matches_enabled,
                   u.application_reminders_enabled, u.weekly_digest_enabled,
                   u.market_insights_enabled, u.quiet_hours_enabled, u.quiet_hours_start,
                   u.quiet_hours_end, u.preferred_notification_time, u.profile_visibility,
                   u.share_analytics, u.share_job_view_history, u.allow_personalized_recommendations,
                   u.profile_completeness, u.created_at, u.updated_at
            FROM iosapp.users u
            JOIN iosapp.device_users du ON u.device_id = du.id
            WHERE du.device_token = $1
        """
        user_result = await db_manager.execute_query(user_query, device_token)
        
        # Get user analytics summary
        analytics_query = """
            SELECT 
                COUNT(*) as total_actions,
                COUNT(CASE WHEN action = 'job_view' THEN 1 END) as jobs_viewed,
                COUNT(CASE WHEN action = 'notification_received' THEN 1 END) as notifications_received,
                COUNT(CASE WHEN action = 'chat_message' THEN 1 END) as chat_messages,
                MAX(created_at) as last_activity
            FROM iosapp.user_analytics
            WHERE device_id = $1
        """
        analytics = await db_manager.execute_query(analytics_query, device_user['id'])
        
        # Build response
        profile_data = {
            "device_id": str(device_user['id']),
            "device_token": device_user['device_token'],
            "registration_date": device_user['created_at'].isoformat(),
            "profile": {
                "name": None,
                "email": None,
                "location": None,
                "job_title": None,
                "experience_level": None,
                "salary_min": None,
                "salary_max": None,
                "remote_preference": None
            },
            "preferences": {
                "keywords": device_user['keywords'] or [],
                "preferred_sources": [],
                "notifications_enabled": device_user['notifications_enabled'],
                "notification_frequency": "real_time",
                "quiet_hours_start": None,
                "quiet_hours_end": None
            },
            "analytics": {
                "total_actions": analytics[0]['total_actions'] if analytics else 0,
                "jobs_viewed": analytics[0]['jobs_viewed'] if analytics else 0,
                "notifications_received": analytics[0]['notifications_received'] if analytics else 0,
                "chat_messages": analytics[0]['chat_messages'] if analytics else 0,
                "last_activity": analytics[0]['last_activity'].isoformat() if analytics and analytics[0]['last_activity'] else None
            }
        }
        
        # If user has extended profile, update with that data
        if user_result:
            user = user_result[0]
            profile_data["profile"].update({
                "name": user.get('name'),
                "email": user.get('email'),
                "location": user.get('location'),
                "job_title": user.get('job_title'),
                "experience_level": user.get('experience_level'),
                "salary_min": user.get('salary_min'),
                "salary_max": user.get('salary_max'),
                "remote_preference": user.get('remote_preference')
            })
            profile_data["preferences"].update({
                "keywords": user.get('keywords') or device_user['keywords'] or [],
                "preferred_sources": user.get('preferred_sources') or [],
                "notifications_enabled": user.get('notifications_enabled', device_user['notifications_enabled']),
                "notification_frequency": user.get('notification_frequency', 'real_time'),
                "quiet_hours_start": user.get('quiet_hours_start'),
                "quiet_hours_end": user.get('quiet_hours_end')
            })
        
        # Track analytics
        await analytics_service.track_action(
            device_id=device_user['id'],
            action="profile_view",
            metadata={"endpoint": "get_user_profile"}
        )
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )

@router.put("/profile")
async def update_user_profile(request: UpdateProfileRequest):
    """Update user profile information"""
    try:
        # Validate device token
        device_token = validate_device_token(request.device_token)
        
        # Validate email if provided
        if request.profile.email:
            request.profile.email = validate_email(request.profile.email)
        
        # Get device user
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(
                status_code=404,
                detail="Device not found. Please register first."
            )
        
        device_id = device_result[0]['id']
        
        # Check if user profile exists (using JOIN)
        user_check_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_users du ON u.device_id = du.id
            WHERE du.device_token = $1
        """
        existing_user = await db_manager.execute_query(user_check_query, device_token)
        
        if existing_user:
            # Update existing profile (using device_id)
            update_query = """
                UPDATE iosapp.users 
                SET first_name = $2, email = $3, location = $4, current_job_title = $5,
                    years_of_experience = $6, min_salary = $7, max_salary = $8,
                    remote_work_preference = $9, updated_at = NOW()
                WHERE device_id = $1
                RETURNING id
            """
            await db_manager.execute_command(
                update_query,
                device_id,
                request.profile.name,
                request.profile.email,
                request.profile.location,
                request.profile.job_title,
                request.profile.experience_level,
                request.profile.salary_min,
                request.profile.salary_max,
                request.profile.remote_preference
            )
        else:
            # Create new profile
            create_query = """
                INSERT INTO iosapp.users 
                (device_token, name, email, location, job_title, experience_level,
                 salary_min, salary_max, remote_preference, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                RETURNING id
            """
            await db_manager.execute_command(
                create_query,
                device_token,
                request.profile.name,
                request.profile.email,
                request.profile.location,
                request.profile.job_title,
                request.profile.experience_level,
                request.profile.salary_min,
                request.profile.salary_max,
                request.profile.remote_preference
            )
        
        # Track analytics
        await analytics_service.track_action(
            device_id=device_id,
            action="profile_update",
            metadata={"fields_updated": [k for k, v in request.profile.dict().items() if v is not None]}
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )

@router.put("/preferences")
async def update_user_preferences(request: UpdatePreferencesRequest):
    """Update user preferences and notification settings"""
    try:
        # Validate device token and keywords
        device_token = validate_device_token(request.device_token)
        keywords = validate_keywords(request.preferences.keywords)
        
        # Get device user
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(
                status_code=404,
                detail="Device not found. Please register first."
            )
        
        device_id = device_result[0]['id']
        
        # Update device user preferences
        device_update_query = """
            UPDATE iosapp.device_users 
            SET keywords = $2, notifications_enabled = $3
            WHERE device_token = $1
        """
        await db_manager.execute_command(
            device_update_query,
            device_token,
            keywords,
            request.preferences.notifications_enabled
        )
        
        # Update or create extended preferences in users table (using JOIN)
        user_check_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_users du ON u.device_id = du.id
            WHERE du.device_token = $1
        """
        existing_user = await db_manager.execute_query(user_check_query, device_token)
        
        if existing_user:
            # Update existing preferences
            preferences_update_query = """
                UPDATE iosapp.users 
                SET keywords = $2, preferred_sources = $3, notifications_enabled = $4,
                    notification_frequency = $5, quiet_hours_start = $6, quiet_hours_end = $7,
                    updated_at = NOW()
                WHERE device_token = $1
            """
            await db_manager.execute_command(
                preferences_update_query,
                device_token,
                keywords,
                request.preferences.preferred_sources,
                request.preferences.notifications_enabled,
                request.preferences.notification_frequency,
                request.preferences.quiet_hours_start,
                request.preferences.quiet_hours_end
            )
        else:
            # Create minimal user record for preferences
            create_preferences_query = """
                INSERT INTO iosapp.users 
                (device_token, keywords, preferred_sources, notifications_enabled,
                 notification_frequency, quiet_hours_start, quiet_hours_end, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
            """
            await db_manager.execute_command(
                create_preferences_query,
                device_token,
                keywords,
                request.preferences.preferred_sources,
                request.preferences.notifications_enabled,
                request.preferences.notification_frequency,
                request.preferences.quiet_hours_start,
                request.preferences.quiet_hours_end
            )
        
        # Track analytics
        await analytics_service.track_action(
            device_id=device_id,
            action="preferences_update",
            metadata={
                "keywords_count": len(keywords),
                "notifications_enabled": request.preferences.notifications_enabled,
                "notification_frequency": request.preferences.notification_frequency
            }
        )
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "updated_keywords": keywords,
            "notifications_enabled": request.preferences.notifications_enabled,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user preferences"
        )

@router.get("/activity/{device_token}")
async def get_user_activity(device_token: str, limit: int = 50, offset: int = 0):
    """Get user activity history"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device user
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
        
        device_id = device_result[0]['id']
        
        # Get user activity
        activity_query = """
            SELECT action, metadata, created_at
            FROM iosapp.user_analytics
            WHERE device_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        activities = await db_manager.execute_query(activity_query, device_id, limit, offset)
        
        # Get total count
        count_query = """
            SELECT COUNT(*) as total
            FROM iosapp.user_analytics
            WHERE device_id = $1
        """
        total_result = await db_manager.execute_query(count_query, device_id)
        total_count = total_result[0]['total'] if total_result else 0
        
        activity_list = []
        for activity in activities:
            activity_list.append({
                "action": activity['action'],
                "metadata": activity['metadata'] or {},
                "timestamp": activity['created_at'].isoformat()
            })
        
        return {
            "activities": activity_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(activity_list) < total_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user activity"
        )

@router.delete("/account")
async def delete_user_account(request: DeleteAccountRequest):
    """Delete user account and all associated data"""
    try:
        # Validate device token
        device_token = validate_device_token(request.device_token)
        
        # Verify confirmation
        if request.confirmation != "DELETE":
            raise HTTPException(
                status_code=400,
                detail="Account deletion requires confirmation string 'DELETE'"
            )
        
        # Get device user
        device_query = """
            SELECT id FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
        
        device_id = device_result[0]['id']
        
        # Delete all user data (cascading deletes will handle related records)
        # 1. Delete from users table (if exists) - using device_id
        await db_manager.execute_command(
            "DELETE FROM iosapp.users WHERE device_id = $1",
            device_id
        )
        
        # 2. Delete analytics (manual since no FK constraint)
        await db_manager.execute_command(
            "DELETE FROM iosapp.user_analytics WHERE device_id = $1",
            device_id
        )
        
        # 3. Delete notification hashes (has FK constraint, will cascade)
        # 4. Delete device user (this will cascade to notification_hashes)
        await db_manager.execute_command(
            "DELETE FROM iosapp.device_users WHERE device_token = $1",
            device_token
        )
        
        return {
            "success": True,
            "message": "Account deleted successfully. All user data has been removed.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user account"
        )

@router.get("/stats/{device_token}")
async def get_user_stats(device_token: str):
    """Get user statistics and insights"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device user
        device_query = """
            SELECT id, created_at FROM iosapp.device_users 
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(
                status_code=404,
                detail="Device not found"
            )
        
        device_id = device_result[0]['id']
        registration_date = device_result[0]['created_at']
        
        # Get comprehensive stats
        stats_query = """
            SELECT 
                COUNT(*) as total_actions,
                COUNT(CASE WHEN action = 'job_view' THEN 1 END) as jobs_viewed,
                COUNT(CASE WHEN action = 'notification_received' THEN 1 END) as notifications_received,
                COUNT(CASE WHEN action = 'chat_message' THEN 1 END) as chat_messages,
                COUNT(CASE WHEN action = 'job_application' THEN 1 END) as applications_tracked,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '7 days' THEN 1 END) as actions_last_7_days,
                COUNT(CASE WHEN created_at > NOW() - INTERVAL '30 days' THEN 1 END) as actions_last_30_days,
                MAX(created_at) as last_activity,
                MIN(created_at) as first_activity
            FROM iosapp.user_analytics
            WHERE device_id = $1
        """
        stats = await db_manager.execute_query(stats_query, device_id)
        
        # Get notification stats
        notification_stats_query = """
            SELECT 
                COUNT(*) as total_notifications,
                COUNT(DISTINCT job_source) as unique_sources,
                COUNT(CASE WHEN sent_at > NOW() - INTERVAL '7 days' THEN 1 END) as notifications_last_7_days,
                COUNT(CASE WHEN sent_at > NOW() - INTERVAL '30 days' THEN 1 END) as notifications_last_30_days
            FROM iosapp.notification_hashes
            WHERE device_id = $1
        """
        notification_stats = await db_manager.execute_query(notification_stats_query, device_id)
        
        # Calculate days since registration
        days_since_registration = (datetime.now(timezone.utc) - registration_date.replace(tzinfo=timezone.utc)).days
        
        stats_data = stats[0] if stats else {}
        notification_data = notification_stats[0] if notification_stats else {}
        
        return {
            "account": {
                "registration_date": registration_date.isoformat(),
                "days_since_registration": days_since_registration,
                "last_activity": stats_data.get('last_activity').isoformat() if stats_data.get('last_activity') else None
            },
            "activity": {
                "total_actions": stats_data.get('total_actions', 0),
                "jobs_viewed": stats_data.get('jobs_viewed', 0),
                "chat_messages": stats_data.get('chat_messages', 0),
                "applications_tracked": stats_data.get('applications_tracked', 0),
                "actions_last_7_days": stats_data.get('actions_last_7_days', 0),
                "actions_last_30_days": stats_data.get('actions_last_30_days', 0)
            },
            "notifications": {
                "total_received": notification_data.get('total_notifications', 0),
                "unique_sources": notification_data.get('unique_sources', 0),
                "last_7_days": notification_data.get('notifications_last_7_days', 0),
                "last_30_days": notification_data.get('notifications_last_30_days', 0)
            },
            "engagement": {
                "avg_actions_per_day": round(stats_data.get('total_actions', 0) / max(days_since_registration, 1), 2),
                "notification_engagement_rate": round(
                    (stats_data.get('jobs_viewed', 0) / max(notification_data.get('total_notifications', 1), 1)) * 100, 2
                )
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user stats"
        )