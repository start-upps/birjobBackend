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
            where_conditions.append(f"created_at >= NOW() - INTERVAL '{days} days'")
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Validate sort_by column
        valid_sort_columns = ["created_at", "title", "company", "source"]
        if sort_by not in valid_sort_columns:
            sort_by = "created_at"
        
        # Build ORDER BY clause
        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        
        # Build LIMIT and OFFSET
        param_count += 1
        limit_offset_clause = f"LIMIT ${param_count}"
        params.append(limit)
        
        param_count += 1
        limit_offset_clause += f" OFFSET ${param_count}"
        params.append(offset)
        
        # Build final query
        jobs_query = f"""
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at as posted_at
            FROM scraper.jobs_jobpost
            {where_clause}
            {order_clause}
            {limit_offset_clause}
        """
        
        # Get jobs
        jobs_result = await db_manager.execute_query(jobs_query, *params)
        
        # Get total count for pagination
        count_params = params[:-2]  # Remove limit and offset
        count_query = f"""
            SELECT COUNT(*) as total
            FROM scraper.jobs_jobpost
            {where_clause}
        """
        
        count_result = await db_manager.execute_query(count_query, *count_params)
        total_count = count_result[0]['total'] if count_result else 0
        
        # Format jobs data
        jobs_data = []
        for job in jobs_result:
            job_item = {
                "id": job['id'],
                "title": job['title'] or "No Title",
                "company": job['company'] or "Unknown Company",
                "apply_link": job['apply_link'] or "",
                "source": job['source'] or "Unknown",
                "posted_at": job['posted_at'].isoformat() if job['posted_at'] else None
            }
            jobs_data.append(job_item)
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        current_page = (offset // limit) + 1
        has_more = offset + limit < total_count
        has_previous = offset > 0
        
        return {
            "success": True,
            "data": {
                "jobs": jobs_data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "current_page": current_page,
                    "total_pages": total_pages,
                    "has_more": has_more,
                    "has_previous": has_previous
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
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get jobs"
        )

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_job_by_id(job_id: int):
    """Get a specific job by ID"""
    try:
        job_query = """
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at as posted_at
            FROM scraper.jobs_jobpost
            WHERE id = $1
        """
        
        job_result = await db_manager.execute_query(job_query, job_id)
        
        if not job_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job = job_result[0]
        job_data = {
            "id": job['id'],
            "title": job['title'] or "No Title",
            "company": job['company'] or "Unknown Company", 
            "apply_link": job['apply_link'] or "",
            "source": job['source'] or "Unknown",
            "posted_at": job['posted_at'].isoformat() if job['posted_at'] else None
        }
        
        return {
            "success": True,
            "data": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job"
        )

@router.get("/hash/{job_hash}", response_model=Dict[str, Any])
async def get_job_by_hash(job_hash: str):
    """Get a specific job by hash (for persistent notification references)"""
    try:
        # First, try to find the job by hash using title and company
        # This works even after truncate-and-load operations
        job_query = """
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at as posted_at
            FROM scraper.jobs_jobpost
            WHERE LOWER(TRIM(title)) || '|' || LOWER(TRIM(company)) = $1
               OR SUBSTRING(ENCODE(SHA256((LOWER(TRIM(title)) || '|' || LOWER(TRIM(company)))::bytea), 'hex'), 1, 32) = $2
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        # Try to find by reconstructed hash pattern or exact hash match
        job_result = await db_manager.execute_query(job_query, job_hash, job_hash)
        
        if not job_result:
            # If not found by hash, try alternative search by comparing all jobs
            fallback_query = """
                SELECT 
                    id,
                    title,
                    company,
                    apply_link,
                    source,
                    created_at as posted_at,
                    SUBSTRING(ENCODE(SHA256((LOWER(TRIM(title)) || '|' || LOWER(TRIM(company)))::bytea), 'hex'), 1, 32) as computed_hash
                FROM scraper.jobs_jobpost
                WHERE created_at >= NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 500
            """
            
            all_jobs = await db_manager.execute_query(fallback_query)
            
            # Find matching job by hash
            for job in all_jobs:
                if job.get('computed_hash') == job_hash:
                    job_result = [job]
                    break
        
        if not job_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found by hash. This may happen if the job is older than 30 days or has been removed."
            )
        
        job = job_result[0]
        job_data = {
            "id": job['id'],
            "title": job['title'] or "No Title",
            "company": job['company'] or "Unknown Company", 
            "apply_link": job['apply_link'] or "",
            "source": job['source'] or "Unknown",
            "posted_at": job['posted_at'].isoformat() if job['posted_at'] else None,
            "hash": job_hash,
            "found_by": "hash_lookup"
        }
        
        return {
            "success": True,
            "data": job_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job by hash {job_hash}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job by hash"
        )

@router.get("/sources/list", response_model=Dict[str, Any])  
async def get_job_sources():
    """Get list of available job sources"""
    try:
        sources_query = """
            SELECT 
                source,
                COUNT(*) as job_count,
                MAX(created_at) as last_updated
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY source
            ORDER BY job_count DESC
        """
        
        sources_result = await db_manager.execute_query(sources_query)
        
        sources_data = []
        for source in sources_result:
            sources_data.append({
                "name": source['source'],
                "job_count": source['job_count'],
                "last_updated": source['last_updated'].isoformat() if source['last_updated'] else None
            })
        
        return {
            "success": True,
            "data": {
                "sources": sources_data,
                "total_sources": len(sources_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting job sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job sources"
        )

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_job_stats():
    """Get job statistics"""
    try:
        stats_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(DISTINCT source) as total_sources,
                COUNT(DISTINCT company) as total_companies,
                MAX(created_at) as latest_job_date
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """
        
        stats_result = await db_manager.execute_query(stats_query)
        
        if stats_result:
            stats = stats_result[0]
            return {
                "success": True,
                "data": {
                    "total_jobs_30d": stats['total_jobs'],
                    "total_sources": stats['total_sources'],
                    "total_companies": stats['total_companies'],
                    "latest_job_date": stats['latest_job_date'].isoformat() if stats['latest_job_date'] else None,
                    "period": "last_30_days"
                }
            }
        else:
            return {
                "success": True,
                "data": {
                    "total_jobs_30d": 0,
                    "total_sources": 0,
                    "total_companies": 0,
                    "latest_job_date": None,
                    "period": "last_30_days"
                }
            }
        
    except Exception as e:
        logger.error(f"Error getting job stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job statistics"
        )