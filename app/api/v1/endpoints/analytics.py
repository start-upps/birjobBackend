from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.database import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/jobs/overview", response_model=Dict[str, Any])
async def get_jobs_overview():
    """Get overall job statistics from current scraping cycle"""
    try:
        # Total jobs (current scraping cycle only)
        total_query = "SELECT COUNT(*) as count FROM scraper.jobs_jobpost"
        total_result = await db_manager.execute_query(total_query)
        total_jobs = total_result[0]["count"] if total_result else 0
        
        # Since data is refreshed every cycle, all jobs are from current cycle
        # Get scraping cycle info
        cycle_info_query = """
            SELECT 
                MIN(created_at) as cycle_start,
                MAX(created_at) as cycle_end,
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as unique_sources
            FROM scraper.jobs_jobpost
        """
        cycle_result = await db_manager.execute_query(cycle_info_query)
        cycle_data = cycle_result[0] if cycle_result else {
            "cycle_start": None, "cycle_end": None, "total_jobs": 0, 
            "unique_companies": 0, "unique_sources": 0
        }
        
        return {
            "total_jobs": cycle_data["total_jobs"],
            "unique_companies": cycle_data["unique_companies"],
            "unique_sources": cycle_data["unique_sources"],
            "cycle_start": cycle_data["cycle_start"].isoformat() if cycle_data["cycle_start"] else None,
            "cycle_end": cycle_data["cycle_end"].isoformat() if cycle_data["cycle_end"] else None,
            "data_freshness": "current_cycle_only",
            "note": "Data is refreshed every 4-5 hours by scraper",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting jobs overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get jobs overview"
        )

