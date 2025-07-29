"""
Job Market Analytics Endpoints
Real-time insights from scraped job data (current snapshot)
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging

from app.core.database import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/market-overview")
async def get_market_overview():
    """
    Get high-level job market overview
    Real-time snapshot of current job market state
    """
    try:
        # Basic market metrics
        queries = {
            "total_jobs": "SELECT COUNT(*) as count FROM scraper.jobs_jobpost",
            "unique_companies": "SELECT COUNT(DISTINCT company) as count FROM scraper.jobs_jobpost",
            "unique_sources": "SELECT COUNT(DISTINCT source) as count FROM scraper.jobs_jobpost",
            "data_freshness": "SELECT MIN(created_at) as oldest, MAX(created_at) as newest FROM scraper.jobs_jobpost"
        }
        
        results = {}
        for key, query in queries.items():
            result = await db_manager.execute_query(query)
            if key == "data_freshness":
                results[key] = {
                    "oldest": result[0]["oldest"].isoformat() if result[0]["oldest"] else None,
                    "newest": result[0]["newest"].isoformat() if result[0]["newest"] else None
                }
            else:
                results[key] = result[0]["count"] if result else 0
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "market_overview": results,
            "data_note": "Live snapshot - data refreshed hourly"
        }
        
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market overview")

@router.get("/source-analytics")
async def get_source_analytics():
    """
    Analyze job volume and distribution by source
    Shows which sources are most active
    """
    try:
        # Volume by source
        volume_query = """
            SELECT source, 
                   COUNT(*) as job_count,
                   COUNT(DISTINCT company) as unique_companies,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scraper.jobs_jobpost), 2) as percentage
            FROM scraper.jobs_jobpost
            GROUP BY source
            ORDER BY job_count DESC
        """
        
        volume_result = await db_manager.execute_query(volume_query)
        
        # Source diversity score (companies per source)
        diversity_query = """
            SELECT source,
                   COUNT(*) as total_jobs,
                   COUNT(DISTINCT company) as unique_companies,
                   ROUND(COUNT(DISTINCT company) * 100.0 / COUNT(*), 2) as diversity_score
            FROM scraper.jobs_jobpost
            GROUP BY source
            ORDER BY diversity_score DESC
        """
        
        diversity_result = await db_manager.execute_query(diversity_query)
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "source_volume": [dict(row) for row in volume_result],
            "source_diversity": [dict(row) for row in diversity_result],
            "insights": {
                "total_sources": len(volume_result),
                "top_source": volume_result[0]["source"] if volume_result else None,
                "most_diverse_source": diversity_result[0]["source"] if diversity_result else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting source analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get source analytics")

@router.get("/company-analytics")
async def get_company_analytics(
    limit: int = Query(default=20, ge=1, le=100, description="Number of companies to return")
):
    """
    Analyze company hiring activity and market presence
    Shows which companies are hiring most actively
    """
    try:
        # Top hiring companies
        top_companies_query = """
            SELECT company,
                   COUNT(*) as job_count,
                   COUNT(DISTINCT source) as sources_used,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scraper.jobs_jobpost), 2) as market_share
            FROM scraper.jobs_jobpost
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT $1
        """
        
        top_companies = await db_manager.execute_query(top_companies_query, limit)
        
        # Company distribution analysis
        distribution_query = """
            WITH company_job_counts AS (
                SELECT company, COUNT(*) as job_count
                FROM scraper.jobs_jobpost
                GROUP BY company
            )
            SELECT 
                CASE 
                    WHEN job_count >= 50 THEN 'Large Hirers (50+)'
                    WHEN job_count >= 20 THEN 'Medium Hirers (20-49)'
                    WHEN job_count >= 5 THEN 'Small Hirers (5-19)'
                    ELSE 'Minimal Hirers (1-4)'
                END as hiring_category,
                COUNT(*) as company_count,
                SUM(job_count) as total_jobs,
                ROUND(AVG(job_count), 2) as avg_jobs_per_company
            FROM company_job_counts
            GROUP BY hiring_category
            ORDER BY MIN(job_count) DESC
        """
        
        distribution_result = await db_manager.execute_query(distribution_query)
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "top_companies": [dict(row) for row in top_companies],
            "hiring_distribution": [dict(row) for row in distribution_result],
            "insights": {
                "total_companies": len(top_companies),
                "top_hirer": top_companies[0]["company"] if top_companies else None,
                "concentration_note": "Market concentration analysis based on current snapshot"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting company analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get company analytics")

@router.get("/title-analytics")
async def get_title_analytics(
    limit: int = Query(default=30, ge=1, le=100, description="Number of titles to return")
):
    """
    Analyze job titles and role demand patterns
    Shows trending roles and skill demands
    """
    try:
        # Most common exact titles
        exact_titles_query = """
            SELECT title,
                   COUNT(*) as job_count,
                   COUNT(DISTINCT company) as company_count,
                   COUNT(DISTINCT source) as source_count
            FROM scraper.jobs_jobpost
            GROUP BY title
            ORDER BY job_count DESC
            LIMIT $1
        """
        
        exact_titles = await db_manager.execute_query(exact_titles_query, limit)
        
        # Role pattern analysis (keyword extraction)
        role_patterns_query = """
            SELECT 
                CASE 
                    WHEN LOWER(title) LIKE '%senior%' OR LOWER(title) LIKE '%sr%' THEN 'Senior Level'
                    WHEN LOWER(title) LIKE '%junior%' OR LOWER(title) LIKE '%jr%' THEN 'Junior Level'
                    WHEN LOWER(title) LIKE '%lead%' OR LOWER(title) LIKE '%principal%' THEN 'Lead Level'
                    WHEN LOWER(title) LIKE '%manager%' OR LOWER(title) LIKE '%mgr%' THEN 'Management'
                    ELSE 'Mid Level'
                END as experience_level,
                COUNT(*) as job_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scraper.jobs_jobpost), 2) as percentage
            FROM scraper.jobs_jobpost
            GROUP BY experience_level
            ORDER BY job_count DESC
        """
        
        role_patterns = await db_manager.execute_query(role_patterns_query)
        
        # Technology/domain analysis
        tech_patterns_query = """
            SELECT 
                CASE 
                    WHEN LOWER(title) LIKE '%java%' THEN 'Java'
                    WHEN LOWER(title) LIKE '%python%' THEN 'Python'
                    WHEN LOWER(title) LIKE '%react%' OR LOWER(title) LIKE '%frontend%' THEN 'Frontend'
                    WHEN LOWER(title) LIKE '%backend%' OR LOWER(title) LIKE '%api%' THEN 'Backend'
                    WHEN LOWER(title) LIKE '%devops%' OR LOWER(title) LIKE '%cloud%' THEN 'DevOps'
                    WHEN LOWER(title) LIKE '%data%' OR LOWER(title) LIKE '%analyst%' THEN 'Data'
                    WHEN LOWER(title) LIKE '%qa%' OR LOWER(title) LIKE '%test%' THEN 'QA/Testing'
                    WHEN LOWER(title) LIKE '%mobile%' OR LOWER(title) LIKE '%ios%' OR LOWER(title) LIKE '%android%' THEN 'Mobile'
                    ELSE 'Other'
                END as tech_domain,
                COUNT(*) as job_count
            FROM scraper.jobs_jobpost
            GROUP BY tech_domain
            ORDER BY job_count DESC
        """
        
        tech_patterns = await db_manager.execute_query(tech_patterns_query)
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "popular_titles": [dict(row) for row in exact_titles],
            "experience_levels": [dict(row) for row in role_patterns],
            "technology_domains": [dict(row) for row in tech_patterns],
            "insights": {
                "total_unique_titles": len(exact_titles),
                "most_common_title": exact_titles[0]["title"] if exact_titles else None,
                "title_diversity_note": "Based on exact title matches from current snapshot"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting title analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get title analytics")

@router.get("/keyword-trends")
async def get_keyword_trends():
    """
    Analyze trending keywords and skills in job titles
    Shows what skills are most in demand
    """
    try:
        # Technology keywords
        tech_keywords_query = """
            SELECT 
                keyword,
                COUNT(*) as mention_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scraper.jobs_jobpost), 2) as percentage
            FROM (
                SELECT 
                    CASE 
                        WHEN LOWER(title) LIKE '%javascript%' OR LOWER(title) LIKE '%js%' THEN 'JavaScript'
                        WHEN LOWER(title) LIKE '%python%' THEN 'Python'
                        WHEN LOWER(title) LIKE '%java%' AND LOWER(title) NOT LIKE '%javascript%' THEN 'Java'
                        WHEN LOWER(title) LIKE '%react%' THEN 'React'
                        WHEN LOWER(title) LIKE '%angular%' THEN 'Angular'
                        WHEN LOWER(title) LIKE '%vue%' THEN 'Vue'
                        WHEN LOWER(title) LIKE '%node%' THEN 'Node.js'
                        WHEN LOWER(title) LIKE '%aws%' THEN 'AWS'
                        WHEN LOWER(title) LIKE '%azure%' THEN 'Azure'
                        WHEN LOWER(title) LIKE '%docker%' THEN 'Docker'
                        WHEN LOWER(title) LIKE '%kubernetes%' THEN 'Kubernetes'
                        WHEN LOWER(title) LIKE '%sql%' THEN 'SQL'
                        WHEN LOWER(title) LIKE '%mongodb%' THEN 'MongoDB'
                        WHEN LOWER(title) LIKE '%redis%' THEN 'Redis'
                        WHEN LOWER(title) LIKE '%elasticsearch%' THEN 'Elasticsearch'
                        ELSE NULL
                    END as keyword
                FROM scraper.jobs_jobpost
            ) keywords
            WHERE keyword IS NOT NULL
            GROUP BY keyword
            ORDER BY mention_count DESC
        """
        
        tech_keywords = await db_manager.execute_query(tech_keywords_query)
        
        # Role-based keywords
        role_keywords_query = """
            SELECT 
                keyword,
                COUNT(*) as mention_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scraper.jobs_jobpost), 2) as percentage
            FROM (
                SELECT 
                    CASE 
                        WHEN LOWER(title) LIKE '%engineer%' THEN 'Engineer'
                        WHEN LOWER(title) LIKE '%developer%' THEN 'Developer'
                        WHEN LOWER(title) LIKE '%manager%' THEN 'Manager'
                        WHEN LOWER(title) LIKE '%analyst%' THEN 'Analyst'
                        WHEN LOWER(title) LIKE '%architect%' THEN 'Architect'
                        WHEN LOWER(title) LIKE '%consultant%' THEN 'Consultant'
                        WHEN LOWER(title) LIKE '%specialist%' THEN 'Specialist'
                        WHEN LOWER(title) LIKE '%administrator%' THEN 'Administrator'
                        WHEN LOWER(title) LIKE '%coordinator%' THEN 'Coordinator'
                        WHEN LOWER(title) LIKE '%designer%' THEN 'Designer'
                        ELSE NULL
                    END as keyword
                FROM scraper.jobs_jobpost
            ) keywords
            WHERE keyword IS NOT NULL
            GROUP BY keyword
            ORDER BY mention_count DESC
        """
        
        role_keywords = await db_manager.execute_query(role_keywords_query)
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "technology_keywords": [dict(row) for row in tech_keywords],
            "role_keywords": [dict(row) for row in role_keywords],
            "insights": {
                "total_tech_mentions": sum(row["mention_count"] for row in tech_keywords),
                "most_demanded_tech": tech_keywords[0]["keyword"] if tech_keywords else None,
                "most_common_role": role_keywords[0]["keyword"] if role_keywords else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting keyword trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get keyword trends")

@router.get("/remote-work-analysis")
async def get_remote_work_analysis():
    """
    Analyze remote work opportunities based on title keywords
    Shows remote vs onsite job distribution
    """
    try:
        # Remote work indicators
        remote_analysis_query = """
            SELECT 
                CASE 
                    WHEN LOWER(title) LIKE '%remote%' THEN 'Remote'
                    WHEN LOWER(title) LIKE '%onsite%' THEN 'Onsite'
                    WHEN LOWER(title) LIKE '%hybrid%' THEN 'Hybrid'
                    WHEN LOWER(title) LIKE '%work from home%' OR LOWER(title) LIKE '%wfh%' THEN 'Remote'
                    ELSE 'Unspecified'
                END as work_type,
                COUNT(*) as job_count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM scraper.jobs_jobpost), 2) as percentage,
                COUNT(DISTINCT company) as companies_offering
            FROM scraper.jobs_jobpost
            GROUP BY work_type
            ORDER BY job_count DESC
        """
        
        remote_analysis = await db_manager.execute_query(remote_analysis_query)
        
        # Companies offering remote work
        remote_companies_query = """
            SELECT company,
                   COUNT(*) as total_jobs,
                   COUNT(CASE WHEN LOWER(title) LIKE '%remote%' OR LOWER(title) LIKE '%work from home%' THEN 1 END) as remote_jobs,
                   ROUND(COUNT(CASE WHEN LOWER(title) LIKE '%remote%' OR LOWER(title) LIKE '%work from home%' THEN 1 END) * 100.0 / COUNT(*), 2) as remote_percentage
            FROM scraper.jobs_jobpost
            GROUP BY company
            HAVING COUNT(CASE WHEN LOWER(title) LIKE '%remote%' OR LOWER(title) LIKE '%work from home%' THEN 1 END) > 0
            ORDER BY remote_jobs DESC
            LIMIT 15
        """
        
        remote_companies = await db_manager.execute_query(remote_companies_query)
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "work_type_distribution": [dict(row) for row in remote_analysis],
            "top_remote_companies": [dict(row) for row in remote_companies],
            "insights": {
                "remote_job_percentage": next((row["percentage"] for row in remote_analysis if row["work_type"] == "Remote"), 0),
                "companies_offering_remote": len(remote_companies),
                "analysis_note": "Based on keywords in job titles - actual remote policies may vary"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting remote work analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get remote work analysis")

@router.get("/market-competition")
async def get_market_competition():
    """
    Analyze market competition and job scarcity
    Shows which roles/companies have high competition
    """
    try:
        # Job concentration by title
        title_competition_query = """
            WITH title_stats AS (
                SELECT title,
                       COUNT(*) as job_count,
                       COUNT(DISTINCT company) as company_count,
                       COUNT(DISTINCT source) as source_count
                FROM scraper.jobs_jobpost
                GROUP BY title
                HAVING COUNT(*) > 1
            )
            SELECT title,
                   job_count,
                   company_count,
                   source_count,
                   ROUND(job_count::float / company_count, 2) as avg_jobs_per_company,
                   CASE 
                       WHEN job_count >= 10 THEN 'High Demand'
                       WHEN job_count >= 5 THEN 'Medium Demand'
                       ELSE 'Low Demand'
                   END as demand_level
            FROM title_stats
            ORDER BY job_count DESC
            LIMIT 25
        """
        
        title_competition = await db_manager.execute_query(title_competition_query)
        
        # Source coverage analysis
        source_coverage_query = """
            SELECT 
                COUNT(DISTINCT source) as total_sources,
                AVG(source_count) as avg_sources_per_job,
                MAX(source_count) as max_sources_per_job
            FROM (
                SELECT title, COUNT(DISTINCT source) as source_count
                FROM scraper.jobs_jobpost
                GROUP BY title
            ) title_sources
        """
        
        source_coverage = await db_manager.execute_query(source_coverage_query)
        
        # Market saturation by domain
        domain_saturation_query = """
            SELECT 
                CASE 
                    WHEN LOWER(title) LIKE '%software%' OR LOWER(title) LIKE '%developer%' THEN 'Software Development'
                    WHEN LOWER(title) LIKE '%data%' OR LOWER(title) LIKE '%analyst%' THEN 'Data & Analytics'
                    WHEN LOWER(title) LIKE '%devops%' OR LOWER(title) LIKE '%cloud%' THEN 'DevOps & Cloud'
                    WHEN LOWER(title) LIKE '%qa%' OR LOWER(title) LIKE '%test%' THEN 'QA & Testing'
                    WHEN LOWER(title) LIKE '%manager%' OR LOWER(title) LIKE '%lead%' THEN 'Management & Leadership'
                    WHEN LOWER(title) LIKE '%design%' OR LOWER(title) LIKE '%ui%' OR LOWER(title) LIKE '%ux%' THEN 'Design & UX'
                    ELSE 'Other'
                END as domain,
                COUNT(*) as total_jobs,
                COUNT(DISTINCT title) as unique_titles,
                COUNT(DISTINCT company) as companies_hiring,
                ROUND(COUNT(*)::float / COUNT(DISTINCT title), 2) as avg_jobs_per_title
            FROM scraper.jobs_jobpost
            GROUP BY domain
            ORDER BY total_jobs DESC
        """
        
        domain_saturation = await db_manager.execute_query(domain_saturation_query)
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "high_competition_titles": [dict(row) for row in title_competition],
            "source_coverage": dict(source_coverage[0]) if source_coverage else {},
            "domain_saturation": [dict(row) for row in domain_saturation],
            "insights": {
                "most_competitive_title": title_competition[0]["title"] if title_competition else None,
                "average_jobs_per_title": round(sum(row["job_count"] for row in title_competition) / len(title_competition), 2) if title_competition else 0,
                "competition_note": "High competition indicates many similar roles available"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting market competition: {e}")
        raise HTTPException(status_code=500, detail="Failed to get market competition analysis")

@router.get("/snapshot-summary")
async def get_snapshot_summary():
    """
    Get comprehensive market snapshot summary
    Quick overview of all key metrics
    """
    try:
        # Get all key metrics in one summary
        summary_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company) as total_companies,
                COUNT(DISTINCT source) as total_sources,
                COUNT(DISTINCT title) as unique_titles,
                MIN(created_at) as data_from,
                MAX(created_at) as data_to,
                COUNT(CASE WHEN LOWER(title) LIKE '%remote%' THEN 1 END) as remote_jobs,
                COUNT(CASE WHEN LOWER(title) LIKE '%senior%' THEN 1 END) as senior_jobs,
                COUNT(CASE WHEN LOWER(title) LIKE '%junior%' THEN 1 END) as junior_jobs
            FROM scraper.jobs_jobpost
        """
        
        summary = await db_manager.execute_query(summary_query)
        
        # Top performers
        top_performers_query = """
            SELECT 
                (SELECT company FROM scraper.jobs_jobpost GROUP BY company ORDER BY COUNT(*) DESC LIMIT 1) as top_company,
                (SELECT source FROM scraper.jobs_jobpost GROUP BY source ORDER BY COUNT(*) DESC LIMIT 1) as top_source,
                (SELECT title FROM scraper.jobs_jobpost GROUP BY title ORDER BY COUNT(*) DESC LIMIT 1) as most_common_title
        """
        
        top_performers = await db_manager.execute_query(top_performers_query)
        
        if summary and top_performers:
            summary_data = dict(summary[0])
            top_data = dict(top_performers[0])
            
            # Calculate percentages
            total_jobs = summary_data["total_jobs"]
            summary_data["remote_percentage"] = round((summary_data["remote_jobs"] / total_jobs) * 100, 2) if total_jobs > 0 else 0
            summary_data["senior_percentage"] = round((summary_data["senior_jobs"] / total_jobs) * 100, 2) if total_jobs > 0 else 0
            summary_data["junior_percentage"] = round((summary_data["junior_jobs"] / total_jobs) * 100, 2) if total_jobs > 0 else 0
            
            return {
                "success": True,
                "snapshot_time": datetime.now().isoformat(),
                "market_summary": summary_data,
                "top_performers": top_data,
                "data_freshness": {
                    "from": summary_data["data_from"].isoformat() if summary_data["data_from"] else None,
                    "to": summary_data["data_to"].isoformat() if summary_data["data_to"] else None,
                    "refresh_cycle": "hourly",
                    "note": "Current snapshot - data is truncated and reloaded hourly"
                }
            }
        
        return {
            "success": True,
            "snapshot_time": datetime.now().isoformat(),
            "market_summary": {},
            "message": "No data available"
        }
        
    except Exception as e:
        logger.error(f"Error getting snapshot summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get snapshot summary")

