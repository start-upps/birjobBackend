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
from app.services.privacy_analytics_service import privacy_analytics_service

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
        
        # Log chat interaction (with consent check)
        metadata = {
            "user_message": user_message[:200],  # Truncate for storage
            "response_length": len(ai_response),
            "context_keywords": keywords[:5],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await privacy_analytics_service.track_action_with_consent(
            device_id, 
            'ai_chat', 
            metadata
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
        
        # Log job analysis (with consent check)
        metadata = {
            "job_id": job_id,
            "job_title": job['title'][:100],
            "job_company": job['company'][:50],
            "analysis_type": "ai_analysis",
            "user_keywords": keywords[:5],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await privacy_analytics_service.track_action_with_consent(
            device_id, 
            'job_analysis', 
            metadata
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
        
        # Log recommendation request (with consent check)
        metadata = {
            "recommendations_count": len(recommendations),
            "user_keywords": keywords,
            "history_jobs": len(history_result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await privacy_analytics_service.track_action_with_consent(
            device_id, 
            'ai_recommendations', 
            metadata
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
    """Generate intelligent AI response using real job market data and analytics"""
    
    message_lower = user_message.lower()
    keywords_raw = context.get("user_keywords", [])
    recent_jobs = context.get("recent_jobs", [])
    
    # Process keywords properly
    if isinstance(keywords_raw, str):
        try:
            keywords = json.loads(keywords_raw)
            if not isinstance(keywords, list):
                keywords = [str(keywords)]
        except:
            keywords = [k.strip() for k in keywords_raw.replace(",", " ").split() if k.strip()]
    elif isinstance(keywords_raw, list):
        keywords = keywords_raw
    else:
        keywords = []
    
    logger.info(f"AI Processing: keywords={keywords}, message='{user_message[:50]}...'")
    
    try:
        # Get real-time market data for intelligent responses
        market_data = await get_market_intelligence_for_ai(keywords)
        
        # Enhanced intelligent routing with broader pattern recognition
        
        # Salary and compensation queries
        if any(word in message_lower for word in ["salary", "pay", "money", "compensation", "earn", "wage", "income", "cost", "much", "$", "dollar"]):
            return await generate_salary_insights(keywords, market_data, user_message)
        
        # Skill development and learning queries
        elif any(word in message_lower for word in ["skills", "learn", "study", "improve", "course", "training", "education", "practice", "master", "tutorial", "guide", "how to", "what should", "develop"]):
            return await generate_skill_recommendations(keywords, market_data, user_message)
        
        # Interview preparation queries
        elif any(word in message_lower for word in ["interview", "prepare", "questions", "tips", "practice", "coding challenge", "technical", "behavioral", "assessment"]):
            return await generate_interview_guidance(keywords, market_data, user_message)
        
        # Career strategy and advice queries (most common)
        elif any(word in message_lower for word in ["career", "advice", "path", "grow", "future", "next step", "should i", "what do", "help me", "guidance", "strategy", "plan", "direction", "goal", "progress", "development", "roadmap"]):
            return await generate_career_strategy(keywords, market_data, recent_jobs, user_message)
        
        # Company and employer queries
        elif any(word in message_lower for word in ["companies", "company", "employers", "where", "who", "hiring", "jobs at", "work at", "employer", "organization", "firm"]):
            return await generate_company_insights(keywords, market_data, user_message)
        
        # Remote work queries
        elif any(word in message_lower for word in ["remote", "work from home", "location", "hybrid", "wfh", "telecommute", "distributed", "virtual", "home office"]):
            return await generate_remote_work_insights(keywords, market_data, user_message)
        
        # Market trends and technology queries
        elif any(word in message_lower for word in ["trends", "market", "demand", "popular", "hot", "trending", "growth", "future", "technology", "tech", "industry", "outlook"]):
            return await generate_market_trends(keywords, market_data, user_message)
        
        # Keyword-specific queries (user mentions their skills)
        elif keywords and any(keyword.lower() in message_lower for keyword in keywords):
            matched = [k for k in keywords if k.lower() in message_lower]
            return await generate_keyword_specific_advice(matched, market_data, user_message)
        
        # General/greeting queries - provide helpful guidance
        elif any(word in message_lower for word in ["hello", "hi", "hey", "help", "what can", "what do you", "how can", "assist", "support"]):
            return await generate_general_assistance(keywords, market_data, user_message)
        
        # Default: If no specific intent detected, ask for clarification or provide varied help
        else:
            logger.info(f"No specific intent detected for message: '{user_message}' - providing clarification")
            return await generate_clarification_response(keywords, market_data, user_message)
            
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        # Fallback to enhanced basic response
        return await generate_fallback_response(keywords, recent_jobs, user_message)

async def get_market_intelligence_for_ai(keywords: List[str]) -> Dict[str, Any]:
    """Get real-time market data for AI responses"""
    try:
        # Market overview
        market_query = """
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(DISTINCT company) as total_companies,
                COUNT(DISTINCT source) as total_sources
            FROM scraper.jobs_jobpost
        """
        market_result = await db_manager.execute_query(market_query)
        
        # Top companies
        companies_query = """
            SELECT company, COUNT(*) as job_count
            FROM scraper.jobs_jobpost
            GROUP BY company
            ORDER BY job_count DESC
            LIMIT 10
        """
        companies_result = await db_manager.execute_query(companies_query)
        
        # Keyword-specific jobs if keywords provided
        keyword_jobs = []
        if keywords:
            keyword_patterns = [f"%{keyword.lower()}%" for keyword in keywords]
            keyword_query = """
                SELECT 
                    COUNT(*) as matching_jobs,
                    COUNT(DISTINCT company) as companies_hiring,
                    array_agg(DISTINCT company) FILTER (WHERE company IS NOT NULL) as top_companies
                FROM scraper.jobs_jobpost
                WHERE LOWER(title) LIKE ANY($1)
                LIMIT 5
            """
            keyword_result = await db_manager.execute_query(keyword_query, keyword_patterns)
            keyword_jobs = keyword_result[0] if keyword_result else {}
        
        # Technology trends
        tech_trends_query = """
            SELECT 
                CASE 
                    WHEN LOWER(title) LIKE '%javascript%' OR LOWER(title) LIKE '%js%' THEN 'JavaScript'
                    WHEN LOWER(title) LIKE '%python%' THEN 'Python'
                    WHEN LOWER(title) LIKE '%java%' AND LOWER(title) NOT LIKE '%javascript%' THEN 'Java'
                    WHEN LOWER(title) LIKE '%react%' THEN 'React'
                    WHEN LOWER(title) LIKE '%ios%' OR LOWER(title) LIKE '%swift%' THEN 'iOS/Swift'
                    WHEN LOWER(title) LIKE '%android%' THEN 'Android'
                    WHEN LOWER(title) LIKE '%sql%' THEN 'SQL'
                    WHEN LOWER(title) LIKE '%aws%' THEN 'AWS'
                END as tech,
                COUNT(*) as job_count
            FROM scraper.jobs_jobpost
            WHERE LOWER(title) LIKE '%javascript%' OR LOWER(title) LIKE '%python%' OR 
                  LOWER(title) LIKE '%java%' OR LOWER(title) LIKE '%react%' OR
                  LOWER(title) LIKE '%ios%' OR LOWER(title) LIKE '%swift%' OR
                  LOWER(title) LIKE '%android%' OR LOWER(title) LIKE '%sql%' OR
                  LOWER(title) LIKE '%aws%'
            GROUP BY tech
            ORDER BY job_count DESC
        """
        tech_result = await db_manager.execute_query(tech_trends_query)
        
        return {
            "market_overview": dict(market_result[0]) if market_result else {},
            "top_companies": [dict(row) for row in companies_result],
            "keyword_data": keyword_jobs,
            "tech_trends": [dict(row) for row in tech_result],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting market intelligence: {e}")
        return {}

async def generate_salary_insights(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate intelligent salary insights based on real market data"""
    keyword_str = ", ".join(keywords) if keywords else "your skills"
    
    # Get market context
    total_jobs = market_data.get("market_overview", {}).get("total_jobs", 0)
    keyword_jobs = market_data.get("keyword_data", {}).get("matching_jobs", 0)
    
    response = f"💰 **Salary Insights for {keyword_str}**\n\n"
    
    if keyword_jobs > 0:
        response += f"📊 Currently tracking {keyword_jobs:,} jobs matching your skills from {total_jobs:,} total positions.\n\n"
    
    # Technology-specific salary insights
    if any(tech in keyword_str.lower() for tech in ["ios", "swift", "mobile"]):
        response += "**iOS Developer Salary Ranges:**\n"
        response += "• Junior (0-2 years): $70k-$120k\n"
        response += "• Mid-level (3-5 years): $120k-$180k\n"
        response += "• Senior (5+ years): $180k-$250k+\n"
        response += "• Staff/Principal: $250k-$400k+\n\n"
        response += "💡 *iOS developers are in high demand with salaries above average due to specialized mobile expertise.*"
    
    elif any(tech in keyword_str.lower() for tech in ["python", "backend", "api"]):
        response += "**Backend Developer Salary Ranges:**\n"
        response += "• Junior: $65k-$110k\n"
        response += "• Mid-level: $110k-$160k\n"
        response += "• Senior: $160k-$220k+\n"
        response += "• Staff/Principal: $220k-$350k+\n\n"
        response += "💡 *Python backend roles offer excellent growth potential in AI/ML and enterprise systems.*"
    
    else:
        response += "**General Tech Salary Ranges:**\n"
        response += "• Entry Level: $60k-$100k\n"
        response += "• Mid-level: $100k-$150k\n"
        response += "• Senior: $150k-$200k+\n"
        response += "• Lead/Principal: $200k-$300k+\n\n"
    
    # Add market-specific insights
    top_companies = market_data.get("top_companies", [])[:3]
    if top_companies:
        company_names = [comp["company"] for comp in top_companies]
        response += f"\n🏢 **Top hiring companies**: {', '.join(company_names)} - these typically offer competitive packages.\n"
    
    response += "\n💼 **Salary negotiation tip**: Research the specific company, location, and your unique value proposition for the best results."
    
    return response

async def generate_skill_recommendations(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate intelligent skill recommendations based on market trends"""
    keyword_str = ", ".join(keywords) if keywords else "technology"
    
    response = f"🚀 **Skill Development Strategy for {keyword_str}**\n\n"
    
    # Get trending technologies from market data
    tech_trends = market_data.get("tech_trends", [])
    if tech_trends:
        response += "📈 **Current Market Demand:**\n"
        for i, tech in enumerate(tech_trends[:5], 1):
            response += f"{i}. {tech['tech']}: {tech['job_count']} current openings\n"
        response += "\n"
    
    # Specific skill recommendations based on keywords
    if any(skill in keyword_str.lower() for skill in ["ios", "swift", "mobile"]):
        response += "**iOS Development Learning Path:**\n"
        response += "🎯 **Core Skills (Essential):**\n"
        response += "• Swift language mastery\n"
        response += "• SwiftUI & UIKit\n"
        response += "• Core Data & data persistence\n"
        response += "• Networking & REST APIs\n"
        response += "• Unit testing & debugging\n\n"
        
        response += "⚡ **Advanced Skills (Competitive Edge):**\n"
        response += "• Combine framework\n"
        response += "• App Store optimization\n"
        response += "• CI/CD with Xcode Cloud\n"
        response += "• Performance optimization\n"
        response += "• Accessibility implementation\n\n"
        
        response += "📱 **Portfolio Projects:**\n"
        response += "• Weather app with location services\n"
        response += "• Social media app with Core Data\n"
        response += "• E-commerce app with payments\n"
        response += "• App with widgets and notifications\n"
    
    elif any(skill in keyword_str.lower() for skill in ["python", "backend", "api"]):
        response += "**Backend Development Learning Path:**\n"
        response += "🎯 **Core Skills:**\n"
        response += "• Python/Django or FastAPI\n"
        response += "• Database design (PostgreSQL/MongoDB)\n"
        response += "• RESTful API development\n"
        response += "• Authentication & security\n"
        response += "• Testing & documentation\n\n"
        
        response += "⚡ **Advanced Skills:**\n"
        response += "• Microservices architecture\n"
        response += "• Docker & containerization\n"
        response += "• AWS/Cloud deployment\n"
        response += "• GraphQL & real-time systems\n"
        response += "• Performance monitoring\n"
    
    else:
        response += "**General Tech Skill Strategy:**\n"
        response += "🎯 **Foundation:** Choose one language/framework and master it deeply\n"
        response += "⚡ **Expansion:** Add complementary skills (testing, databases, cloud)\n"
        response += "🚀 **Specialization:** Focus on a domain (mobile, web, AI, DevOps)\n\n"
    
    # Add market-specific learning recommendations
    keyword_jobs = market_data.get("keyword_data", {}).get("matching_jobs", 0)
    if keyword_jobs > 100:
        response += f"\n💡 **Hot Market**: {keyword_jobs} current openings in your area - excellent time to level up!\n"
    elif keyword_jobs > 0:
        response += f"\n📊 **Growing Field**: {keyword_jobs} current opportunities - good potential for growth.\n"
    
    response += "\n🎓 **Learning Resources**: Focus on hands-on projects, contribute to open source, and build a portfolio that showcases real-world applications."
    
    return response

async def generate_interview_guidance(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate intelligent interview preparation guidance"""
    keyword_str = ", ".join(keywords) if keywords else "your skills"
    
    response = f"🎯 **Interview Preparation for {keyword_str}**\n\n"
    
    # Technology-specific interview prep
    if any(tech in keyword_str.lower() for tech in ["ios", "swift", "mobile"]):
        response += "📱 **iOS Interview Focus Areas:**\n\n"
        response += "**🔧 Technical Skills:**\n"
        response += "• Swift language features and best practices\n"
        response += "• iOS app lifecycle and memory management\n"
        response += "• UIKit vs SwiftUI differences and when to use each\n"
        response += "• Core Data, networking, and data persistence\n"
        response += "• Unit testing and debugging techniques\n\n"
        
        response += "**💡 Common iOS Interview Questions:**\n"
        response += "• \"Explain ARC and how it prevents memory leaks\"\n"
        response += "• \"Difference between weak and strong references?\"\n"
        response += "• \"How do you handle networking and API calls?\"\n"
        response += "• \"What's the difference between delegates and closures?\"\n"
        response += "• \"How do you optimize app performance?\"\n\n"
        
        response += "**📱 Coding Challenges:**\n"
        response += "• Build a simple table view with custom cells\n"
        response += "• Implement a networking layer with error handling\n"
        response += "• Create a custom UI component in SwiftUI\n"
        response += "• Design a data model with Core Data relationships\n"
    
    elif any(tech in keyword_str.lower() for tech in ["python", "backend", "api"]):
        response += "⚙️ **Backend Interview Focus Areas:**\n\n"
        response += "**🔧 Technical Skills:**\n"
        response += "• Python fundamentals and advanced concepts\n"
        response += "• Database design and optimization\n"
        response += "• RESTful API design and best practices\n"
        response += "• System design and architecture\n"
        response += "• Testing strategies and debugging\n\n"
        
        response += "**💡 Common Backend Questions:**\n"
        response += "• \"How do you design a scalable API?\"\n"
        response += "• \"Explain database indexing and query optimization\"\n"
        response += "• \"How do you handle authentication and security?\"\n"
        response += "• \"What's your approach to error handling?\"\n"
        response += "• \"How do you ensure API performance?\"\n\n"
        
        response += "**⚙️ System Design:**\n"
        response += "• Design a URL shortener (like bit.ly)\n"
        response += "• Build a simple chat application backend\n"
        response += "• Create a job queue processing system\n"
        response += "• Design a notification delivery system\n"
    
    else:
        response += "💻 **General Tech Interview Preparation:**\n\n"
        response += "**🔧 Core Areas:**\n"
        response += "• Algorithm and data structure fundamentals\n"
        response += "• System design thinking\n"
        response += "• Code quality and best practices\n"
        response += "• Problem-solving approach\n"
        response += "• Communication and collaboration skills\n\n"
    
    # Universal interview advice
    response += "🚀 **Interview Success Strategy:**\n\n"
    response += "**📋 Before the Interview:**\n"
    response += "• Research the company's tech stack and products\n"
    response += "• Practice coding problems on LeetCode/HackerRank\n"
    response += "• Prepare questions about the team and role\n"
    response += "• Review your portfolio projects thoroughly\n"
    response += "• Practice explaining complex concepts simply\n\n"
    
    response += "**💬 During the Interview:**\n"
    response += "• Think out loud when solving problems\n"
    response += "• Ask clarifying questions before coding\n"
    response += "• Explain your reasoning and trade-offs\n"
    response += "• Be honest about what you don't know\n"
    response += "• Show enthusiasm for learning and growth\n\n"
    
    response += "**🎯 Behavioral Questions:**\n"
    response += "• Prepare STAR method examples (Situation, Task, Action, Result)\n"
    response += "• Focus on technical challenges you've overcome\n"
    response += "• Highlight collaboration and problem-solving skills\n"
    response += "• Show genuine interest in the company's mission\n\n"
    
    # Company-specific insights
    top_companies = market_data.get("top_companies", [])[:5]
    if top_companies:
        response += "🏢 **Top Companies Currently Hiring:**\n"
        for company in top_companies:
            response += f"• {company['company']} - {company['job_count']} positions\n"
        response += "\n"
    
    response += "💡 **Pro Tip**: Practice coding problems, but also prepare to discuss your real projects in detail. Companies want to see how you think and solve actual problems."
    
    return response

async def generate_career_strategy(keywords: List[str], market_data: Dict, recent_jobs: List, user_message: str) -> str:
    """Generate intelligent career strategy based on real market data and user activity"""
    keyword_str = ", ".join(keywords) if keywords else "your skills"
    
    # Add variation to prevent identical responses
    import hashlib
    message_hash = hashlib.md5(user_message.encode()).hexdigest()[:8]
    
    # Vary response format based on message content
    if "what" in user_message.lower() and ("do" in user_message.lower() or "should" in user_message.lower()):
        response = f"💡 **Personalized Action Plan for {keyword_str}**\n\n"
    elif "help" in user_message.lower() or "advice" in user_message.lower():
        response = f"🚀 **Strategic Career Guidance for {keyword_str}**\n\n"
    elif "next" in user_message.lower() or "step" in user_message.lower():
        response = f"📋 **Next Steps in Your {keyword_str} Journey**\n\n"
    else:
        response = f"🎯 **Career Strategy for {keyword_str}** (#{message_hash})\n\n"
    
    # Market context
    total_jobs = market_data.get("market_overview", {}).get("total_jobs", 0)
    total_companies = market_data.get("market_overview", {}).get("total_companies", 0)
    keyword_jobs = market_data.get("keyword_data", {}).get("matching_jobs", 0)
    hiring_companies = market_data.get("keyword_data", {}).get("companies_hiring", 0)
    
    response += f"📊 **Market Overview:**\n"
    response += f"• {total_jobs:,} total jobs from {total_companies:,} companies\n"
    if keyword_jobs > 0:
        response += f"• {keyword_jobs} jobs match your skills\n"
        response += f"• {hiring_companies} companies actively hiring in your area\n"
    response += "\n"
    
    # Personalized insights based on recent job activity
    if recent_jobs:
        companies = list(set([job["company"] for job in recent_jobs[:5]]))
        response += f"🎯 **Your Activity Analysis:**\n"
        response += f"• Recent matches with: {', '.join(companies)}\n"
        response += f"• {len(recent_jobs)} total job notifications\n"
        response += "• This shows good market alignment with your profile\n\n"
        
        response += "**Recommended Next Steps:**\n"
        response += "1. **Research these companies** - understand their tech stacks and culture\n"
        response += "2. **Network strategically** - connect with employees at these companies\n"
        response += "3. **Tailor applications** - customize resume for each company's needs\n"
        response += "4. **Follow up professionally** on applications\n\n"
    else:
        response += "🔍 **Profile Optimization Needed:**\n"
        response += "• No recent job matches found\n"
        response += "• Consider expanding or refining your keywords\n"
        response += "• Ensure your profile reflects current market demands\n\n"
    
    # Technology-specific career advice
    if any(tech in keyword_str.lower() for tech in ["ios", "swift", "mobile"]):
        response += "📱 **iOS Career Path:**\n"
        response += "• **Years 0-2**: Master Swift, build portfolio apps, contribute to open source\n"
        response += "• **Years 3-5**: Lead small projects, mentor juniors, explore specialized areas (AR, AI)\n"
        response += "• **Years 5+**: Architect mobile solutions, technical leadership, or product management\n\n"
        
        response += "🎯 **iOS Market Opportunities:**\n"
        response += "• High demand for senior iOS developers\n"
        response += "• Remote work opportunities growing\n"
        response += "• Cross-platform skills (Flutter/React Native) add value\n"
        response += "• AI integration in mobile apps is trending\n"
    
    elif any(tech in keyword_str.lower() for tech in ["python", "backend"]):
        response += "⚙️ **Backend Career Path:**\n"
        response += "• **Years 0-2**: Master Python/frameworks, database design, API development\n"
        response += "• **Years 3-5**: System architecture, DevOps, team leadership\n"
        response += "• **Years 5+**: Staff engineer, architect, or engineering management\n\n"
        
        response += "🎯 **Backend Market Opportunities:**\n"
        response += "• AI/ML integration driving demand\n"
        response += "• Cloud-native development essential\n"
        response += "• Microservices expertise valuable\n"
        response += "• DevOps skills increasingly important\n"
    
    # Top companies hiring
    top_companies = market_data.get("top_companies", [])[:5]
    if top_companies:
        response += f"\n🏢 **Top Hiring Companies:**\n"
        for i, company in enumerate(top_companies, 1):
            response += f"{i}. {company['company']} - {company['job_count']} open positions\n"
    
    response += f"\n💡 **Key Insight**: With {keyword_jobs} current opportunities, focus on quality applications to companies that align with your career goals rather than mass applications."
    
    return response

async def generate_company_insights(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate insights about companies and employers"""
    keyword_str = ", ".join(keywords) if keywords else "your skills"
    
    response = f"🏢 **Company Insights for {keyword_str}**\n\n"
    
    # Top companies from market data
    top_companies = market_data.get("top_companies", [])
    hiring_companies = market_data.get("keyword_data", {}).get("companies_hiring", 0)
    
    if top_companies:
        response += "📈 **Most Active Employers:**\n"
        for i, company in enumerate(top_companies[:8], 1):
            response += f"{i}. **{company['company']}** - {company['job_count']} open positions\n"
        response += "\n"
    
    if hiring_companies > 0:
        response += f"🎯 **Companies hiring for {keyword_str}**: {hiring_companies} companies actively recruiting\n\n"
    
    # Company research strategy
    response += "🔍 **Company Research Strategy:**\n"
    response += "• **Glassdoor**: Employee reviews, salary data, interview experiences\n"
    response += "• **LinkedIn**: Company updates, employee connections, growth trajectory\n"
    response += "• **GitHub**: Open source contributions, engineering practices\n"
    response += "• **Stack Overflow**: Technology stack, engineering blog posts\n"
    response += "• **Crunchbase**: Funding, growth stage, leadership team\n\n"
    
    # Company types and what to look for
    response += "💼 **Company Types & Considerations:**\n"
    response += "• **Startups**: High growth potential, equity, flexibility, but higher risk\n"
    response += "• **Scale-ups**: Growing fast, good career advancement, moderate stability\n"
    response += "• **Enterprise**: Stable, structured, good benefits, slower innovation\n"
    response += "• **Tech Giants**: Prestigious, excellent comp, competitive, complex politics\n\n"
    
    # Red flags and green flags
    response += "🚩 **Red Flags to Watch:**\n"
    response += "• High employee turnover (check LinkedIn)\n"
    response += "• Consistent negative Glassdoor reviews\n"
    response += "• Unclear or unrealistic job descriptions\n"
    response += "• Poor communication during interview process\n\n"
    
    response += "✅ **Green Flags to Look For:**\n"
    response += "• Clear career progression paths\n"
    response += "• Investment in employee development\n"
    response += "• Strong engineering culture and practices\n"
    response += "• Transparent communication about challenges\n"
    response += "• Good work-life balance policies\n"
    
    return response

async def generate_remote_work_insights(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate insights about remote work opportunities"""
    keyword_str = ", ".join(keywords) if keywords else "your field"
    
    response = f"🏠 **Remote Work Insights for {keyword_str}**\n\n"
    
    # Get remote work data
    try:
        remote_query = """
            SELECT 
                COUNT(*) as total_remote,
                COUNT(DISTINCT company) as companies_offering_remote
            FROM scraper.jobs_jobpost
            WHERE LOWER(title) LIKE '%remote%' OR LOWER(title) LIKE '%work from home%'
        """
        remote_result = await db_manager.execute_query(remote_query)
        
        if remote_result:
            remote_jobs = remote_result[0]['total_remote']
            remote_companies = remote_result[0]['companies_offering_remote']
            total_jobs = market_data.get("market_overview", {}).get("total_jobs", 1)
            remote_percentage = (remote_jobs / total_jobs) * 100 if total_jobs > 0 else 0
            
            response += f"📊 **Remote Work Market:**\n"
            response += f"• {remote_jobs} remote positions available ({remote_percentage:.1f}% of total)\n"
            response += f"• {remote_companies} companies offering remote work\n"
            response += f"• Growing trend in post-pandemic job market\n\n"
    except Exception as e:
        logger.error(f"Error getting remote data: {e}")
    
    # Technology-specific remote opportunities
    if any(tech in keyword_str.lower() for tech in ["ios", "swift", "mobile"]):
        response += "📱 **iOS Remote Opportunities:**\n"
        response += "• **High demand**: Mobile development is very remote-friendly\n"
        response += "• **Global opportunities**: Work for companies worldwide\n"
        response += "• **App Store success**: Some developers work fully independently\n"
        response += "• **Collaboration tools**: Xcode Cloud, GitHub enable remote workflows\n\n"
    
    elif any(tech in keyword_str.lower() for tech in ["backend", "api", "python"]):
        response += "⚙️ **Backend Remote Opportunities:**\n"
        response += "• **Excellent remote fit**: Backend work is location-independent\n"
        response += "• **DevOps integration**: Remote-first infrastructure is standard\n"
        response += "• **Async workflows**: Backend development suits async communication\n"
        response += "• **Global talent access**: Companies hire globally for backend roles\n\n"
    
    # Remote work best practices
    response += "🎯 **Remote Work Success Tips:**\n"
    response += "• **Communication**: Over-communicate progress and blockers\n"
    response += "• **Time management**: Set clear boundaries between work and personal time\n"
    response += "• **Home office**: Invest in good setup (monitor, chair, lighting)\n"
    response += "• **Network**: Join remote-first communities and events\n"
    response += "• **Skills**: Develop strong written communication abilities\n\n"
    
    # Finding remote opportunities
    response += "🔍 **Where to Find Remote Jobs:**\n"
    response += "• **Remote-first companies**: GitLab, Buffer, Zapier, Automattic\n"
    response += "• **Job boards**: AngelList, Remote.co, We Work Remotely\n"
    response += "• **Freelance**: Upwork, Toptal for contract/consulting work\n"
    response += "• **Networking**: Twitter, LinkedIn remote work communities\n\n"
    
    response += "💡 **Pro Tip**: Many companies now offer hybrid or full remote options even if not explicitly advertised. Don't hesitate to ask during interviews!"
    
    return response

async def generate_market_trends(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate market trend insights"""
    response = "📈 **Technology Market Trends**\n\n"
    
    # Technology trends from market data
    tech_trends = market_data.get("tech_trends", [])
    if tech_trends:
        response += "🔥 **Hottest Technologies (by job demand):**\n"
        for i, tech in enumerate(tech_trends[:8], 1):
            response += f"{i}. {tech['tech']}: {tech['job_count']} current openings\n"
        response += "\n"
    
    # General market trends
    response += "🚀 **Key Market Trends 2025:**\n"
    response += "• **AI Integration**: Every role now expects some AI familiarity\n"
    response += "• **Remote/Hybrid**: 70%+ of companies offer flexible work\n"
    response += "• **Cloud Native**: AWS/Azure skills increasingly essential\n"
    response += "• **Mobile First**: iOS/Android development still growing\n"
    response += "• **DevOps Culture**: Developers expected to understand deployment\n"
    response += "• **Security Focus**: Security skills premium across all roles\n\n"
    
    # Skill predictions
    response += "🔮 **Skills to Watch:**\n"
    response += "• **AI/ML**: ChatGPT integration, prompt engineering\n"
    response += "• **Swift/SwiftUI**: Apple's continued ecosystem growth\n"
    response += "• **Rust**: Growing for system programming and performance\n"
    response += "• **Kubernetes**: Container orchestration becoming standard\n"
    response += "• **TypeScript**: JavaScript's typed future\n\n"
    
    # Salary trends
    response += "💰 **Salary Trends:**\n"
    response += "• Senior roles: 15-25% increase year-over-year\n"
    response += "• Remote positions: Global salary competition\n"
    response += "• AI specialists: 30-50% premium over base roles\n"
    response += "• Mobile experts: Sustained high demand and compensation\n\n"
    
    # Industry insights
    total_jobs = market_data.get("market_overview", {}).get("total_jobs", 0)
    total_companies = market_data.get("market_overview", {}).get("total_companies", 0)
    
    if total_jobs > 0 and total_companies > 0:
        jobs_per_company = total_jobs / total_companies
        response += f"📊 **Current Market Snapshot:**\n"
        response += f"• {total_jobs:,} total positions tracked\n"
        response += f"• {total_companies:,} companies actively hiring\n"
        response += f"• {jobs_per_company:.1f} average jobs per company\n"
        response += "• Strong seller's market for skilled developers\n\n"
    
    response += "💡 **Strategic Advice**: Focus on fundamentals first, then add trending technologies that align with your career goals. Don't chase every trend - depth beats breadth."
    
    return response

async def generate_keyword_specific_advice(matched_keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate advice specific to matched keywords"""
    keyword_str = ", ".join(matched_keywords)
    
    response = f"🎯 **Focused Advice for {keyword_str}**\n\n"
    
    # Get specific data for these keywords
    keyword_jobs = market_data.get("keyword_data", {}).get("matching_jobs", 0)
    hiring_companies = market_data.get("keyword_data", {}).get("companies_hiring", 0)
    
    if keyword_jobs > 0:
        response += f"📊 **Market Data for Your Skills:**\n"
        response += f"• {keyword_jobs} current job openings\n"
        response += f"• {hiring_companies} companies actively recruiting\n"
        response += "• Strong market demand for your skill set\n\n"
    
    # Specific advice based on the primary keyword
    primary_keyword = matched_keywords[0].lower()
    
    if primary_keyword in ["ios", "swift"]:
        response += "📱 **iOS/Swift Specific Insights:**\n"
        response += "• Apple's ecosystem continues strong growth\n"
        response += "• SwiftUI adoption accelerating across industry\n"
        response += "• Vision Pro development opening new opportunities\n"
        response += "• Cross-platform skills (React Native) add value\n"
        response += "• App Store optimization expertise in demand\n\n"
        
        response += "🚀 **Next Steps:**\n"
        response += "• Build apps showcasing SwiftUI and modern iOS features\n"
        response += "• Contribute to iOS open source projects\n"
        response += "• Learn app analytics and performance optimization\n"
        response += "• Explore AR/VR with ARKit and Vision Pro\n"
    
    elif primary_keyword in ["python", "backend"]:
        response += "🐍 **Python/Backend Specific Insights:**\n"
        response += "• AI/ML integration driving huge demand\n"
        response += "• FastAPI and async Python trending\n"
        response += "• Cloud deployment skills essential\n"
        response += "• Data engineering roles growing rapidly\n"
        response += "• API design expertise highly valued\n\n"
        
        response += "🚀 **Next Steps:**\n"
        response += "• Build ML-powered APIs with FastAPI\n"
        response += "• Learn cloud deployment (AWS, Docker)\n"
        response += "• Practice system design and architecture\n"
        response += "• Contribute to Python open source projects\n"
    
    elif primary_keyword in ["react", "frontend", "javascript"]:
        response += "⚛️ **Frontend/React Specific Insights:**\n"
        response += "• React 18+ and Next.js in high demand\n"
        response += "• TypeScript adoption now standard\n"
        response += "• Performance optimization crucial\n"
        response += "• Full-stack JavaScript developers sought\n"
        response += "• Component library experience valuable\n\n"
        
        response += "🚀 **Next Steps:**\n"
        response += "• Master Next.js and server-side rendering\n"
        response += "• Build performant, accessible components\n"
        response += "• Learn state management (Redux Toolkit, Zustand)\n"
        response += "• Practice responsive design and animations\n"
    
    else:
        response += f"💡 **General Advice for {keyword_str}:**\n"
        response += "• Research current best practices in your field\n"
        response += "• Build projects that showcase real-world problem solving\n"
        response += "• Network with professionals in your technology area\n"
        response += "• Stay updated with official documentation and communities\n"
        response += "• Consider adjacent skills that complement your expertise\n\n"
    
    # Market positioning advice
    response += "📈 **Market Positioning:**\n"
    response += f"• Position yourself as a {keyword_str} specialist\n"
    response += "• Highlight unique projects and achievements\n"
    response += "• Share knowledge through blogs, talks, or open source\n"
    response += "• Build a portfolio that tells a compelling story\n"
    
    return response

async def generate_general_assistance(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate general helpful assistance with variations"""
    keyword_str = ", ".join(keywords) if keywords else "technology"
    
    # Vary greeting based on user message
    if "hello" in user_message.lower() or "hi" in user_message.lower():
        response = f"👋 **Hello! I'm your AI Career Assistant**\n\n"
        response += f"I specialize in **{keyword_str}** and I'm here to help with your career journey!\n\n"
    elif "help" in user_message.lower():
        response = f"🆘 **How I Can Help You with {keyword_str}**\n\n"
    elif "what can" in user_message.lower() or "what do you" in user_message.lower():
        response = f"🔧 **My Capabilities for {keyword_str} Professionals**\n\n"
    else:
        response = f"🤖 **AI Career Assistant - {keyword_str} Specialist**\n\n"
    
    # Market context
    total_jobs = market_data.get("market_overview", {}).get("total_jobs", 0)
    total_companies = market_data.get("market_overview", {}).get("total_companies", 0)
    
    if total_jobs > 0:
        response += f"📊 **Current Market:** {total_jobs:,} jobs from {total_companies:,} companies\n\n"
    
    response += "💬 **I can help you with:**\n\n"
    response += "🔍 **Job Search Strategy:**\n"
    response += "• Salary negotiations and market rates\n"
    response += "• Company research and insights\n"
    response += "• Interview preparation and tips\n"
    response += "• Portfolio and resume optimization\n\n"
    
    response += "📈 **Career Development:**\n"
    response += "• Skill development roadmaps\n"
    response += "• Technology trend analysis\n"
    response += "• Career path planning\n"
    response += "• Learning resource recommendations\n\n"
    
    response += "🌐 **Market Intelligence:**\n"
    response += "• Remote work opportunities\n"
    response += "• Company hiring patterns\n"
    response += "• Technology demand trends\n"
    response += "• Compensation benchmarking\n\n"
    
    if keywords:
        response += f"🎯 **Your Focus:** I have context about your {keyword_str} interests and can provide personalized advice.\n\n"
    
    response += "💡 **Try asking me:**\n"
    response += "• \"What's the salary range for iOS developers?\"\n"
    response += "• \"Which companies are hiring for Python roles?\"\n"
    response += "• \"How can I improve my interview skills?\"\n"
    response += "• \"What technologies should I learn next?\"\n"
    response += "• \"Show me remote work opportunities\"\n\n"
    
    response += "🚀 **Let's build your career together!** What specific area would you like to explore?"
    
    return response

async def generate_fallback_response(keywords: List[str], recent_jobs: List, user_message: str) -> str:
    """Enhanced fallback when AI services fail"""
    keyword_str = ", ".join(keywords) if keywords else "your skills"
    
    response = f"🤖 **Quick Assistance for {keyword_str}**\n\n"
    
    if recent_jobs:
        companies = [job["company"] for job in recent_jobs[:3]]
        response += f"✨ You've had recent matches with: {', '.join(companies)}\n\n"
        response += "**Suggestions:**\n"
        response += "• Research these companies' tech stacks and culture\n"
        response += "• Check their career pages for new openings\n"
        response += "• Network with current employees on LinkedIn\n"
        response += "• Tailor your applications to their specific needs\n\n"
    
    response += "💡 **I can help with:**\n"
    response += "• Salary insights and market rates\n"
    response += "• Skill development recommendations\n"
    response += "• Interview preparation strategies\n"
    response += "• Company research and analysis\n"
    response += "• Career path planning\n\n"
    
    response += f"Ask me something specific about {keyword_str} and I'll provide detailed, data-driven insights!"
    
    return response

async def generate_clarification_response(keywords: List[str], market_data: Dict, user_message: str) -> str:
    """Generate clarifying questions when intent is unclear"""
    keyword_str = ", ".join(keywords) if keywords else "your field"
    
    # Get market context for relevance
    total_jobs = market_data.get("market_overview", {}).get("total_jobs", 0)
    keyword_jobs = market_data.get("keyword_data", {}).get("matching_jobs", 0)
    
    response = f"🤔 **Let me help you better with {keyword_str}!**\n\n"
    
    if keyword_jobs > 0:
        response += f"I found {keyword_jobs} current job opportunities matching your skills from {total_jobs:,} total positions.\n\n"
    
    response += "I can provide specific insights about:\n\n"
    response += "💰 **Salary & Compensation**: \"What's the salary for my skills?\"\n"
    response += "🚀 **Skill Development**: \"What skills should I learn next?\"\n"
    response += "🎯 **Career Strategy**: \"What career advice do you have?\"\n"
    response += "🎤 **Interview Prep**: \"How should I prepare for interviews?\"\n"
    response += "🏢 **Company Research**: \"Which companies are hiring?\"\n"
    response += "🏠 **Remote Work**: \"Are there remote opportunities?\"\n"
    response += "📈 **Market Trends**: \"What are the current tech trends?\"\n\n"
    
    # Add personalized suggestion based on keywords
    if any(tech in keyword_str.lower() for tech in ["engineer", "developer", "programming"]):
        response += "💡 **Quick suggestion**: Try asking \"What's the career path for engineers?\" or \"What skills are in demand?\"\n\n"
    elif any(tech in keyword_str.lower() for tech in ["manager", "management", "lead"]):
        response += "💡 **Quick suggestion**: Try asking \"How do I transition to management?\" or \"What companies hire managers?\"\n\n"
    elif any(tech in keyword_str.lower() for tech in ["ai", "ml", "data"]):
        response += "💡 **Quick suggestion**: Try asking \"What's the AI job market like?\" or \"What AI skills should I learn?\"\n\n"
    else:
        response += "💡 **Quick suggestion**: Try asking \"What career advice do you have?\" or \"What skills should I focus on?\"\n\n"
    
    response += "What specific area would you like to explore? 🚀"
    
    return response

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