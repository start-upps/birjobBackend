"""
Device-based AI chatbot endpoints
Works with minimal schema (device_users, notification_hashes, user_analytics)
No email dependencies - everything is device-token based
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
import json

from app.core.database import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

def validate_device_token(device_token: str) -> str:
    """Simple device token validation"""
    if not device_token or len(device_token) < 16:
        raise HTTPException(status_code=400, detail="Invalid device token")
    return device_token

@router.post("/chat/{device_token}")
async def chat_with_ai(
    device_token: str,
    chat_request: Dict[str, Any]
):
    """Chat with AI about jobs and career advice"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info and user context
        device_query = """
            SELECT id, keywords FROM iosapp.device_users
            WHERE device_token = $1 AND notifications_enabled = true
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found or notifications disabled")
        
        device_id = device_result[0]['id']
        keywords_raw = device_result[0]['keywords']
        
        logger.info(f"Raw keywords from DB: type={type(keywords_raw)}, value={repr(keywords_raw)}")
        
        # Handle JSONB field properly - fix the JSON parsing issue
        if keywords_raw is None:
            keywords = []
        elif isinstance(keywords_raw, list):
            keywords = keywords_raw  # Already a list
        elif isinstance(keywords_raw, str):
            # Handle JSON string from database
            try:
                parsed = json.loads(keywords_raw)
                keywords = parsed if isinstance(parsed, list) else [str(parsed)]
            except (json.JSONDecodeError, TypeError):
                # Fallback: treat as single keyword
                keywords = [keywords_raw] if keywords_raw.strip() else []
        else:
            # Handle other types (e.g., dict, number)
            keywords = []
            
        logger.info(f"Processed keywords: type={type(keywords)}, value={keywords}")
        
        # Extract message from request
        user_message = chat_request.get("message", "").strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="message is required")
        
        # Get recent job activity for context
        recent_notifications_query = """
            SELECT 
                job_title,
                job_company,
                job_source,
                matched_keywords,
                sent_at
            FROM iosapp.notification_hashes
            WHERE device_id = $1
            ORDER BY sent_at DESC
            LIMIT 10
        """
        recent_notifications = await db_manager.execute_query(recent_notifications_query, device_id)
        
        # Build AI context
        logger.info(f"Debug: keywords type={type(keywords)}, value={keywords}")
        context = {
            "user_keywords": keywords,
            "recent_jobs": [
                {
                    "title": notif['job_title'],
                    "company": notif['job_company'],
                    "source": notif['job_source'],
                    "matched_keywords": notif['matched_keywords']
                }
                for notif in recent_notifications[:5]  # Last 5 jobs
            ]
        }
        
        # Simple AI response logic (you can replace with actual AI service)
        ai_response = await generate_ai_response(user_message, context)
        
        # Log chat interaction
        chat_log_query = """
            INSERT INTO iosapp.user_analytics (device_id, action, metadata)
            VALUES ($1, 'ai_chat', $2)
        """
        metadata = {
            "user_message": user_message[:200],  # Truncate for storage
            "response_length": len(ai_response),
            "context_keywords": keywords[:5],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db_manager.execute_command(
            chat_log_query,
            device_id,
            json.dumps(metadata)
        )
        
        return {
            "success": True,
            "data": {
                "response": ai_response,
                "context_used": {
                    "keywords": keywords,  # This should be a list, not a string
                    "raw_keywords_type": str(type(keywords_raw)),
                    "raw_keywords_value": str(keywords_raw),
                    "processed_keywords_type": str(type(keywords)),
                    "processed_keywords_value": str(keywords),
                    "recent_jobs_count": len(recent_notifications)
                },
                "conversation_id": str(device_id),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request")

@router.post("/analyze-job/{device_token}")
async def analyze_job_with_ai(
    device_token: str,
    job_request: Dict[str, Any]
):
    """Analyze a specific job with AI"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id, keywords FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        keywords = device_result[0]['keywords'] or []
        
        # Ensure keywords is properly formatted as list (parse JSON if needed)
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords) if keywords.startswith('[') else [keywords]
            except json.JSONDecodeError:
                keywords = [keywords] if keywords else []
        elif keywords is None:
            keywords = []
        
        # Extract job info
        job_id = job_request.get("job_id")
        if not job_id:
            raise HTTPException(status_code=400, detail="job_id is required")
        
        # Get job details from scraper database
        job_query = """
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at
            FROM scraper.jobs_jobpost
            WHERE id = $1
        """
        job_result = await db_manager.execute_query(job_query, job_id)
        
        if not job_result:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_result[0]
        
        # Generate AI analysis
        analysis = await generate_job_analysis(job, keywords)
        
        # Log job analysis
        analysis_log_query = """
            INSERT INTO iosapp.user_analytics (device_id, action, metadata)
            VALUES ($1, 'job_analysis', $2)
        """
        metadata = {
            "job_id": job_id,
            "job_title": job['title'][:100],
            "job_company": job['company'][:50],
            "analysis_type": "ai_analysis",
            "user_keywords": keywords[:5],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db_manager.execute_command(
            analysis_log_query,
            device_id,
            json.dumps(metadata)
        )
        
        return {
            "success": True,
            "data": {
                "job": {
                    "id": job['id'],
                    "title": job['title'],
                    "company": job['company'],
                    "source": job['source']
                },
                "analysis": analysis,
                "match_score": calculate_match_score(job, keywords),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in job analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze job")

@router.get("/recommendations/{device_token}")
async def get_ai_recommendations(
    device_token: str,
    limit: int = 5
):
    """Get AI-powered job recommendations based on device activity"""
    try:
        # Validate device token
        device_token = validate_device_token(device_token)
        
        # Get device info
        device_query = """
            SELECT id, keywords FROM iosapp.device_users
            WHERE device_token = $1
        """
        device_result = await db_manager.execute_query(device_query, device_token)
        
        if not device_result:
            raise HTTPException(status_code=404, detail="Device not found")
        
        device_id = device_result[0]['id']
        keywords = device_result[0]['keywords'] or []
        
        # Ensure keywords is properly formatted as list (parse JSON if needed)
        if isinstance(keywords, str):
            try:
                keywords = json.loads(keywords) if keywords.startswith('[') else [keywords]
            except json.JSONDecodeError:
                keywords = [keywords] if keywords else []
        elif keywords is None:
            keywords = []
        
        if not keywords:
            raise HTTPException(status_code=400, detail="No keywords set for recommendations")
        
        # Get user's notification history for learning
        history_query = """
            SELECT 
                job_title,
                job_company,
                job_source,
                matched_keywords
            FROM iosapp.notification_hashes
            WHERE device_id = $1
            ORDER BY sent_at DESC
            LIMIT 20
        """
        history_result = await db_manager.execute_query(history_query, device_id)
        
        # Find recommended jobs based on keywords and history
        recommendations_query = """
            SELECT 
                id,
                title,
                company,
                apply_link,
                source,
                created_at
            FROM scraper.jobs_jobpost
            WHERE created_at >= NOW() - INTERVAL '7 days'
            AND (
                LOWER(title) LIKE ANY($1)
                OR LOWER(company) LIKE ANY($1)
            )
            ORDER BY created_at DESC
            LIMIT $2
        """
        
        # Create LIKE patterns from keywords
        # Ensure keywords is a list
        if isinstance(keywords, str):
            keywords = json.loads(keywords) if keywords.startswith('[') else [keywords]
        like_patterns = [f"%{keyword.lower()}%" for keyword in keywords]
        
        recommendations_result = await db_manager.execute_query(
            recommendations_query, 
            like_patterns, 
            limit
        )
        
        # Generate AI explanations for recommendations
        recommendations = []
        for job in recommendations_result:
            explanation = generate_recommendation_explanation(job, keywords, history_result)
            match_score = calculate_match_score(job, keywords)
            
            recommendations.append({
                "job": {
                    "id": job['id'],
                    "title": job['title'],
                    "company": job['company'],
                    "apply_link": job['apply_link'],
                    "source": job['source'],
                    "posted_at": job['created_at'].isoformat() if job['created_at'] else None
                },
                "match_score": match_score,
                "explanation": explanation,
                "matched_keywords": find_matched_keywords(job, keywords)
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Log recommendation request
        rec_log_query = """
            INSERT INTO iosapp.user_analytics (device_id, action, metadata)
            VALUES ($1, 'ai_recommendations', $2)
        """
        metadata = {
            "recommendations_count": len(recommendations),
            "user_keywords": keywords,
            "history_jobs": len(history_result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db_manager.execute_command(
            rec_log_query,
            device_id,
            json.dumps(metadata)
        )
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "total_found": len(recommendations),
                "based_on_keywords": keywords,
                "recommendation_criteria": {
                    "keywords": keywords,
                    "history_jobs": len(history_result),
                    "time_range": "last_7_days"
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

# Helper functions for AI functionality

async def generate_ai_response(user_message: str, context: Dict[str, Any]) -> str:
    """Generate AI response based on user message and context"""
    
    # Simple keyword-based responses (replace with actual AI service)
    message_lower = user_message.lower()
    keywords_raw = context.get("user_keywords", [])
    recent_jobs = context.get("recent_jobs", [])
    
    # Force keywords to be a proper list
    if isinstance(keywords_raw, str):
        try:
            # Try to parse as JSON first
            keywords = json.loads(keywords_raw)
            if not isinstance(keywords, list):
                keywords = [str(keywords)]
        except:
            # Fallback: split by comma or space
            keywords = [k.strip() for k in keywords_raw.replace(",", " ").split() if k.strip()]
    elif isinstance(keywords_raw, list):
        keywords = keywords_raw
    else:
        keywords = []
    
    logger.info(f"AI Debug: keywords_raw type={type(keywords_raw)}, value={repr(keywords_raw)}")
    logger.info(f"AI Debug: final keywords type={type(keywords)}, value={keywords}")
    
    if "salary" in message_lower or "pay" in message_lower:
        keywords_str = ", ".join(keywords)
        return f"Based on your keywords {keywords_str}, typical salary ranges vary by location and experience. iOS developers typically earn $80k-$200k+ depending on skills and location. Would you like me to analyze specific jobs for salary information?"
    
    elif "skills" in message_lower or "learn" in message_lower:
        keywords_str = ", ".join(keywords)
        return f"Given your interest in {keywords_str}, I recommend focusing on: SwiftUI, Combine, Core Data, networking, and testing. Consider building portfolio apps showcasing these skills."
    
    elif "interview" in message_lower:
        keywords_str = ", ".join(keywords)
        return f"For iOS interviews, prepare for: algorithm questions, iOS-specific concepts (memory management, lifecycle), system design, and coding challenges. Practice with your {keywords_str} focus areas."
    
    elif "career" in message_lower or "advice" in message_lower:
        keywords_str = ", ".join(keywords)
        if recent_jobs:
            companies = [job["company"] for job in recent_jobs[:3]]
            return f"You've had matches with {', '.join(companies)}. Consider researching these companies' tech stacks and contributing to open source projects that align with your {keywords_str} interests."
        else:
            return f"Focus on building a strong portfolio with {keywords_str}. Contribute to open source, build personal projects, and network with iOS developers on platforms like Twitter and GitHub."
    
    elif isinstance(keywords, list) and any(keyword.lower() in message_lower for keyword in keywords):
        # Debug what keywords looks like here
        logger.info(f"AI Response - keywords type: {type(keywords)}, value: {repr(keywords)}")
        matched = [k for k in keywords if k.lower() in message_lower]
        logger.info(f"AI Response - matched: {matched}")
        matched_str = ", ".join(matched)
        return f"Great question about {matched_str}! Based on your job matches, this is clearly an important skill area. Would you like specific recommendations for {matched[0]} positions or learning resources?"
    
    else:
        keywords_str = ", ".join(keywords)
        return f"I'm here to help with your job search in {keywords_str}! I can provide career advice, analyze specific jobs, discuss salaries, interview tips, or recommend learning paths. What would you like to know?"

async def generate_job_analysis(job: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
    """Generate AI analysis of a specific job"""
    
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    
    # Calculate keyword matches
    matched_keywords = find_matched_keywords(job, keywords)
    match_score = calculate_match_score(job, keywords)
    
    # Generate analysis components
    analysis = {
        "match_assessment": f"This position matches {len(matched_keywords)} of your {len(keywords)} keywords ({match_score}% match)",
        "matched_keywords": matched_keywords,
        "skill_relevance": "High" if match_score > 70 else "Medium" if match_score > 40 else "Low",
        "recommendation": "Highly recommended" if match_score > 70 else "Consider applying" if match_score > 40 else "May require additional skills",
        "key_highlights": [],
        "potential_concerns": []
    }
    
    # Add specific insights based on job content
    if "senior" in title:
        analysis["key_highlights"].append("Senior-level position with likely higher compensation")
        analysis["potential_concerns"].append("May require 5+ years of experience")
    
    if "remote" in title or "remote" in company:
        analysis["key_highlights"].append("Remote work opportunity")
    
    if any(keyword in title for keyword in ["ios", "swift", "mobile"]):
        analysis["key_highlights"].append("Direct match for mobile development role")
    
    if "startup" in company or len(company.split()) <= 2:
        analysis["key_highlights"].append("Startup environment - potential for growth and equity")
        analysis["potential_concerns"].append("Startup risk and potentially lower initial salary")
    
    return analysis

def calculate_match_score(job: Dict[str, Any], keywords: List[str]) -> int:
    """Calculate how well a job matches user keywords (0-100)"""
    if not keywords:
        return 0
    
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    
    matched_count = 0
    for keyword in keywords:
        if keyword.lower() in title or keyword.lower() in company:
            matched_count += 1
    
    return int((matched_count / len(keywords)) * 100)

def find_matched_keywords(job: Dict[str, Any], keywords: List[str]) -> List[str]:
    """Find which keywords match this job"""
    title = job.get("title", "").lower()
    company = job.get("company", "").lower()
    
    matched = []
    for keyword in keywords:
        if keyword.lower() in title or keyword.lower() in company:
            matched.append(keyword)
    
    return matched

def generate_recommendation_explanation(job: Dict[str, Any], keywords: List[str], history: List[Dict]) -> str:
    """Generate explanation for why this job is recommended"""
    matched_keywords = find_matched_keywords(job, keywords)
    match_score = calculate_match_score(job, keywords)
    
    if match_score > 80:
        return f"Excellent match! This role closely aligns with your {matched_keywords} expertise and similar to your recent job interests."
    elif match_score > 60:
        return f"Good fit based on your {matched_keywords} background. The role at {job['company']} could be a great next step."
    elif match_score > 40:
        return f"Potential opportunity matching {matched_keywords}. Consider if the company culture and role responsibilities align with your goals."
    else:
        return f"Emerging opportunity that could expand your skills beyond {keywords}. Worth exploring if you're interested in growth."