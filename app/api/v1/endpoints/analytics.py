from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.database import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/jobs/overview", response_model=Dict[str, Any])
async def get_jobs_overview():
    """Get overall job statistics"""
    try:
        # Total jobs
        total_query = "SELECT COUNT(*) as count FROM scraper.jobs_jobpost"
        total_result = await db_manager.execute_query(total_query)
        total_jobs = total_result[0]["count"] if total_result else 0
        
        # Jobs by time periods
        periods_query = """
            SELECT 
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as last_week,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days') as last_month
            FROM scraper.jobs_jobpost
        """
        periods_result = await db_manager.execute_query(periods_query)
        periods = periods_result[0] if periods_result else {"last_24h": 0, "last_week": 0, "last_month": 0}
        
        # Unique companies and sources
        unique_query = """
            SELECT 
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as unique_sources
            FROM scraper.jobs_jobpost
        """
        unique_result = await db_manager.execute_query(unique_query)
        unique_data = unique_result[0] if unique_result else {"unique_companies": 0, "unique_sources": 0}
        
        return {
            "total_jobs": total_jobs,
            "jobs_last_24h": periods["last_24h"],
            "jobs_last_week": periods["last_week"], 
            "jobs_last_month": periods["last_month"],
            "unique_companies": unique_data["unique_companies"],
            "unique_sources": unique_data["unique_sources"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting jobs overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get jobs overview"
        )

@router.get("/jobs/by-source", response_model=Dict[str, Any])
async def get_jobs_by_source(days: int = Query(default=7, ge=1, le=365)):
    """Get job distribution by source"""
    try:
        query = """
            SELECT 
                source,
                COUNT(*) as job_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage,
                MAX(created_at) as latest_job
            FROM scraper.jobs_jobpost 
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY source
            ORDER BY job_count DESC
        """ % days
        
        result = await db_manager.execute_query(query)
        
        sources_data = []
        for row in result:
            sources_data.append({
                "source": row["source"],
                "job_count": row["job_count"],
                "percentage": float(row["percentage"]) if row["percentage"] else 0,
                "latest_job": row["latest_job"].isoformat() if row["latest_job"] else None
            })
        
        return {
            "period_days": days,
            "sources": sources_data,
            "total_sources": len(sources_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting jobs by source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get jobs by source"
        )

@router.get("/jobs/by-company", response_model=Dict[str, Any])
async def get_top_companies(
    limit: int = Query(default=20, ge=1, le=100),
    days: int = Query(default=30, ge=1, le=365)
):
    """Get top companies by job count"""
    try:
        query = """
            SELECT 
                company,
                COUNT(*) as job_count,
                MIN(created_at) as first_job,
                MAX(created_at) as latest_job
            FROM scraper.jobs_jobpost 
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT %s
        """ % (days, limit)
        
        result = await db_manager.execute_query(query)
        
        companies_data = []
        for row in result:
            companies_data.append({
                "company": row["company"],
                "job_count": row["job_count"],
                "first_job": row["first_job"].isoformat() if row["first_job"] else None,
                "latest_job": row["latest_job"].isoformat() if row["latest_job"] else None
            })
        
        return {
            "period_days": days,
            "companies": companies_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting top companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top companies"
        )

@router.get("/jobs/trends", response_model=Dict[str, Any])
async def get_job_trends(days: int = Query(default=30, ge=7, le=365)):
    """Get job posting trends over time"""
    try:
        query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as job_count,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as active_sources
            FROM scraper.jobs_jobpost 
            WHERE created_at > NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """ % days
        
        result = await db_manager.execute_query(query)
        
        trends_data = []
        for row in result:
            trends_data.append({
                "date": row["date"].isoformat() if row["date"] else None,
                "job_count": row["job_count"],
                "unique_companies": row["unique_companies"],
                "active_sources": row["active_sources"]
            })
        
        # Calculate averages
        if trends_data:
            avg_jobs_per_day = sum(d["job_count"] for d in trends_data) / len(trends_data)
            avg_companies_per_day = sum(d["unique_companies"] for d in trends_data) / len(trends_data)
        else:
            avg_jobs_per_day = avg_companies_per_day = 0
        
        return {
            "period_days": days,
            "daily_data": trends_data,
            "avg_jobs_per_day": round(avg_jobs_per_day, 2),
            "avg_companies_per_day": round(avg_companies_per_day, 2),
            "total_days": len(trends_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting job trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job trends"
        )

@router.get("/jobs/keywords", response_model=Dict[str, Any])
async def get_popular_keywords(
    limit: int = Query(default=50, ge=10, le=200),
    days: int = Query(default=30, ge=1, le=365)
):
    """Get most popular keywords in job titles"""
    try:
        query = """
            WITH words AS (
                SELECT 
                    LOWER(TRIM(word)) as keyword,
                    COUNT(*) as frequency
                FROM scraper.jobs_jobpost,
                LATERAL unnest(string_to_array(title, ' ')) AS word
                WHERE created_at > NOW() - INTERVAL '%s days'
                AND LENGTH(TRIM(word)) > 2
                AND TRIM(word) !~ '^[0-9]+$'
                GROUP BY LOWER(TRIM(word))
            )
            SELECT keyword, frequency
            FROM words
            WHERE keyword NOT IN ('və', 'üzrə', 'the', 'and', 'for', 'with', 'at', 'in', 'on', 'to', 'of', 'a', 'an')
            ORDER BY frequency DESC
            LIMIT %s
        """ % (days, limit)
        
        result = await db_manager.execute_query(query)
        
        keywords_data = []
        total_frequency = 0
        for row in result:
            keywords_data.append({
                "keyword": row["keyword"],
                "frequency": row["frequency"]
            })
            total_frequency += row["frequency"]
        
        # Add percentages
        for item in keywords_data:
            item["percentage"] = round((item["frequency"] / total_frequency * 100), 2) if total_frequency > 0 else 0
        
        return {
            "period_days": days,
            "keywords": keywords_data,
            "total_keywords": len(keywords_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting popular keywords: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular keywords"
        )

@router.get("/jobs/search", response_model=Dict[str, Any])
async def search_jobs_analytics(
    keyword: str = Query(..., min_length=2),
    days: int = Query(default=30, ge=1, le=365)
):
    """Search and analyze jobs containing specific keyword"""
    try:
        # Search jobs
        search_query = """
            SELECT 
                COUNT(*) as total_matches,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as unique_sources
            FROM scraper.jobs_jobpost 
            WHERE (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)
            AND created_at > NOW() - INTERVAL '%s days'
        """ % (f"'%{keyword.lower()}%'", f"'%{keyword.lower()}%'", days)
        
        search_result = await db_manager.execute_query(search_query)
        search_data = search_result[0] if search_result else {"total_matches": 0, "unique_companies": 0, "unique_sources": 0}
        
        # Top companies for this keyword
        companies_query = """
            SELECT company, COUNT(*) as job_count
            FROM scraper.jobs_jobpost 
            WHERE (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)
            AND created_at > NOW() - INTERVAL '%s days'
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT 10
        """ % (f"'%{keyword.lower()}%'", f"'%{keyword.lower()}%'", days)
        
        companies_result = await db_manager.execute_query(companies_query)
        companies_data = [{"company": row["company"], "job_count": row["job_count"]} for row in companies_result]
        
        # Sources for this keyword
        sources_query = """
            SELECT source, COUNT(*) as job_count
            FROM scraper.jobs_jobpost 
            WHERE (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)
            AND created_at > NOW() - INTERVAL '%s days'
            GROUP BY source
            ORDER BY job_count DESC
        """ % (f"'%{keyword.lower()}%'", f"'%{keyword.lower()}%'", days)
        
        sources_result = await db_manager.execute_query(sources_query)
        sources_data = [{"source": row["source"], "job_count": row["job_count"]} for row in sources_result]
        
        return {
            "keyword": keyword,
            "period_days": days,
            "total_matches": search_data["total_matches"],
            "unique_companies": search_data["unique_companies"],
            "unique_sources": search_data["unique_sources"],
            "top_companies": companies_data,
            "sources": sources_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search jobs analytics"
        )