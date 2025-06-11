from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from app.core.database import get_db, db_manager
from app.models.device import JobMatch, DeviceToken
from app.schemas.device import JobMatchesResponse, MarkReadRequest, APIResponse
from app.core.redis_client import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{device_id}", response_model=JobMatchesResponse)
async def get_job_matches(
    device_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    since: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve recent job matches for a device"""
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )
    
    try:
        # Verify device exists
        stmt = select(DeviceToken).where(DeviceToken.id == device_uuid)
        result = await db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Build query for matches
        where_conditions = [JobMatch.device_id == device_uuid]
        
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                where_conditions.append(JobMatch.created_at >= since_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid since timestamp format"
                )
        
        # Get total count
        count_stmt = select(JobMatch).where(and_(*where_conditions))
        count_result = await db.execute(count_stmt)
        total_matches = len(count_result.scalars().all())
        
        # Get matches with pagination
        stmt = select(JobMatch).where(
            and_(*where_conditions)
        ).order_by(desc(JobMatch.created_at)).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        matches = result.scalars().all()
        
        # Get job details for each match from scraper schema
        match_data = []
        for match in matches:
            # Query job details from scraper schema
            job_query = """
                SELECT id, title, company, apply_link, source, posted_at
                FROM scraper.jobs_jobpost 
                WHERE id = $1
            """
            job_result = await db_manager.execute_query(job_query, int(match.job_id))
            
            if job_result:
                job = job_result[0]
                match_data.append({
                    "match_id": str(match.id),
                    "job": {
                        "id": job["id"],
                        "title": job["title"],
                        "company": job["company"],
                        "apply_link": job["apply_link"],
                        "source": job["source"],
                        "posted_at": job["posted_at"].isoformat() if job["posted_at"] else None
                    },
                    "matched_keywords": match.matched_keywords,
                    "relevance_score": float(match.relevance_score) if match.relevance_score else 0.0,
                    "matched_at": match.created_at.isoformat()
                })
        
        has_more = offset + limit < total_matches
        
        return JobMatchesResponse(
            data={
                "matches": match_data,
                "pagination": {
                    "total": total_matches,
                    "limit": limit,
                    "offset": offset,
                    "has_more": has_more
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job matches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job matches"
        )

@router.post("/{match_id}/read", response_model=APIResponse)
async def mark_match_as_read(
    match_id: str,
    device_id: str = Query(...),  # Query parameter to verify ownership
    db: AsyncSession = Depends(get_db)
):
    """Mark a job match as read/viewed"""
    try:
        match_uuid = uuid.UUID(match_id)
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    try:
        # Find and update match
        stmt = select(JobMatch).where(
            and_(
                JobMatch.id == match_uuid,
                JobMatch.device_id == device_uuid
            )
        )
        result = await db.execute(stmt)
        match = result.scalar_one_or_none()
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )
        
        if not match.is_read:
            match.is_read = True
            await db.commit()
            logger.info(f"Match marked as read: {match_id}")
        
        return APIResponse(message="Match marked as read")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking match as read: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark match as read"
        )

@router.get("/{device_id}/unread-count")
async def get_unread_count(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread matches for a device"""
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid device ID format"
        )
    
    try:
        stmt = select(JobMatch).where(
            and_(
                JobMatch.device_id == device_uuid,
                JobMatch.is_read == False
            )
        )
        result = await db.execute(stmt)
        unread_matches = result.scalars().all()
        
        return {
            "success": True,
            "data": {
                "unread_count": len(unread_matches)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting unread count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )