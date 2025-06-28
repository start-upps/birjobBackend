from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime

from app.core.database import db_manager
from app.schemas.user_unified import (
    UnifiedUserCreate, UnifiedUserUpdate, UnifiedUserResponse,
    UpdateKeywordsRequest, AddKeywordRequest, KeywordResponse,
    UserProfileCreate, UserProfileResponse, UserProfile,
    SuccessResponse, ErrorResponse
)
from app.services.match_engine import ProfileBasedJobMatcher

router = APIRouter()
logger = logging.getLogger(__name__)

# =====================================
# Core User Profile Management
# =====================================

@router.post("/profile", response_model=SuccessResponse)
async def create_or_update_user_profile(user_data: UnifiedUserCreate):
    """Create or update user profile in unified table"""
    try:
        # Convert Pydantic model to dict for database insertion
        user_dict = user_data.dict(exclude_unset=True)
        device_id = user_dict.pop('device_id')
        
        # Prepare JSONB fields
        jsonb_fields = ['desired_job_types', 'skills', 'preferred_locations', 'match_keywords',
                       'additional_personal_info', 'additional_job_preferences', 
                       'additional_notification_settings', 'additional_privacy_settings']
        
        for field in jsonb_fields:
            if field in user_dict and user_dict[field] is not None:
                user_dict[field] = json.dumps(user_dict[field])
        
        # Build dynamic INSERT/UPDATE query
        fields = list(user_dict.keys())
        placeholders = [f"${i+2}" for i in range(len(fields))]
        
        # Create UPSERT query
        upsert_query = f"""
            INSERT INTO iosapp.users_unified (device_id, {', '.join(fields)})
            VALUES ($1, {', '.join(placeholders)})
            ON CONFLICT (device_id) 
            DO UPDATE SET 
                {', '.join([f"{field} = EXCLUDED.{field}" for field in fields])},
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, device_id, profile_completeness, updated_at;
        """
        
        result = await db_manager.execute_query(
            upsert_query, 
            device_id,
            *user_dict.values()
        )
        
        if result:
            user_result = result[0]
            return SuccessResponse(
                message="User profile created/updated successfully",
                data={
                    "userId": str(user_result["id"]),
                    "deviceId": user_result["device_id"],
                    "profileCompleteness": user_result["profile_completeness"],
                    "lastUpdated": user_result["updated_at"].isoformat()
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create/update profile"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create/update profile"
        )

@router.get("/profile/{device_id}", response_model=UserProfileResponse)
async def get_user_profile(device_id: str):
    """Get user profile by device ID"""
    try:
        profile_query = """
            SELECT 
                id, device_id, first_name, last_name, email, phone, location,
                current_job_title, years_of_experience, linkedin_profile, portfolio_url, bio,
                desired_job_types, remote_work_preference, skills, preferred_locations,
                min_salary, max_salary, salary_currency, salary_negotiable,
                match_keywords, job_matches_enabled, application_reminders_enabled,
                weekly_digest_enabled, market_insights_enabled, quiet_hours_enabled,
                quiet_hours_start, quiet_hours_end, preferred_notification_time,
                profile_visibility, share_analytics, share_job_view_history,
                allow_personalized_recommendations, additional_personal_info,
                additional_job_preferences, additional_notification_settings,
                additional_privacy_settings, profile_completeness, created_at, updated_at
            FROM iosapp.users_unified 
            WHERE device_id = $1
        """
        
        result = await db_manager.execute_query(profile_query, device_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user_data = result[0]
        
        # Parse JSONB fields
        def parse_jsonb_field(field_value):
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return []
            return field_value or []
        
        # Convert to legacy format for backward compatibility
        profile = UserProfile(
            userId=str(user_data["id"]),
            deviceId=user_data["device_id"],
            personalInfo={
                "firstName": user_data["first_name"],
                "lastName": user_data["last_name"],
                "email": user_data["email"],
                "phone": user_data["phone"],
                "location": user_data["location"],
                "currentJobTitle": user_data["current_job_title"],
                "yearsOfExperience": user_data["years_of_experience"],
                "linkedInProfile": user_data["linkedin_profile"],
                "portfolioURL": user_data["portfolio_url"],
                "bio": user_data["bio"]
            },
            jobPreferences={
                "desiredJobTypes": parse_jsonb_field(user_data["desired_job_types"]),
                "remoteWorkPreference": user_data["remote_work_preference"],
                "skills": parse_jsonb_field(user_data["skills"]),
                "preferredLocations": parse_jsonb_field(user_data["preferred_locations"]),
                "salaryRange": {
                    "minSalary": user_data["min_salary"],
                    "maxSalary": user_data["max_salary"],
                    "currency": user_data["salary_currency"],
                    "isNegotiable": user_data["salary_negotiable"]
                },
                "matchKeywords": parse_jsonb_field(user_data["match_keywords"])
            },
            notificationSettings={
                "jobMatchesEnabled": user_data["job_matches_enabled"],
                "applicationRemindersEnabled": user_data["application_reminders_enabled"],
                "weeklyDigestEnabled": user_data["weekly_digest_enabled"],
                "marketInsightsEnabled": user_data["market_insights_enabled"],
                "quietHoursEnabled": user_data["quiet_hours_enabled"],
                "quietHoursStart": user_data["quiet_hours_start"],
                "quietHoursEnd": user_data["quiet_hours_end"],
                "preferredNotificationTime": user_data["preferred_notification_time"]
            },
            privacySettings={
                "profileVisibility": user_data["profile_visibility"],
                "shareAnalytics": user_data["share_analytics"],
                "shareJobViewHistory": user_data["share_job_view_history"],
                "allowPersonalizedRecommendations": user_data["allow_personalized_recommendations"]
            },
            profileCompleteness=user_data["profile_completeness"],
            createdAt=user_data["created_at"],
            lastUpdated=user_data["updated_at"]
        )
        
        return UserProfileResponse(
            success=True,
            message="Profile retrieved successfully",
            data=profile
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

# =====================================
# Keyword Management (New Unified Approach)
# =====================================

@router.get("/{device_id}/profile/keywords", response_model=Dict[str, Any])
async def get_profile_keywords(device_id: str):
    """Get user's profile keywords for job matching"""
    try:
        profile_query = """
            SELECT match_keywords, skills, updated_at
            FROM iosapp.users_unified 
            WHERE device_id = $1
        """
        
        result = await db_manager.execute_query(profile_query, device_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user_data = result[0]
        
        # Parse JSONB fields
        def parse_jsonb_field(field_value):
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return []
            return field_value or []
        
        match_keywords = parse_jsonb_field(user_data["match_keywords"])
        skills = parse_jsonb_field(user_data["skills"])
        
        return {
            "success": True,
            "data": {
                "matchKeywords": match_keywords,
                "keywordCount": len(match_keywords),
                "lastUpdated": user_data["updated_at"].isoformat() if user_data["updated_at"] else None,
                "relatedSkills": skills
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile keywords"
        )

@router.post("/{device_id}/profile/keywords", response_model=Dict[str, Any])
async def update_profile_keywords(device_id: str, request: UpdateKeywordsRequest):
    """Update user's profile keywords list"""
    try:
        # Validate and clean keywords
        unique_keywords = list(set(kw.strip().lower() for kw in request.match_keywords if kw.strip()))
        
        if len(unique_keywords) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 keywords allowed"
            )
        
        update_query = """
            UPDATE iosapp.users_unified 
            SET 
                match_keywords = $1::jsonb,
                updated_at = CURRENT_TIMESTAMP
            WHERE device_id = $2
            RETURNING updated_at
        """
        
        result = await db_manager.execute_query(
            update_query, 
            json.dumps(unique_keywords), 
            device_id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return {
            "success": True,
            "message": "Keywords updated successfully",
            "data": {
                "matchKeywords": unique_keywords,
                "keywordCount": len(unique_keywords),
                "lastUpdated": result[0]["updated_at"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile keywords"
        )

@router.post("/{device_id}/profile/keywords/add", response_model=Dict[str, Any])
async def add_profile_keyword(device_id: str, request: AddKeywordRequest):
    """Add a single keyword to user's profile"""
    try:
        new_keyword = request.keyword.strip().lower()
        
        # Get current keywords
        current_query = """
            SELECT match_keywords 
            FROM iosapp.users_unified 
            WHERE device_id = $1
        """
        
        current_result = await db_manager.execute_query(current_query, device_id)
        
        if not current_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Parse JSONB field
        def parse_jsonb_field(field_value):
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return []
            return field_value or []
        
        current_keywords = parse_jsonb_field(current_result[0]["match_keywords"])
        
        # Check if keyword already exists
        if new_keyword in current_keywords:
            return {
                "success": True,
                "message": "Keyword already exists",
                "data": {
                    "matchKeywords": current_keywords,
                    "keywordCount": len(current_keywords)
                }
            }
        
        # Check keyword limit
        if len(current_keywords) >= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 keywords allowed"
            )
        
        # Add new keyword
        updated_keywords = current_keywords + [new_keyword]
        
        # Update database
        update_query = """
            UPDATE iosapp.users_unified 
            SET 
                match_keywords = $1::jsonb,
                updated_at = CURRENT_TIMESTAMP
            WHERE device_id = $2
            RETURNING updated_at
        """
        
        result = await db_manager.execute_query(
            update_query, 
            json.dumps(updated_keywords), 
            device_id
        )
        
        return {
            "success": True,
            "message": "Keyword added successfully",
            "data": {
                "matchKeywords": updated_keywords,
                "keywordCount": len(updated_keywords),
                "addedKeyword": new_keyword,
                "lastUpdated": result[0]["updated_at"].isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding profile keyword: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add profile keyword"
        )

@router.delete("/{device_id}/profile/keywords/{keyword}", response_model=Dict[str, Any])
async def remove_profile_keyword(device_id: str, keyword: str):
    """Remove a keyword from user's profile"""
    try:
        keyword = keyword.strip().lower()
        
        # Get current keywords
        current_query = """
            SELECT match_keywords 
            FROM iosapp.users_unified 
            WHERE device_id = $1
        """
        
        current_result = await db_manager.execute_query(current_query, device_id)
        
        if not current_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Parse JSONB field
        def parse_jsonb_field(field_value):
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return []
            return field_value or []
        
        current_keywords = parse_jsonb_field(current_result[0]["match_keywords"])
        
        # Remove keyword if it exists
        if keyword in current_keywords:
            updated_keywords = [kw for kw in current_keywords if kw != keyword]
            
            # Update database
            update_query = """
                UPDATE iosapp.users_unified 
                SET 
                    match_keywords = $1::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE device_id = $2
                RETURNING updated_at
            """
            
            result = await db_manager.execute_query(
                update_query, 
                json.dumps(updated_keywords), 
                device_id
            )
            
            return {
                "success": True,
                "message": "Keyword removed successfully",
                "data": {
                    "matchKeywords": updated_keywords,
                    "keywordCount": len(updated_keywords),
                    "removedKeyword": keyword,
                    "lastUpdated": result[0]["updated_at"].isoformat()
                }
            }
        else:
            return {
                "success": True,
                "message": "Keyword not found in profile",
                "data": {
                    "matchKeywords": current_keywords,
                    "keywordCount": len(current_keywords)
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing profile keyword: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove profile keyword"
        )

@router.get("/{device_id}/profile/matches", response_model=Dict[str, Any])
async def get_profile_based_matches(
    device_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get intelligent job matches based on profile keywords"""
    try:
        # Get user's keywords
        keywords_query = """
            SELECT match_keywords 
            FROM iosapp.users_unified 
            WHERE device_id = $1
        """
        
        keywords_result = await db_manager.execute_query(keywords_query, device_id)
        
        if not keywords_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Parse JSONB field
        def parse_jsonb_field(field_value):
            if isinstance(field_value, str):
                try:
                    return json.loads(field_value)
                except:
                    return []
            return field_value or []
        
        match_keywords = parse_jsonb_field(keywords_result[0]["match_keywords"])
        
        if not match_keywords:
            return {
                "success": True,
                "data": {
                    "matches": [],
                    "totalCount": 0,
                    "userKeywords": [],
                    "matchingStats": {
                        "totalJobsEvaluated": 0,
                        "jobsWithMatches": 0,
                        "averageScore": 0,
                        "topScore": 0
                    }
                }
            }
        
        # Get jobs for matching
        jobs_query = """
            SELECT id, title, company, apply_link, source, created_at
            FROM scraper.jobs_jobpost
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        
        jobs_result = await db_manager.execute_query(jobs_query, limit * 2, offset)
        
        # Use the job matching service
        matcher = ProfileBasedJobMatcher()
        scored_jobs = []
        
        for job in jobs_result:
            match_details = matcher.calculate_match_score(dict(job), match_keywords)
            
            if match_details["score"] > 0:  # Only include jobs with relevance
                scored_jobs.append({
                    "jobId": job["id"],
                    "title": job["title"],
                    "company": job["company"],
                    "location": "Remote",  # Default since location not in table
                    "salary": "Competitive",  # Default since salary not in table
                    "description": job["title"],  # Use title as description fallback
                    "source": job["source"],
                    "postedAt": job["created_at"].isoformat() if job["created_at"] else None,
                    "matchScore": round(match_details["score"], 1),
                    "matchedKeywords": match_details["matched_keywords"],
                    "matchReasons": match_details["match_reasons"][:3],  # Top 3 reasons
                    "keywordRelevance": match_details["keyword_relevance"]
                })
        
        # Sort by score (descending) and take requested limit
        scored_jobs.sort(key=lambda x: x["matchScore"], reverse=True)
        final_matches = scored_jobs[:limit]
        
        # Calculate stats
        total_jobs_evaluated = len(jobs_result)
        jobs_with_matches = len(scored_jobs)
        average_score = sum(job["matchScore"] for job in scored_jobs) / len(scored_jobs) if scored_jobs else 0
        top_score = max(job["matchScore"] for job in scored_jobs) if scored_jobs else 0
        
        matches = {
            "matches": final_matches,
            "totalCount": jobs_with_matches,
            "userKeywords": match_keywords,
            "matchingStats": {
                "totalJobsEvaluated": total_jobs_evaluated,
                "jobsWithMatches": jobs_with_matches,
                "averageScore": round(average_score, 1),
                "topScore": round(top_score, 1)
            }
        }
        
        return {
            "success": True,
            "data": matches
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile-based matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile-based matches"
        )

# =====================================
# Legacy Compatibility Endpoints
# =====================================

@router.post("/profile/sync")
async def sync_user_profile(
    sourceDeviceId: str = Query(...),
    targetDeviceId: str = Query(...)
):
    """Sync user profile between devices (legacy endpoint)"""
    try:
        # Get source profile
        source_query = """
            SELECT * FROM iosapp.users_unified WHERE device_id = $1
        """
        source_result = await db_manager.execute_query(source_query, sourceDeviceId)
        
        if not source_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source device profile not found"
            )
        
        source_data = dict(source_result[0])
        # Remove ID and device_id for target insertion
        source_data.pop('id', None)
        source_data.pop('device_id', None)
        source_data.pop('created_at', None)
        source_data.pop('updated_at', None)
        
        # Prepare fields for insertion
        fields = list(source_data.keys())
        placeholders = [f"${i+2}" for i in range(len(fields))]
        
        # Insert/update target profile
        sync_query = f"""
            INSERT INTO iosapp.users_unified (device_id, {', '.join(fields)})
            VALUES ($1, {', '.join(placeholders)})
            ON CONFLICT (device_id) 
            DO UPDATE SET 
                {', '.join([f"{field} = EXCLUDED.{field}" for field in fields])},
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, profile_completeness;
        """
        
        result = await db_manager.execute_query(
            sync_query,
            targetDeviceId,
            *source_data.values()
        )
        
        return {
            "success": True,
            "message": "Profile synced successfully",
            "data": {
                "targetDeviceId": targetDeviceId,
                "profileCompleteness": result[0]["profile_completeness"]
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