@router.get("/jobs/by-source", response_model=Dict[str, Any])
async def get_jobs_by_source():
    """Get job distribution by source from current scraping cycle"""
    try:
        query = """
            SELECT 
                source,
                COUNT(*) as job_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage,
                MIN(created_at) as first_job,
                MAX(created_at) as latest_job
            FROM scraper.jobs_jobpost 
            GROUP BY source
            ORDER BY job_count DESC
        """
        
        result = await db_manager.execute_query(query)
        
        sources_data = []
        for row in result:
            sources_data.append({
                "source": row["source"],
                "job_count": row["job_count"],
                "percentage": round(float(row["percentage"]), 2) if row["percentage"] else 0,
                "first_job": row["first_job"].isoformat() if row["first_job"] else None,
                "latest_job": row["latest_job"].isoformat() if row["latest_job"] else None
            })
        
        return {
            "sources": sources_data,
            "total_sources": len(sources_data),
            "data_freshness": "current_cycle_only",
            "note": "All data from current scraping cycle (refreshed every 4-5 hours)",
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
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get top companies by job count from current scraping cycle"""
    try:
        query = """
            SELECT 
                company,
                COUNT(*) as job_count,
                MIN(created_at) as first_job,
                MAX(created_at) as latest_job
            FROM scraper.jobs_jobpost 
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT %s
        """ % limit
        
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
            "companies": companies_data,
            "limit": limit,
            "data_freshness": "current_cycle_only",
            "note": "All data from current scraping cycle (refreshed every 4-5 hours)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting top companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get top companies"
        )

@router.get("/jobs/current-cycle", response_model=Dict[str, Any])
async def get_current_cycle_analysis():
    """Get analysis of current scraping cycle (replaces trends since no historical data)"""
    try:
        # Get cycle overview
        overview_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as unique_sources,
                MIN(created_at) as cycle_start,
                MAX(created_at) as cycle_end
            FROM scraper.jobs_jobpost
        """
        overview_result = await db_manager.execute_query(overview_query)
        overview = overview_result[0] if overview_result else {}
        
        # Get hourly distribution within current cycle
        hourly_query = """
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as job_count
            FROM scraper.jobs_jobpost 
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """
        hourly_result = await db_manager.execute_query(hourly_query)
        
        hourly_data = []
        for row in hourly_result:
            hourly_data.append({
                "hour": int(row["hour"]),
                "job_count": row["job_count"]
            })
        
        # Get top source analysis
        source_analysis_query = """
            SELECT 
                source,
                COUNT(*) as job_count,
                COUNT(DISTINCT company) as companies_per_source,
                MIN(created_at) as first_job,
                MAX(created_at) as last_job
            FROM scraper.jobs_jobpost 
            GROUP BY source
            ORDER BY job_count DESC
            LIMIT 10
        """
        source_result = await db_manager.execute_query(source_analysis_query)
        
        source_analysis = []
        for row in source_result:
            source_analysis.append({
                "source": row["source"],
                "job_count": row["job_count"],
                "companies_per_source": row["companies_per_source"],
                "first_job": row["first_job"].isoformat() if row["first_job"] else None,
                "last_job": row["last_job"].isoformat() if row["last_job"] else None
            })
        
        # Calculate cycle duration
        cycle_duration = None
        if overview.get("cycle_start") and overview.get("cycle_end"):
            duration = overview["cycle_end"] - overview["cycle_start"]
            cycle_duration = str(duration)
        
        return {
            "cycle_overview": {
                "total_jobs": overview.get("total_jobs", 0),
                "unique_companies": overview.get("unique_companies", 0),
                "unique_sources": overview.get("unique_sources", 0),
                "cycle_start": overview["cycle_start"].isoformat() if overview.get("cycle_start") else None,
                "cycle_end": overview["cycle_end"].isoformat() if overview.get("cycle_end") else None,
                "cycle_duration": cycle_duration
            },
            "hourly_distribution": hourly_data,
            "source_analysis": source_analysis,
            "data_freshness": "current_cycle_only",
            "note": "Analysis of current scraping cycle. Historical trends not available due to data refresh cycle.",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current cycle analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current cycle analysis"
        )

@router.get("/jobs/keywords", response_model=Dict[str, Any])
async def get_popular_keywords(
    limit: int = Query(default=50, ge=10, le=200)
):
    """Get most popular keywords in job titles from current scraping cycle"""
    try:
        query = """
            WITH words AS (
                SELECT 
                    LOWER(TRIM(word)) as keyword,
                    COUNT(*) as frequency
                FROM scraper.jobs_jobpost,
                LATERAL unnest(string_to_array(title, ' ')) AS word
                WHERE LENGTH(TRIM(word)) > 2
                AND TRIM(word) !~ '^[0-9]+$'
                GROUP BY LOWER(TRIM(word))
            )
            SELECT keyword, frequency
            FROM words
            WHERE keyword NOT IN ('və', 'üzrə', 'the', 'and', 'for', 'with', 'at', 'in', 'on', 'to', 'of', 'a', 'an')
            ORDER BY frequency DESC
            LIMIT %s
        """ % limit
        
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
            "keywords": keywords_data,
            "total_keywords": len(keywords_data),
            "total_word_frequency": total_frequency,
            "data_freshness": "current_cycle_only",
            "note": "Keywords from current scraping cycle (refreshed every 4-5 hours)",
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
    keyword: str = Query(..., min_length=2)
):
    """Search and analyze jobs containing specific keyword from current scraping cycle"""
    try:
        # Search jobs
        search_query = """
            SELECT 
                COUNT(*) as total_matches,
                COUNT(DISTINCT company) as unique_companies,
                COUNT(DISTINCT source) as unique_sources
            FROM scraper.jobs_jobpost 
            WHERE (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)
        """ % (f"'%{keyword.lower()}%'", f"'%{keyword.lower()}%'")
        
        search_result = await db_manager.execute_query(search_query)
        search_data = search_result[0] if search_result else {"total_matches": 0, "unique_companies": 0, "unique_sources": 0}
        
        # Top companies for this keyword
        companies_query = """
            SELECT company, COUNT(*) as job_count
            FROM scraper.jobs_jobpost 
            WHERE (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT 10
        """ % (f"'%{keyword.lower()}%'", f"'%{keyword.lower()}%'")
        
        companies_result = await db_manager.execute_query(companies_query)
        companies_data = [{"company": row["company"], "job_count": row["job_count"]} for row in companies_result]
        
        # Sources for this keyword
        sources_query = """
            SELECT source, COUNT(*) as job_count
            FROM scraper.jobs_jobpost 
            WHERE (LOWER(title) LIKE %s OR LOWER(company) LIKE %s)
            GROUP BY source
            ORDER BY job_count DESC
        """ % (f"'%{keyword.lower()}%'", f"'%{keyword.lower()}%'")
        
        sources_result = await db_manager.execute_query(sources_query)
        sources_data = [{"source": row["source"], "job_count": row["job_count"]} for row in sources_result]
        
        # Calculate match percentage
        total_jobs_query = "SELECT COUNT(*) as total FROM scraper.jobs_jobpost"
        total_jobs_result = await db_manager.execute_query(total_jobs_query)
        total_jobs = total_jobs_result[0]["total"] if total_jobs_result else 0
        
        match_percentage = round((search_data["total_matches"] / total_jobs * 100), 2) if total_jobs > 0 else 0
        
        return {
            "keyword": keyword,
            "total_matches": search_data["total_matches"],
            "unique_companies": search_data["unique_companies"],
            "unique_sources": search_data["unique_sources"],
            "match_percentage": match_percentage,
            "total_jobs_in_cycle": total_jobs,
            "top_companies": companies_data,
            "sources": sources_data,
            "data_freshness": "current_cycle_only",
            "note": "Search results from current scraping cycle (refreshed every 4-5 hours)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search jobs analytics"
        )