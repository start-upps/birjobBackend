from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.database import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=Dict[str, Any])
async def get_jobs(
    limit: int = Query(default=20, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(default=0, ge=0, description="Number of jobs to skip"),
    search: Optional[str] = Query(default=None, description="Search in title, company, or description"),
    company: Optional[str] = Query(default=None, description="Filter by company name"),
    source: Optional[str] = Query(default=None, description="Filter by job source"),
    location: Optional[str] = Query(default=None, description="Filter by location"),
    days: Optional[int] = Query(default=None, ge=1, le=365, description="Jobs posted within last N days"),
    sort_by: str = Query(default="created_at", description="Sort by: created_at, title, company"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="Sort order: asc or desc")
):
    """
    Get jobs from the scraper database with filtering, search, and pagination.
    This serves as the main job listing endpoint for the mobile app.
    """
    try:
        # Build WHERE conditions
        where_conditions = []
        params = []
        param_count = 0
        
        # Search functionality (only available columns)
        if search:
            param_count += 1
            where_conditions.append(f"""
                (LOWER(title) LIKE LOWER(${param_count}) 
                OR LOWER(company) LIKE LOWER(${param_count}))
            """)
            params.append(f"%{search}%")
        
        # Company filter
        if company:
            param_count += 1
            where_conditions.append(f"LOWER(company) LIKE LOWER(${param_count})")
            params.append(f"%{company}%")
        
        # Source filter
        if source:
            param_count += 1
            where_conditions.append(f"source = ${param_count}")
            params.append(source)
        
        # Location filter (search in title/company since no location column)
        if location:
            param_count += 1
            where_conditions.append(f"(LOWER(title) LIKE LOWER(${param_count}) OR LOWER(company) LIKE LOWER(${param_count}))")
            params.append(f"%{location}%")
        
        # Date filter
        if days:
            param_count += 1
            cutoff_date = datetime.now() - timedelta(days=days)
            where_conditions.append(f"created_at >= ${param_count}")
            params.append(cutoff_date)
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Validate sort_by field
        allowed_sort_fields = ["created_at", "title", "company", "id"]
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"
        
        # Build ORDER BY clause
        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(*) as total
            FROM scraper.jobs_jobpost
            {where_clause}
        """
        
        count_result = await db_manager.execute_query(count_query, *params)
        total_jobs = count_result[0]['total'] if count_result else 0
        
        # Get jobs with pagination
        param_count += 1
        limit_param = f"${param_count}"
        param_count += 1
        offset_param = f"${param_count}"
        
        jobs_query = f"""
            SELECT id, title, company, apply_link, source, created_at
            FROM scraper.jobs_jobpost
            {where_clause}
            {order_clause}
            LIMIT {limit_param} OFFSET {offset_param}
        """
        
        params.extend([limit, offset])
        jobs_result = await db_manager.execute_query(jobs_query, *params)
        
        # Format job data (only available columns)
        jobs = []
        for job in jobs_result:
            job_data = {
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "apply_link": job["apply_link"],
                "source": job["source"],
                "posted_at": job["created_at"].isoformat() if job["created_at"] else None
            }
            jobs.append(job_data)
        
        # Calculate pagination info
        has_more = offset + limit < total_jobs
        total_pages = (total_jobs + limit - 1) // limit  # Ceiling division
        current_page = (offset // limit) + 1
        
        return {
            "success": True,
            "data": {
                "jobs": jobs,
                "pagination": {
                    "total": total_jobs,
                    "limit": limit,
                    "offset": offset,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "has_more": has_more,
                    "has_previous": offset > 0
                },
                "filters": {
                    "search": search,
                    "company": company,
                    "source": source,
                    "location": location,
                    "days": days,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch jobs"
        )

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_details(job_id: int):
    """
    Get detailed information for a specific job by ID.
    """
    try:
        job_query = """
            SELECT id, title, company, apply_link, source, created_at
            FROM scraper.jobs_jobpost
            WHERE id = $1
        """
        
        result = await db_manager.execute_query(job_query, job_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job = result[0]
        job_data = {
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "apply_link": job["apply_link"],
            "source": job["source"],
            "posted_at": job["created_at"].isoformat() if job["created_at"] else None
        }
        
        return {
            "success": True,
            "data": {"job": job_data}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job details"
        )

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_job_stats():
    """
    Get job statistics and summary information for the app dashboard.
    """
    try:
        # Get total jobs count
        total_query = "SELECT COUNT(*) as total FROM scraper.jobs_jobpost"
        total_result = await db_manager.execute_query(total_query)
        total_jobs = total_result[0]['total'] if total_result else 0
        
        # Get jobs from last 24 hours
        recent_query = """
            SELECT COUNT(*) as recent
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """
        recent_result = await db_manager.execute_query(recent_query)
        recent_jobs = recent_result[0]['recent'] if recent_result else 0
        
        # Get top companies
        companies_query = """
            SELECT company, COUNT(*) as job_count
            FROM scraper.jobs_jobpost
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT 10
        """
        companies_result = await db_manager.execute_query(companies_query)
        top_companies = [{"company": row["company"], "job_count": row["job_count"]} for row in companies_result]
        
        # Get job sources
        sources_query = """
            SELECT source, COUNT(*) as job_count
            FROM scraper.jobs_jobpost
            GROUP BY source
            ORDER BY job_count DESC
        """
        sources_result = await db_manager.execute_query(sources_query)
        job_sources = [{"source": row["source"], "job_count": row["job_count"]} for row in sources_result]
        
        return {
            "success": True,
            "data": {
                "total_jobs": total_jobs,
                "recent_jobs_24h": recent_jobs,
                "top_companies": top_companies,
                "job_sources": job_sources,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching job stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job statistics"
        )

# Job Management Endpoints for RDBMS Schema

@router.post("/save", response_model=Dict[str, Any])
async def save_job(job_data: Dict[str, Any]):
    """Save a job for user (uses device_id to find user via RDBMS relationship)"""
    try:
        device_id = job_data.get("device_id")
        job_id = job_data.get("job_id")
        
        if not device_id or not job_id:
            raise HTTPException(status_code=400, detail="device_id and job_id are required")
        
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
        
        # Get job details for caching
        job_details = await get_job_details(job_id)
        
        # Insert saved job with foreign key relationship
        save_query = """
            INSERT INTO iosapp.saved_jobs (user_id, job_id, job_title, job_company, job_source)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id, job_id) DO NOTHING
            RETURNING id
        """
        result = await db_manager.execute_query(
            save_query, 
            user_id, 
            job_id,
            job_details.get("title", ""),
            job_details.get("company", ""),
            job_details.get("source", "")
        )
        
        if result:
            return {"success": True, "message": "Job saved successfully"}
        else:
            return {"success": True, "message": "Job already saved"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving job: {e}")
        raise HTTPException(status_code=500, detail="Failed to save job")

@router.delete("/unsave", response_model=Dict[str, Any])
async def unsave_job(job_data: Dict[str, Any]):
    """Remove saved job for user"""
    try:
        device_id = job_data.get("device_id")
        job_id = job_data.get("job_id")
        
        if not device_id or not job_id:
            raise HTTPException(status_code=400, detail="device_id and job_id are required")
        
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
        
        # Delete saved job
        delete_query = """
            DELETE FROM iosapp.saved_jobs 
            WHERE user_id = $1 AND job_id = $2
            RETURNING id
        """
        result = await db_manager.execute_query(delete_query, user_id, job_id)
        
        if result:
            return {"success": True, "message": "Job unsaved successfully"}
        else:
            raise HTTPException(status_code=404, detail="Saved job not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsaving job: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsave job")

@router.get("/saved/{device_id}", response_model=Dict[str, Any])
async def get_saved_jobs(device_id: str):
    """Get all saved jobs for user via device_id"""
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
        
        # Get saved jobs with cached details
        saved_jobs_query = """
            SELECT job_id, job_title, job_company, job_source, created_at
            FROM iosapp.saved_jobs
            WHERE user_id = $1
            ORDER BY created_at DESC
        """
        saved_jobs = await db_manager.execute_query(saved_jobs_query, user_id)
        
        saved_jobs_data = []
        for job in saved_jobs:
            saved_jobs_data.append({
                "job_id": job["job_id"],
                "job_title": job["job_title"],
                "job_company": job["job_company"],
                "job_source": job["job_source"],
                "saved_at": job["created_at"].isoformat()
            })
        
        return {
            "success": True,
            "data": {"saved_jobs": saved_jobs_data}
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get saved jobs")

@router.post("/view", response_model=Dict[str, Any])
async def record_job_view(view_data: Dict[str, Any]):
    """Record job view for analytics with RDBMS foreign key"""
    try:
        device_id = view_data.get("device_id")
        job_id = view_data.get("job_id")
        view_duration = view_data.get("view_duration_seconds", 0)
        
        if not device_id or not job_id:
            raise HTTPException(status_code=400, detail="device_id and job_id are required")
        
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
        
        # Get job details for caching
        job_details = await get_job_details(job_id)
        
        # Record job view with foreign key relationship
        view_query = """
            INSERT INTO iosapp.job_views (user_id, job_id, job_title, job_company, job_source, view_duration_seconds)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        result = await db_manager.execute_query(
            view_query, 
            user_id, 
            job_id,
            job_details.get("title", ""),
            job_details.get("company", ""),
            job_details.get("source", ""),
            view_duration
        )
        
        if result:
            return {"success": True, "message": "Job view recorded"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record job view")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording job view: {e}")
        raise HTTPException(status_code=500, detail="Failed to record job view")

async def get_job_details(job_id: int) -> Dict[str, Any]:
    """Helper function to get job details for caching"""
    try:
        job_query = """
            SELECT title, company, source
            FROM scraper.jobs_jobpost
            WHERE id = $1
        """
        result = await db_manager.execute_query(job_query, job_id)
        
        if result:
            job = result[0]
            return {
                "title": job["title"],
                "company": job["company"],
                "source": job["source"]
            }
        else:
            return {"title": "", "company": "", "source": "unknown"}
            
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        return {"title": "", "company": "", "source": "unknown"}