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
            # Auto-create user with email only
            create_query = """
                INSERT INTO iosapp.users (email, device_id, keywords, preferred_sources)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """
            fake_device_id = f"web_{email}_{int(datetime.now().timestamp())}"
            new_result = await db_manager.execute_query(
                create_query, email, fake_device_id, json.dumps([]), json.dumps([])
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
            current_keywords = result[0]["keywords"] or []
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
            current_keywords = result[0]["keywords"] or []
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

@router.post("/register", response_model=SuccessResponse)
async def register_user(user_data: UserCreate):
    """Register new user with device_id (iOS app)"""
    try:
        # Check if user already exists
        query = "SELECT * FROM iosapp.users WHERE device_id = $1"
        result = await db_manager.execute_query(query, user_data.device_id)
        
        if result:
            return SuccessResponse(
                message="User already exists",
                data={"user_id": str(result[0]["id"])}
            )
        
        # Create new user
        insert_query = """
            INSERT INTO iosapp.users (device_id, email, keywords, preferred_sources, notifications_enabled)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """
        
        new_result = await db_manager.execute_query(
            insert_query,
            user_data.device_id,
            user_data.email,
            json.dumps(user_data.keywords or []),
            json.dumps(user_data.preferred_sources or []),
            user_data.notifications_enabled
        )
        
        if new_result:
            user = new_result[0]
            return SuccessResponse(
                message="User created successfully",
                data={
                    "user_id": str(user["id"]),
                    "device_id": user["device_id"],
                    "created_at": user["created_at"].isoformat()
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create user")
            
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@router.get("/{device_id}", response_model=SuccessResponse)
async def get_user(device_id: str):
    """Get user by device_id"""
    try:
        query = "SELECT * FROM iosapp.users WHERE device_id = $1"
        result = await db_manager.execute_query(query, device_id)
        
        if result:
            user = result[0]
            return SuccessResponse(
                message="User found",
                data={
                    "id": str(user["id"]),
                    "device_id": user["device_id"],
                    "email": user["email"],
                    "keywords": user["keywords"] or [],
                    "preferred_sources": user["preferred_sources"] or [],
                    "notifications_enabled": user["notifications_enabled"],
                    "created_at": user["created_at"].isoformat(),
                    "updated_at": user["updated_at"].isoformat()
                }
            )
        else:
            raise HTTPException(status_code=404, detail="User not found")
            
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")

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
            WHERE device_id = ${len(values)}
            RETURNING *
        """
        
        result = await db_manager.execute_query(query, *values)
        
        if result:
            user = result[0]
            return SuccessResponse(
                message="User updated successfully",
                data={
                    "id": str(user["id"]),
                    "device_id": user["device_id"],
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
        # Check if user exists
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
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
        # Check if user exists
        user_query = "SELECT id FROM iosapp.users WHERE device_id = $1"
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