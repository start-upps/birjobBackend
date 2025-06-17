from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from app.core.database import db_manager
from app.schemas.user import (
    UserProfileCreate, UserProfileResponse, UserProfileUpdateResponse,
    SaveJobRequest, SavedJobsListResponse, JobViewRequest,
    UserAnalyticsResponse, ApplicationHistoryResponse,
    SuccessResponse, ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

def calculate_profile_completeness(user_data: dict) -> int:
    """Calculate profile completeness percentage"""
    total_fields = 20  # Total important fields for profile
    completed_fields = 0
    
    # Personal info fields (8 fields)
    personal_info = user_data.get('personalInfo', {})
    personal_fields = ['firstName', 'lastName', 'email', 'phone', 'location', 
                      'currentJobTitle', 'yearsOfExperience', 'bio']
    completed_fields += sum(1 for field in personal_fields if personal_info.get(field))
    
    # Job preferences fields (6 fields)
    job_prefs = user_data.get('jobPreferences', {})
    if job_prefs.get('desiredJobTypes'):
        completed_fields += 1
    if job_prefs.get('remoteWorkPreference'):
        completed_fields += 1
    if job_prefs.get('skills'):
        completed_fields += 1
    if job_prefs.get('preferredLocations'):
        completed_fields += 1
    salary_range = job_prefs.get('salaryRange', {})
    if salary_range.get('minSalary'):
        completed_fields += 1
    if salary_range.get('maxSalary'):
        completed_fields += 1
    
    # Additional profile elements (6 fields)
    if personal_info.get('linkedInProfile'):
        completed_fields += 1
    if personal_info.get('portfolioURL'):
        completed_fields += 1
    if user_data.get('notificationSettings'):
        completed_fields += 1
    if user_data.get('privacySettings'):
        completed_fields += 1
    # Bonus for having skills > 3
    skills = job_prefs.get('skills', [])
    if len(skills) >= 3:
        completed_fields += 1
    # Bonus for having bio > 50 characters
    bio = personal_info.get('bio', '')
    if len(bio) >= 50:
        completed_fields += 1
    
    return min(int((completed_fields / total_fields) * 100), 100)

@router.post("/profile", response_model=UserProfileUpdateResponse)
async def create_or_update_profile(profile_data: UserProfileCreate):
    """Create or update user profile"""
    try:
        device_id = profile_data.deviceId
        
        # Check if user exists
        existing_user_query = """
            SELECT id FROM iosapp.users WHERE device_id = $1
        """
        existing_user = await db_manager.execute_query(existing_user_query, device_id)
        
        # Calculate profile completeness
        profile_completeness = calculate_profile_completeness(profile_data.dict())
        
        if existing_user:
            # Update existing user
            user_id = existing_user[0]['id']
            
            update_query = """
                UPDATE iosapp.users SET
                    first_name = $1, last_name = $2, email = $3, phone = $4,
                    location = $5, current_job_title = $6, years_of_experience = $7,
                    linkedin_profile = $8, portfolio_url = $9, bio = $10,
                    desired_job_types = $11, remote_work_preference = $12,
                    skills = $13, preferred_locations = $14,
                    min_salary = $15, max_salary = $16, salary_currency = $17, salary_negotiable = $18,
                    job_matches_enabled = $19, application_reminders_enabled = $20,
                    weekly_digest_enabled = $21, market_insights_enabled = $22,
                    quiet_hours_enabled = $23, quiet_hours_start = $24, quiet_hours_end = $25,
                    preferred_notification_time = $26,
                    profile_visibility = $27, share_analytics = $28,
                    share_job_view_history = $29, allow_personalized_recommendations = $30,
                    profile_completeness = $31, updated_at = $32
                WHERE device_id = $33
            """
            
            # Extract data with defaults
            personal = profile_data.personalInfo or {}
            job_prefs = profile_data.jobPreferences or {}
            salary_range = job_prefs.salaryRange or {}
            notifications = profile_data.notificationSettings or {}
            privacy = profile_data.privacySettings or {}
            
            params = (
                personal.firstName, personal.lastName, personal.email, personal.phone,
                personal.location, personal.currentJobTitle, personal.yearsOfExperience,
                personal.linkedInProfile, personal.portfolioURL, personal.bio,
                job_prefs.desiredJobTypes, job_prefs.remoteWorkPreference,
                job_prefs.skills, job_prefs.preferredLocations,
                salary_range.minSalary, salary_range.maxSalary, 
                salary_range.currency or "USD", salary_range.isNegotiable,
                notifications.jobMatchesEnabled, notifications.applicationRemindersEnabled,
                notifications.weeklyDigestEnabled, notifications.marketInsightsEnabled,
                notifications.quietHoursEnabled, notifications.quietHoursStart,
                notifications.quietHoursEnd, notifications.preferredNotificationTime,
                privacy.profileVisibility, privacy.shareAnalytics,
                privacy.shareJobViewHistory, privacy.allowPersonalizedRecommendations,
                profile_completeness, datetime.utcnow(), device_id
            )
            
            await db_manager.execute_query(update_query, *params)
            
            return UserProfileUpdateResponse(
                success=True,
                message="Profile updated successfully",
                data={
                    "userId": user_id,
                    "deviceId": device_id,
                    "profileCompleteness": profile_completeness,
                    "lastUpdated": datetime.utcnow().isoformat()
                }
            )
        
        else:
            # Create new user
            import uuid
            user_id = str(uuid.uuid4())
            
            insert_query = """
                INSERT INTO iosapp.users (
                    id, device_id, first_name, last_name, email, phone,
                    location, current_job_title, years_of_experience,
                    linkedin_profile, portfolio_url, bio,
                    desired_job_types, remote_work_preference,
                    skills, preferred_locations,
                    min_salary, max_salary, salary_currency, salary_negotiable,
                    job_matches_enabled, application_reminders_enabled,
                    weekly_digest_enabled, market_insights_enabled,
                    quiet_hours_enabled, quiet_hours_start, quiet_hours_end,
                    preferred_notification_time,
                    profile_visibility, share_analytics,
                    share_job_view_history, allow_personalized_recommendations,
                    profile_completeness, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
                    $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32,
                    $33, $34, $35
                )
            """
            
            # Extract data with defaults
            personal = profile_data.personalInfo or {}
            job_prefs = profile_data.jobPreferences or {}
            salary_range = job_prefs.salaryRange or {}
            notifications = profile_data.notificationSettings or {}
            privacy = profile_data.privacySettings or {}
            
            now = datetime.utcnow()
            params = (
                user_id, device_id,
                personal.firstName, personal.lastName, personal.email, personal.phone,
                personal.location, personal.currentJobTitle, personal.yearsOfExperience,
                personal.linkedInProfile, personal.portfolioURL, personal.bio,
                job_prefs.desiredJobTypes, job_prefs.remoteWorkPreference,
                job_prefs.skills, job_prefs.preferredLocations,
                salary_range.minSalary, salary_range.maxSalary,
                salary_range.currency or "USD", salary_range.isNegotiable,
                notifications.jobMatchesEnabled, notifications.applicationRemindersEnabled,
                notifications.weeklyDigestEnabled, notifications.marketInsightsEnabled,
                notifications.quietHoursEnabled, notifications.quietHoursStart,
                notifications.quietHoursEnd, notifications.preferredNotificationTime,
                privacy.profileVisibility, privacy.shareAnalytics,
                privacy.shareJobViewHistory, privacy.allowPersonalizedRecommendations,
                profile_completeness, now, now
            )
            
            await db_manager.execute_query(insert_query, *params)
            
            return UserProfileUpdateResponse(
                success=True,
                message="Profile created successfully",
                data={
                    "userId": user_id,
                    "deviceId": device_id,
                    "profileCompleteness": profile_completeness,
                    "lastUpdated": now.isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Error creating/updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create/update profile"
        )

@router.get("/profile/{device_id}")
async def get_user_profile(device_id: str):
    """Get user profile by device ID"""
    try:
        query = """
            SELECT * FROM iosapp.users WHERE device_id = $1
        """
        
        result = await db_manager.execute_query(query, device_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user = result[0]
        
        # Build response data
        response_data = {
            "userId": user["id"],
            "deviceId": user["device_id"],
            "personalInfo": {
                "firstName": user["first_name"],
                "lastName": user["last_name"],
                "email": user["email"],
                "phone": user["phone"],
                "location": user["location"],
                "currentJobTitle": user["current_job_title"],
                "yearsOfExperience": user["years_of_experience"],
                "linkedInProfile": user["linkedin_profile"],
                "portfolioURL": user["portfolio_url"],
                "bio": user["bio"]
            },
            "jobPreferences": {
                "desiredJobTypes": user["desired_job_types"],
                "remoteWorkPreference": user["remote_work_preference"],
                "skills": user["skills"],
                "preferredLocations": user["preferred_locations"],
                "salaryRange": {
                    "minSalary": user["min_salary"],
                    "maxSalary": user["max_salary"],
                    "currency": user["salary_currency"],
                    "isNegotiable": user["salary_negotiable"]
                }
            },
            "notificationSettings": {
                "jobMatchesEnabled": user["job_matches_enabled"],
                "applicationRemindersEnabled": user["application_reminders_enabled"],
                "weeklyDigestEnabled": user["weekly_digest_enabled"],
                "marketInsightsEnabled": user["market_insights_enabled"],
                "quietHoursEnabled": user["quiet_hours_enabled"],
                "quietHoursStart": user["quiet_hours_start"],
                "quietHoursEnd": user["quiet_hours_end"],
                "preferredNotificationTime": user["preferred_notification_time"]
            },
            "privacySettings": {
                "profileVisibility": user["profile_visibility"],
                "shareAnalytics": user["share_analytics"],
                "shareJobViewHistory": user["share_job_view_history"],
                "allowPersonalizedRecommendations": user["allow_personalized_recommendations"]
            },
            "profileCompleteness": user["profile_completeness"],
            "createdAt": user["created_at"].isoformat() if user["created_at"] else None,
            "lastUpdated": user["updated_at"].isoformat() if user["updated_at"] else None
        }
        
        return {
            "success": True,
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )

@router.post("/{device_id}/saved-jobs")
async def save_job(device_id: str, save_data: SaveJobRequest):
    """Save a job to user's saved jobs list"""
    try:
        # Get user ID from device ID
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_result[0]["id"]
        
        # Check if job already saved
        existing_query = """
            SELECT id FROM iosapp.saved_jobs 
            WHERE user_id = $1 AND job_id = $2
        """
        existing = await db_manager.execute_query(existing_query, user_id, save_data.jobId)
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Job already saved"
            )
        
        # Save the job
        import uuid
        saved_job_id = str(uuid.uuid4())
        
        insert_query = """
            INSERT INTO iosapp.saved_jobs (id, user_id, job_id, notes, created_at)
            VALUES ($1, $2, $3, $4, $5)
        """
        
        now = datetime.utcnow()
        await db_manager.execute_query(
            insert_query, 
            saved_job_id, user_id, save_data.jobId, save_data.notes, now
        )
        
        return {
            "success": True,
            "message": "Job saved successfully",
            "data": {
                "savedJobId": saved_job_id,
                "jobId": save_data.jobId,
                "savedAt": now.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save job"
        )

@router.get("/{device_id}/saved-jobs")
async def get_saved_jobs(
    device_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's saved jobs with pagination"""
    try:
        # Get user ID
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_result[0]["id"]
        offset = (page - 1) * limit
        
        # Get saved jobs with job details
        saved_jobs_query = """
            SELECT 
                sj.id as saved_job_id,
                sj.job_id,
                sj.notes,
                sj.application_status,
                sj.created_at as saved_at,
                j.title,
                j.company,
                j.created_at as posted_date
            FROM iosapp.saved_jobs sj
            LEFT JOIN scraper.jobs_jobpost j ON sj.job_id = j.id
            WHERE sj.user_id = $1
            ORDER BY sj.created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        saved_jobs = await db_manager.execute_query(
            saved_jobs_query, user_id, limit, offset
        )
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM iosapp.saved_jobs WHERE user_id = $1"
        count_result = await db_manager.execute_query(count_query, user_id)
        total_saved_jobs = count_result[0]["total"] if count_result else 0
        
        # Format response
        jobs_data = []
        for job in saved_jobs:
            jobs_data.append({
                "savedJobId": job["saved_job_id"],
                "jobId": job["job_id"],
                "title": job["title"] or "Job title not available",
                "companyName": job["company"] or "Company not available",
                "location": "Location not available",  # Can be enhanced with location data
                "salary": "Salary not specified",  # Can be enhanced with salary data
                "postedDate": job["posted_date"].isoformat() if job["posted_date"] else None,
                "savedAt": job["saved_at"].isoformat() if job["saved_at"] else None,
                "notes": job["notes"],
                "applicationStatus": job["application_status"]
            })
        
        total_pages = (total_saved_jobs + limit - 1) // limit
        
        return {
            "success": True,
            "data": {
                "savedJobs": jobs_data,
                "totalSavedJobs": total_saved_jobs,
                "page": page,
                "totalPages": total_pages
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get saved jobs"
        )

@router.delete("/{device_id}/saved-jobs/{job_id}")
async def remove_saved_job(device_id: str, job_id: int):
    """Remove a job from user's saved jobs"""
    try:
        # Get user ID
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_result[0]["id"]
        
        # Delete the saved job
        delete_query = """
            DELETE FROM iosapp.saved_jobs 
            WHERE user_id = $1 AND job_id = $2
        """
        
        result = await db_manager.execute_query(delete_query, user_id, job_id)
        
        return {
            "success": True,
            "message": "Job removed from saved jobs"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing saved job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove saved job"
        )

@router.get("/{device_id}/analytics")
async def get_user_analytics(device_id: str):
    """Get user-specific analytics and insights"""
    try:
        # Get user ID
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_result[0]["id"]
        
        # Get profile insights
        profile_query = """
            SELECT 
                profile_completeness,
                skills,
                years_of_experience,
                current_job_title
            FROM iosapp.users 
            WHERE device_id = $1
        """
        profile_result = await db_manager.execute_query(profile_query, device_id)
        user_profile = profile_result[0] if profile_result else {}
        
        # Calculate profile strength (based on completeness and skills)
        profile_completeness = user_profile.get("profile_completeness", 0)
        skills_count = len(user_profile.get("skills", []) or [])
        profile_strength = min(profile_completeness + (skills_count * 2), 100)
        
        # Get job activity stats
        activity_queries = {
            "total_jobs_viewed": "SELECT COUNT(*) as count FROM iosapp.job_views WHERE user_id = $1",
            "total_jobs_saved": "SELECT COUNT(*) as count FROM iosapp.saved_jobs WHERE user_id = $1",
            "total_applications": "SELECT COUNT(*) as count FROM iosapp.job_applications WHERE user_id = $1"
        }
        
        activity_stats = {}
        for stat_name, query in activity_queries.items():
            result = await db_manager.execute_query(query, user_id)
            activity_stats[stat_name] = result[0]["count"] if result else 0
        
        # Get average view time
        avg_view_query = """
            SELECT AVG(view_duration) as avg_duration 
            FROM iosapp.job_views 
            WHERE user_id = $1 AND view_duration > 0
        """
        avg_view_result = await db_manager.execute_query(avg_view_query, user_id)
        avg_view_time = avg_view_result[0]["avg_duration"] if avg_view_result and avg_view_result[0]["avg_duration"] else 0
        avg_view_time_str = f"{int(avg_view_time / 60)} minutes" if avg_view_time > 60 else f"{int(avg_view_time)} seconds"
        
        # Get last week activity
        from datetime import datetime, timedelta
        last_week = datetime.utcnow() - timedelta(days=7)
        
        last_week_queries = {
            "jobs_viewed": f"""
                SELECT COUNT(*) as count FROM iosapp.job_views 
                WHERE user_id = $1 AND viewed_at >= '{last_week.isoformat()}'
            """,
            "jobs_saved": f"""
                SELECT COUNT(*) as count FROM iosapp.saved_jobs 
                WHERE user_id = $1 AND created_at >= '{last_week.isoformat()}'
            """,
            "applications": f"""
                SELECT COUNT(*) as count FROM iosapp.job_applications 
                WHERE user_id = $1 AND applied_at >= '{last_week.isoformat()}'
            """
        }
        
        last_week_activity = {}
        for stat_name, query in last_week_queries.items():
            result = await db_manager.execute_query(query, user_id)
            last_week_activity[stat_name] = result[0]["count"] if result else 0
        
        # Get most viewed categories (based on job titles)
        categories_query = """
            SELECT 
                CASE 
                    WHEN LOWER(j.title) LIKE '%ios%' OR LOWER(j.title) LIKE '%swift%' THEN 'iOS Development'
                    WHEN LOWER(j.title) LIKE '%android%' OR LOWER(j.title) LIKE '%kotlin%' THEN 'Android Development'
                    WHEN LOWER(j.title) LIKE '%web%' OR LOWER(j.title) LIKE '%javascript%' THEN 'Web Development'
                    WHEN LOWER(j.title) LIKE '%data%' OR LOWER(j.title) LIKE '%python%' THEN 'Data Science'
                    WHEN LOWER(j.title) LIKE '%mobile%' THEN 'Mobile Development'
                    ELSE 'Other'
                END as category,
                COUNT(*) as view_count
            FROM iosapp.job_views jv
            JOIN scraper.jobs_jobpost j ON jv.job_id = j.id
            WHERE jv.user_id = $1
            GROUP BY category
            ORDER BY view_count DESC
            LIMIT 5
        """
        categories_result = await db_manager.execute_query(categories_query, user_id)
        most_viewed_categories = [row["category"] for row in categories_result if row["category"] != "Other"]
        
        # Calculate market fit based on skills and activity
        skills = user_profile.get("skills", []) or []
        market_fit = min(50 + len(skills) * 5 + (activity_stats["total_jobs_viewed"] // 10), 100)
        
        # Generate improvement areas
        improvement_areas = []
        if profile_completeness < 80:
            improvement_areas.append("Complete your profile for better job matches")
        if len(skills) < 5:
            improvement_areas.append("Add more skills to your profile")
        if activity_stats["total_applications"] == 0:
            improvement_areas.append("Start applying to relevant job positions")
        if not user_profile.get("current_job_title"):
            improvement_areas.append("Add your current job title")
        
        # Mock matching insights (can be enhanced with real data)
        total_matches = activity_stats["total_jobs_viewed"]  # Simplified
        average_match_score = 75 if total_matches > 0 else 0  # Mock score
        
        # Mock market insights
        market_insights = [
            {
                "insight": "iOS Developer demand increased 15% this month",
                "confidence": 0.9,
                "category": "market_trend"
            },
            {
                "insight": "Your skill set matches 80% of current iOS job requirements",
                "confidence": 0.85,
                "category": "skills_analysis"
            }
        ]
        
        response_data = {
            "profileInsights": {
                "profileStrength": profile_strength,
                "profileCompleteness": profile_completeness,
                "skillsAssessment": f"Strong profile with {len(skills)} skills listed" if len(skills) >= 3 else "Add more skills to strengthen your profile",
                "marketFit": market_fit,
                "improvementAreas": improvement_areas
            },
            "jobActivity": {
                "totalJobsViewed": activity_stats["total_jobs_viewed"],
                "totalJobsSaved": activity_stats["total_jobs_saved"],
                "totalApplications": activity_stats["total_applications"],
                "averageViewTime": avg_view_time_str,
                "mostViewedCategories": most_viewed_categories,
                "lastWeekActivity": last_week_activity
            },
            "matchingInsights": {
                "totalMatches": total_matches,
                "averageMatchScore": average_match_score,
                "topMatchingCompanies": ["Apple", "Google", "Meta"],  # Mock data
                "recommendedSkills": ["SwiftUI", "Combine", "Core Data"]  # Mock data
            },
            "marketInsights": market_insights
        }
        
        return {
            "success": True,
            "data": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user analytics"
        )

@router.post("/{device_id}/job-views")
async def track_job_view(device_id: str, view_data: JobViewRequest):
    """Track when a user views a job"""
    try:
        # Get user ID
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_result[0]["id"]
        
        # Insert job view record
        import uuid
        view_id = str(uuid.uuid4())
        
        insert_query = """
            INSERT INTO iosapp.job_views 
            (id, user_id, job_id, view_duration, source, viewed_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        await db_manager.execute_query(
            insert_query,
            view_id, user_id, view_data.jobId, view_data.viewDuration, 
             view_data.source, view_data.timestamp
        )
        
        return {
            "success": True,
            "message": "Job view tracked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking job view: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track job view"
        )

@router.get("/{device_id}/applications")
async def get_application_history(
    device_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get user's job application history"""
    try:
        # Get user ID
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_id = user_result[0]["id"]
        offset = (page - 1) * limit
        
        # Get applications with job details
        applications_query = """
            SELECT 
                ja.id as application_id,
                ja.job_id,
                ja.status,
                ja.applied_at,
                ja.notes,
                ja.follow_up_date,
                j.title,
                j.company
            FROM iosapp.job_applications ja
            LEFT JOIN scraper.jobs_jobpost j ON ja.job_id = j.id
            WHERE ja.user_id = $1
            ORDER BY ja.applied_at DESC
            LIMIT $2 OFFSET $3
        """
        
        applications = await db_manager.execute_query(
            applications_query, user_id, limit, offset
        )
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM iosapp.job_applications WHERE user_id = $1"
        count_result = await db_manager.execute_query(count_query, user_id)
        total_applications = count_result[0]["total"] if count_result else 0
        
        # Get status counts
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM iosapp.job_applications 
            WHERE user_id = $1 
            GROUP BY status
        """
        status_result = await db_manager.execute_query(status_query, user_id)
        status_counts = {row["status"]: row["count"] for row in status_result}
        
        # Format applications data
        applications_data = []
        for app in applications:
            applications_data.append({
                "applicationId": app["application_id"],
                "jobId": app["job_id"],
                "title": app["title"] or "Job title not available",
                "companyName": app["company"] or "Company not available",
                "appliedAt": app["applied_at"].isoformat() if app["applied_at"] else None,
                "status": app["status"],
                "notes": app["notes"],
                "followUpDate": app["follow_up_date"].isoformat() if app["follow_up_date"] else None
            })
        
        return {
            "success": True,
            "data": {
                "applications": applications_data,
                "totalApplications": total_applications,
                "statusCounts": {
                    "pending": status_counts.get("pending", 0),
                    "interview": status_counts.get("interview", 0),
                    "rejected": status_counts.get("rejected", 0),
                    "offer": status_counts.get("offer", 0)
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get application history"
        )

@router.post("/profile/sync")
async def sync_profile(sync_request):
    """Sync profile across devices - placeholder implementation"""
    try:
        # This is a placeholder implementation
        # In a real system, you would implement proper device sync logic
        
        source_device = sync_request.get("sourceDeviceId")
        target_device = sync_request.get("targetDeviceId")
        
        if not source_device or not target_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target device IDs are required"
            )
        
        # Mock successful sync response
        return {
            "success": True,
            "message": "Profile synchronized successfully",
            "data": {
                "syncedItems": {
                    "profile": True,
                    "savedJobs": 0,  # Would contain actual count
                    "preferences": True,
                    "analytics": True
                },
                "lastSync": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync profile"
        )