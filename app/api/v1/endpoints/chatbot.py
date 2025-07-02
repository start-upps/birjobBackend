from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
import logging
import json

from app.core.database import db_manager
from app.services.gemini_chatbot import gemini_service
from app.schemas.chatbot import (
    ChatRequest, ChatResponse,
    JobRecommendationsRequest, JobRecommendationsResponse,
    JobAnalysisRequest, JobAnalysisResponse,
    ChatbotStatsResponse, UserContext
)

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_user_context(device_id: str) -> UserContext:
    """Get user context including keywords and recent job activity"""
    try:
        # Get user info via device_tokens relationship
        user_query = """
            SELECT u.id, u.keywords FROM iosapp.users u
            JOIN iosapp.device_tokens dt ON u.id = dt.user_id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            return UserContext()
        
        user = user_result[0]
        user_id = user["id"]
        
        # Parse keywords
        keywords_data = user["keywords"]
        if isinstance(keywords_data, str):
            keywords = json.loads(keywords_data) if keywords_data else []
        else:
            keywords = keywords_data or []
        
        # Get recent job views
        recent_jobs_query = """
            SELECT job_id, job_title, job_company, job_source, viewed_at
            FROM iosapp.job_views
            WHERE user_id = $1
            ORDER BY viewed_at DESC
            LIMIT 5
        """
        recent_jobs_result = await db_manager.execute_query(recent_jobs_query, user_id)
        
        recent_jobs = []
        for job in recent_jobs_result:
            recent_jobs.append({
                "job_id": job["job_id"],
                "title": job["job_title"],
                "company": job["job_company"],
                "source": job["job_source"]
            })
        
        return UserContext(
            keywords=keywords,
            recent_jobs=recent_jobs
        )
        
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return UserContext()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    """Have a conversation with the Gemini-powered job search assistant"""
    try:
        # Get user context if requested
        user_context = None
        if request.include_user_context:
            context = await get_user_context(request.device_id)
            user_context = {
                "keywords": context.keywords,
                "recent_jobs": context.recent_jobs
            }
        
        # Convert conversation history to dict format
        conversation_history = []
        for msg in request.conversation_history:
            conversation_history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Generate response
        result = await gemini_service.chat(
            message=request.message,
            conversation_history=conversation_history,
            user_context=user_context
        )
        
        if result["success"]:
            # Record analytics event for chatbot usage
            try:
                analytics_query = """
                    INSERT INTO iosapp.user_analytics 
                    (user_id, action_type, action_data, device_info)
                    SELECT u.id, 'chatbot_message', $2, '{}'::jsonb
                    FROM iosapp.users u
                    JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                    WHERE dt.device_id = $1 AND dt.is_active = true
                """
                await db_manager.execute_query(
                    analytics_query,
                    request.device_id,
                    json.dumps({
                        "message_length": len(request.message),
                        "has_context": request.include_user_context,
                        "conversation_length": len(request.conversation_history)
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to record chatbot analytics: {e}")
            
            return ChatResponse(
                response=result["response"],
                timestamp=result["timestamp"],
                model=result["model"]
            )
        else:
            return ChatResponse(
                success=False,
                response=result["response"],
                timestamp=result.get("timestamp", ""),
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"Error in chatbot conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )

@router.post("/recommendations", response_model=JobRecommendationsResponse)
async def get_job_recommendations(request: JobRecommendationsRequest):
    """Get personalized job search recommendations based on user's profile"""
    try:
        # Get user context
        context = await get_user_context(request.device_id)
        
        # Use provided keywords or fall back to user's profile keywords
        keywords = request.keywords if request.keywords else context.keywords
        
        if not keywords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No keywords provided and user has no job preferences set"
            )
        
        # Generate recommendations
        result = await gemini_service.get_job_recommendations(
            user_keywords=keywords,
            user_location=request.location
        )
        
        if result["success"]:
            # Record analytics
            try:
                analytics_query = """
                    INSERT INTO iosapp.user_analytics 
                    (user_id, action_type, action_data, device_info)
                    SELECT u.id, 'job_recommendations', $2, '{}'::jsonb
                    FROM iosapp.users u
                    JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                    WHERE dt.device_id = $1 AND dt.is_active = true
                """
                await db_manager.execute_query(
                    analytics_query,
                    request.device_id,
                    json.dumps({
                        "keywords": keywords,
                        "location": request.location
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to record recommendations analytics: {e}")
            
            return JobRecommendationsResponse(
                recommendations=result["recommendations"],
                keywords=result["keywords"],
                location=result.get("location"),
                timestamp=result["timestamp"]
            )
        else:
            return JobRecommendationsResponse(
                success=False,
                recommendations="",
                keywords=keywords,
                location=request.location,
                timestamp="",
                error=result.get("error")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating job recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate job recommendations"
        )

@router.post("/analyze-job", response_model=JobAnalysisResponse)
async def analyze_job(request: JobAnalysisRequest):
    """Analyze a job posting and provide insights and advice"""
    try:
        # If job_id is provided, try to get job details from database
        job_description = request.job_description
        if request.job_id and not job_description:
            try:
                job_query = """
                    SELECT title, company, apply_link
                    FROM scraper.jobs_jobpost
                    WHERE id = $1
                """
                job_result = await db_manager.execute_query(job_query, request.job_id)
                if job_result:
                    job = job_result[0]
                    # Use database info if provided data doesn't match
                    if not request.job_title or request.job_title != job["title"]:
                        request.job_title = job["title"]
                    if not request.job_company or request.job_company != job["company"]:
                        request.job_company = job["company"]
            except Exception as e:
                logger.warning(f"Could not fetch job details from database: {e}")
        
        # Generate analysis
        result = await gemini_service.analyze_job_description(
            job_title=request.job_title,
            job_company=request.job_company,
            job_description=job_description
        )
        
        if result["success"]:
            # Record analytics
            try:
                analytics_query = """
                    INSERT INTO iosapp.user_analytics 
                    (user_id, action_type, action_data, device_info)
                    SELECT u.id, 'job_analysis', $2, '{}'::jsonb
                    FROM iosapp.users u
                    JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                    WHERE dt.device_id = $1 AND dt.is_active = true
                """
                await db_manager.execute_query(
                    analytics_query,
                    request.device_id,
                    json.dumps({
                        "job_id": request.job_id,
                        "job_title": request.job_title,
                        "company": request.job_company
                    })
                )
            except Exception as e:
                logger.warning(f"Failed to record job analysis analytics: {e}")
            
            return JobAnalysisResponse(
                analysis=result["analysis"],
                job_title=result["job_title"],
                company=result["company"],
                timestamp=result["timestamp"]
            )
        else:
            return JobAnalysisResponse(
                success=False,
                analysis="",
                job_title=request.job_title,
                company=request.job_company,
                timestamp="",
                error=result.get("error")
            )
            
    except Exception as e:
        logger.error(f"Error analyzing job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze job posting"
        )

@router.get("/stats", response_model=ChatbotStatsResponse)
async def get_chatbot_stats():
    """Get chatbot usage statistics"""
    try:
        # Get chatbot usage stats from analytics
        stats_query = """
            SELECT 
                COUNT(*) as total_interactions,
                COUNT(DISTINCT user_id) as unique_users,
                action_type,
                COUNT(*) as action_count
            FROM iosapp.user_analytics
            WHERE action_type IN ('chatbot_message', 'job_recommendations', 'job_analysis')
            AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            GROUP BY action_type
        """
        
        stats_result = await db_manager.execute_query(stats_query)
        
        total_interactions = 0
        unique_users = 0
        interactions_by_type = {}
        
        for row in stats_result:
            total_interactions += row["action_count"]
            if row["unique_users"] > unique_users:
                unique_users = row["unique_users"]
            interactions_by_type[row["action_type"]] = row["action_count"]
        
        return ChatbotStatsResponse(
            data={
                "last_24_hours": {
                    "total_interactions": total_interactions,
                    "unique_users": unique_users,
                    "interactions_by_type": interactions_by_type
                },
                "chatbot_status": "operational" if gemini_service.model else "unavailable",
                "timestamp": f"{__import__('datetime').datetime.now().isoformat()}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting chatbot stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get chatbot statistics"
        )