@router.post("/event")
async def track_analytics_event(request: Dict[str, Any]):
    """
    Track user analytics events (apply attempts, job views, etc.)
    Used by iOS app to track user interactions
    """
    try:
        device_id = request.get("device_id")
        action_type = request.get("action_type")
        action_data = request.get("action_data", {})
        
        if not device_id or not action_type:
            raise HTTPException(status_code=400, detail="device_id and action_type are required")
        
        # Track the event using privacy analytics service
        from app.services.privacy_analytics_service import privacy_analytics_service
        
        # Map action types to analytics actions
        analytics_action = {
            "job_apply_from_notification": "job_apply_attempt",
            "job_view": "job_view",
            "notification_open": "notification_opened",
            "search_performed": "job_search",
            "job_share": "job_shared"
        }.get(action_type, action_type)
        
        # Extract relevant metadata
        metadata = {
            "action_type": action_type,
            "timestamp": datetime.now().isoformat(),
            **action_data
        }
        
        # Track with consent check
        await privacy_analytics_service.track_action_with_consent(
            device_id,
            analytics_action,
            metadata
        )
        
        logger.info(f"Tracked analytics event: {action_type} for device {device_id[:8]}...")
        
        return {
            "success": True,
            "message": "Event tracked successfully",
            "action_type": action_type,
            "analytics_action": analytics_action
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking analytics event: {e}")
        raise HTTPException(status_code=500, detail="Failed to track analytics event")