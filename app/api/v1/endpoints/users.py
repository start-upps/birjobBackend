from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime

from app.core.database import db_manager
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse,
    AddKeywordRequest, RemoveKeywordRequest, UpdateKeywordsRequest,
    SaveJobRequest, JobViewRequest, EmailUserRequest, EmailKeywordRequest,
    UserRegistrationRequest, UserRegistrationResponse,
    SuccessResponse, ErrorResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# =====================================
# Email-based User Management (Website Style)
# =====================================

@router.get("/by-email", response_model=SuccessResponse)
async def get_user_by_email(email: str = Query(...)):
    """Get or create user by email (website-style)"""
    try:
        # Check if user exists
        query = "SELECT * FROM iosapp.users WHERE email = $1"
        result = await db_manager.execute_query(query, email)
        
        if result:
            user = result[0]
            return SuccessResponse(
                message="User found",
                data={
                    "id": str(user["id"]),
                    "email": user["email"],
                    "keywords": user["keywords"] or [],
                    "preferred_sources": user["preferred_sources"] or [],
                    "notifications_enabled": user["notifications_enabled"],
                    "created_at": user["created_at"].isoformat()
                }
            )
        else:
            # Auto-create user with email only (no device_id in users table now)
            create_query = """
                INSERT INTO iosapp.users (email, keywords, preferred_sources)
                VALUES ($1, $2, $3)
                RETURNING *
            """
            new_result = await db_manager.execute_query(
                create_query, email, json.dumps([]), json.dumps([])
            )
            
            if new_result:
                user = new_result[0]
                return SuccessResponse(
                    message="User created",
                    data={
                        "id": str(user["id"]),
                        "email": user["email"],
                        "keywords": [],
                        "preferred_sources": [],
                        "notifications_enabled": True,
                        "created_at": user["created_at"].isoformat()
                    }
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to create user")
                
    except Exception as e:
        logger.error(f"Error in get_user_by_email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/keywords/email", response_model=SuccessResponse)
async def add_keyword_by_email(request: EmailKeywordRequest):
    """Add keyword for user by email (website-style)"""
    try:
        # Get or create user
        user_response = await get_user_by_email(request.email)
        
        # Get current keywords
        query = "SELECT keywords FROM iosapp.users WHERE email = $1"
        result = await db_manager.execute_query(query, request.email)
        
        if result:
            # Parse JSON string to list if needed
            keywords_data = result[0]["keywords"]
            if isinstance(keywords_data, str):
                current_keywords = json.loads(keywords_data) if keywords_data else []
            else:
                current_keywords = keywords_data or []
                
            keyword_lower = request.keyword.lower().strip()
            
            if keyword_lower not in [k.lower() for k in current_keywords]:
                current_keywords.append(keyword_lower)
                
                # Update keywords
                update_query = """
                    UPDATE iosapp.users 
                    SET keywords = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE email = $2
                """
                await db_manager.execute_query(update_query, json.dumps(current_keywords), request.email)
                
                return SuccessResponse(
                    message="Keyword added successfully",
                    data={"keywords": current_keywords}
                )
            else:
                return SuccessResponse(
                    message="Keyword already exists",
                    data={"keywords": current_keywords}
                )
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        logger.error(f"Error adding keyword by email: {e}")
        raise HTTPException(status_code=500, detail="Failed to add keyword")

@router.delete("/keywords/email", response_model=SuccessResponse)
async def remove_keyword_by_email(email: str = Query(...), keyword: str = Query(...)):
    """Remove keyword for user by email (website-style)"""
    try:
        # Get current keywords
        query = "SELECT keywords FROM iosapp.users WHERE email = $1"
        result = await db_manager.execute_query(query, email)
        
        if result:
            # Parse JSON string to list if needed
            keywords_data = result[0]["keywords"]
            if isinstance(keywords_data, str):
                current_keywords = json.loads(keywords_data) if keywords_data else []
            else:
                current_keywords = keywords_data or []
                
            keyword_lower = keyword.lower().strip()
            
            # Remove keyword (case-insensitive)
            updated_keywords = [k for k in current_keywords if k.lower() != keyword_lower]
            
            # Update keywords
            update_query = """
                UPDATE iosapp.users 
                SET keywords = $1, updated_at = CURRENT_TIMESTAMP
                WHERE email = $2
            """
            await db_manager.execute_query(update_query, json.dumps(updated_keywords), email)
            
            return SuccessResponse(
                message="Keyword removed successfully",
                data={"keywords": updated_keywords}
            )
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        logger.error(f"Error removing keyword by email: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove keyword")

# =====================================
# Device-based User Management (iOS App)
# =====================================

@router.post("/register", response_model=UserRegistrationResponse)
async def register_user_with_device(request: UserRegistrationRequest):
    """Unified user registration with device token (iOS app)"""
    try:
        # First, create or find user
        user_query = """
            SELECT u.* FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if user_result:
            # Update existing user
            user_id = user_result[0]['id']
            update_query = """
                UPDATE iosapp.users 
                SET email = $1, keywords = $2, preferred_sources = $3, 
                    notifications_enabled = true, updated_at = NOW()
                WHERE id = $4
            """
            await db_manager.execute_command(
                update_query,
                request.email,
                json.dumps(request.keywords),
                json.dumps(request.preferred_sources),
                user_id
            )
            
            # Update device token
            device_update_query = """
                UPDATE iosapp.device_tokens 
                SET device_token = $1, device_info = $2, updated_at = NOW()
                WHERE user_id = $3 AND device_id = $4
            """
            await db_manager.execute_command(
                device_update_query,
                request.device_token,
                json.dumps(request.device_info),
                user_id,
                request.device_id
            )
            
            return UserRegistrationResponse(
                message="User updated successfully",
                data={
                    "user_id": str(user_id),
                    "device_id": request.device_id
                }
            )
        else:
            # Create new user
            user_insert_query = """
                INSERT INTO iosapp.users (email, keywords, preferred_sources, notifications_enabled)
                VALUES ($1, $2, $3, true)
                RETURNING id
            """
            user_insert_result = await db_manager.execute_query(
                user_insert_query,
                request.email,
                json.dumps(request.keywords),
                json.dumps(request.preferred_sources)
            )
            
            if not user_insert_result:
                raise Exception("Failed to create user")
            
            user_id = user_insert_result[0]['id']
            
            # Create device token
            device_insert_query = """
                INSERT INTO iosapp.device_tokens (user_id, device_id, device_token, device_info)
                VALUES ($1, $2, $3, $4)
            """
            await db_manager.execute_command(
                device_insert_query,
                user_id,
                request.device_id,
                request.device_token,
                json.dumps(request.device_info)
            )
            
            logger.info(f"New user registered: {user_id} with device: {request.device_id}")
            
            return UserRegistrationResponse(
                message="User registered successfully", 
                data={
                    "user_id": str(user_id),
                    "device_id": request.device_id
                }
            )
            
    except Exception as e:
        logger.error(f"Error in unified user registration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")

@router.post("/register-basic", response_model=SuccessResponse)
async def register_user(user_data: UserCreate):
    """Register new user with device_id (iOS app)"""
    try:
        # Check if device already exists
        device_query = """
            SELECT u.* FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        device_result = await db_manager.execute_query(device_query, user_data.device_id)
        
        if device_result:
            return SuccessResponse(
                message="User already registered with this device",
                data={"user_id": str(device_result[0]["id"])}
            )
        
        # Check if email already exists
        email_query = "SELECT * FROM iosapp.users WHERE email = $1"
        email_result = await db_manager.execute_query(email_query, user_data.email)
        
        user_id = None
        
        if email_result:
            # User exists with this email, link to existing user
            user_id = email_result[0]["id"]
            
            # Update keywords if provided
            if user_data.keywords:
                update_query = """
                    UPDATE iosapp.users 
                    SET keywords = $1, notifications_enabled = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """
                await db_manager.execute_query(
                    update_query,
                    json.dumps(user_data.keywords),
                    user_data.notifications_enabled,
                    user_id
                )
        else:
            # Create new user
            user_insert_query = """
                INSERT INTO iosapp.users (email, keywords, preferred_sources, notifications_enabled)
                VALUES ($1, $2, $3, $4)
                RETURNING id, created_at
            """
            
            user_result = await db_manager.execute_query(
                user_insert_query,
                user_data.email,
                json.dumps(user_data.keywords or []),
                json.dumps(user_data.preferred_sources or []),
                user_data.notifications_enabled
            )
            
            if user_result:
                user_id = user_result[0]["id"]
            else:
                raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Create device token entry without actual token (will be added when APNs token is available)
        device_token_query = """
            INSERT INTO iosapp.device_tokens (user_id, device_id, device_info)
            VALUES ($1, $2, $3)
        """
        
        await db_manager.execute_query(
            device_token_query,
            user_id,
            user_data.device_id,
            json.dumps({})
        )
        
        return SuccessResponse(
            message="User registered successfully",
            data={
                "user_id": str(user_id),
                "device_id": user_data.device_id
            }
        )
            
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.get("/profile/{device_id}", response_model=SuccessResponse)
async def get_user_profile(device_id: str):
    """Get user profile by device_id (using device_tokens relationship)"""
    try:
        # Query user via device_tokens table (new RDBMS relationship)
        query = """
            SELECT u.* FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        result = await db_manager.execute_query(query, device_id)
        
        if result:
            user = result[0]
            return SuccessResponse(
                message="User profile found",
                data={
                    "id": str(user["id"]),
                    "device_id": device_id,  # Include device_id for iOS app compatibility
                    "email": user["email"],
                    "keywords": user["keywords"] or [],
                    "preferred_sources": user["preferred_sources"] or [],
                    "notifications_enabled": user["notifications_enabled"],
                    "created_at": user["created_at"].isoformat(),
                    "updated_at": user["updated_at"].isoformat()
                }
            )
        else:
            raise HTTPException(status_code=404, detail="User profile not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

@router.get("/profile/exists/{device_id}", response_model=SuccessResponse)
async def check_profile_exists(device_id: str):
    """Check if user profile exists for device"""
    try:
        query = """
            SELECT COUNT(*) as count FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        result = await db_manager.execute_query(query, device_id)
        
        exists = result[0]["count"] > 0 if result else False
        
        return SuccessResponse(
            message="Profile existence checked",
            data={"exists": exists}
        )
            
    except Exception as e:
        logger.error(f"Error checking profile existence: {e}")
        raise HTTPException(status_code=500, detail="Failed to check profile existence")

@router.delete("/profile/{device_id}", response_model=SuccessResponse)
async def delete_user_profile(device_id: str):
    """Delete user profile and all associated data by device_id (GDPR compliance)"""
    try:
        # Find user via device_tokens relationship
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_id = user_result[0]["id"]
        
        # Delete user (CASCADE will handle related tables: device_tokens, saved_jobs, job_views, user_analytics)
        delete_query = "DELETE FROM iosapp.users WHERE id = $1 RETURNING id"
        delete_result = await db_manager.execute_query(delete_query, user_id)
        
        if delete_result:
            return SuccessResponse(
                message="User profile and all associated data deleted successfully",
                data={"deleted_user_id": str(user_id), "device_id": device_id}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete user profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user profile")

@router.delete("/profile", response_model=SuccessResponse)
async def delete_user_profile_body(request_data: Dict[str, Any]):
    """Delete user profile by device_id in request body (alternative endpoint)"""
    device_id = request_data.get("device_id")
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")
    return await delete_user_profile(device_id)

@router.put("/profile", response_model=SuccessResponse)
async def create_or_update_profile(profile_data: UserCreate):
    """Create or update user profile via device ID (PUT method)"""
    return await _create_or_update_profile_internal(profile_data)

@router.post("/profile", response_model=SuccessResponse)
async def create_or_update_profile_post(profile_data: UserCreate):
    """Create or update user profile via device ID (POST method)"""
    return await _create_or_update_profile_internal(profile_data)

async def _create_or_update_profile_internal(profile_data: UserCreate):
    """Create or update user profile via device ID"""
    try:
        # Validate device_id format to prevent bad data
        if not profile_data.device_id or not isinstance(profile_data.device_id, str):
            raise HTTPException(status_code=400, detail="device_id is required and must be a string")
        
        profile_data.device_id = profile_data.device_id.strip()
        
        if len(profile_data.device_id) < 8:
            raise HTTPException(status_code=400, detail="device_id must be at least 8 characters")
        
        # Validate email format if provided
        if profile_data.email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, profile_data.email):
                raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Validate keywords array
        if profile_data.keywords and not isinstance(profile_data.keywords, list):
            raise HTTPException(status_code=400, detail="keywords must be an array")
        
        # Limit keywords count and length
        if profile_data.keywords and len(profile_data.keywords) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 keywords allowed")
        
        for keyword in (profile_data.keywords or []):
            if not isinstance(keyword, str) or len(keyword.strip()) == 0:
                raise HTTPException(status_code=400, detail="Each keyword must be a non-empty string")
            if len(keyword) > 100:
                raise HTTPException(status_code=400, detail="Each keyword must be less than 100 characters")
        # First check if user exists via device_id
        check_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        existing_result = await db_manager.execute_query(check_query, profile_data.device_id)
        
        if existing_result:
            # Update existing user
            user_id = existing_result[0]["id"]
            update_query = """
                UPDATE iosapp.users 
                SET email = $1, keywords = $2, preferred_sources = $3, 
                    notifications_enabled = $4, updated_at = CURRENT_TIMESTAMP
                WHERE id = $5
                RETURNING *
            """
            result = await db_manager.execute_query(
                update_query, 
                profile_data.email,
                json.dumps(profile_data.keywords or []),
                json.dumps(profile_data.preferred_sources or []),
                profile_data.notifications_enabled,
                user_id
            )
            
            if result:
                user = result[0]
                return SuccessResponse(
                    message="Profile updated successfully",
                    data={
                        "id": str(user["id"]),
                        "device_id": profile_data.device_id,
                        "email": user["email"],
                        "keywords": user["keywords"] or [],
                        "preferred_sources": user["preferred_sources"] or [],
                        "notifications_enabled": user["notifications_enabled"],
                        "created_at": user["created_at"].isoformat(),
                        "updated_at": user["updated_at"].isoformat()
                    }
                )
        else:
            # Create new user and device token entry
            # First create user
            create_user_query = """
                INSERT INTO iosapp.users (email, keywords, preferred_sources, notifications_enabled)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (email) DO UPDATE SET
                    keywords = EXCLUDED.keywords,
                    preferred_sources = EXCLUDED.preferred_sources,
                    notifications_enabled = EXCLUDED.notifications_enabled,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
            """
            user_result = await db_manager.execute_query(
                create_user_query,
                profile_data.email,
                json.dumps(profile_data.keywords or []),
                json.dumps(profile_data.preferred_sources or []),
                profile_data.notifications_enabled
            )
            
            if user_result:
                user = user_result[0]
                
                # Only create device token entry if we have actual device info
                # Don't create entries with placeholder/temp data that could cause issues
                device_query = """
                    INSERT INTO iosapp.device_tokens (user_id, device_id, is_active)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (device_id) DO UPDATE SET 
                        user_id = EXCLUDED.user_id, 
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW()
                """
                
                # Create device entry without device_token - it will be added when APNs token is available
                await db_manager.execute_query(
                    device_query,
                    user["id"],
                    profile_data.device_id,
                    True  # Set as active, but no device_token yet
                )
                
                return SuccessResponse(
                    message="Profile created successfully",
                    data={
                        "id": str(user["id"]),
                        "device_id": profile_data.device_id,
                        "email": user["email"],
                        "keywords": user["keywords"] or [],
                        "preferred_sources": user["preferred_sources"] or [],
                        "notifications_enabled": user["notifications_enabled"],
                        "created_at": user["created_at"].isoformat(),
                        "updated_at": user["updated_at"].isoformat()
                    }
                )
            
        raise HTTPException(status_code=500, detail="Failed to create/update profile")
            
    except Exception as e:
        logger.error(f"Error creating/updating profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create/update profile")

@router.put("/{device_id}", response_model=SuccessResponse)
async def update_user(device_id: str, user_data: UserUpdate):
    """Update user by device_id"""
    try:
        # Build dynamic update query
        updates = []
        values = []
        
        if user_data.email is not None:
            updates.append("email = $" + str(len(values) + 1))
            values.append(user_data.email)
            
        if user_data.keywords is not None:
            updates.append("keywords = $" + str(len(values) + 1))
            values.append(json.dumps(user_data.keywords))
            
        if user_data.preferred_sources is not None:
            updates.append("preferred_sources = $" + str(len(values) + 1))
            values.append(json.dumps(user_data.preferred_sources))
            
        if user_data.notifications_enabled is not None:
            updates.append("notifications_enabled = $" + str(len(values) + 1))
            values.append(user_data.notifications_enabled)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(device_id)
        
        query = f"""
            UPDATE iosapp.users 
            SET {', '.join(updates)}
            FROM iosapp.device_tokens dt
            WHERE iosapp.users.id = dt.user_id 
            AND dt.device_id = ${len(values)}
            AND dt.is_active = true
            RETURNING iosapp.users.*
        """
        
        result = await db_manager.execute_query(query, *values)
        
        if result:
            user = result[0]
            return SuccessResponse(
                message="User updated successfully",
                data={
                    "id": str(user["id"]),
                    "device_id": device_id,
                    "updated_at": user["updated_at"].isoformat()
                }
            )
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

# =====================================
# Job Interaction (Simple)
# =====================================

@router.post("/save-job", response_model=SuccessResponse)
async def save_job(request: SaveJobRequest):
    """Save job for user"""
    try:
        # Check if user exists via device_tokens
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user_result[0]["id"]
        
        # Check if job already saved
        check_query = "SELECT id FROM iosapp.saved_jobs WHERE user_id = $1 AND job_id = $2"
        existing = await db_manager.execute_query(check_query, user_id, request.job_id)
        
        if existing:
            return SuccessResponse(
                message="Job already saved",
                data={"saved_job_id": str(existing[0]["id"])}
            )
        
        # Save job
        save_query = """
            INSERT INTO iosapp.saved_jobs (user_id, job_id)
            VALUES ($1, $2)
            RETURNING *
        """
        
        result = await db_manager.execute_query(save_query, user_id, request.job_id)
        
        if result:
            return SuccessResponse(
                message="Job saved successfully",
                data={"saved_job_id": str(result[0]["id"])}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save job")
            
    except Exception as e:
        logger.error(f"Error saving job: {e}")
        raise HTTPException(status_code=500, detail="Failed to save job")

@router.post("/view-job", response_model=SuccessResponse)
async def view_job(request: JobViewRequest):
    """Record job view"""
    try:
        # Check if user exists via device_tokens
        user_query = """
            SELECT u.id FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, request.device_id)
        
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user_result[0]["id"]
        
        # Record view
        view_query = """
            INSERT INTO iosapp.job_views (user_id, job_id)
            VALUES ($1, $2)
            RETURNING *
        """
        
        result = await db_manager.execute_query(view_query, user_id, request.job_id)
        
        if result:
            return SuccessResponse(
                message="Job view recorded",
                data={"view_id": str(result[0]["id"])}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to record view")
            
    except Exception as e:
        logger.error(f"Error recording job view: {e}")
        raise HTTPException(status_code=500, detail="Failed to record job view")