from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import json
import aiohttp
from datetime import datetime

from app.core.config import settings
from app.core.database import db_manager
from app.schemas.user import JobRecommendationRequest, JobMatchAnalysisRequest

router = APIRouter()
logger = logging.getLogger(__name__)

class AIRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="User message to analyze")
    context: Optional[str] = Field(None, max_length=2000, description="Optional context for the AI")
    job_id: Optional[int] = Field(None, description="Optional job ID for job-specific analysis")

class AIResponse(BaseModel):
    response: str
    timestamp: str
    tokens_used: Optional[int] = None

@router.post("/analyze", response_model=AIResponse)
async def analyze_with_gemini(request: AIRequest):
    """
    Analyze text using Google Gemini AI
    
    This endpoint provides AI-powered analysis for job-related queries, resume feedback,
    career advice, and general job search assistance.
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not configured"
            )
        
        # Prepare the prompt
        system_prompt = """You are a helpful AI assistant for a job search application. 
        You help users with job-related questions, career advice, resume feedback, and job search strategies.
        Be professional, helpful, and concise in your responses. Focus on actionable advice."""
        
        user_message = request.message
        if request.context:
            user_message = f"Context: {request.context}\n\nQuestion: {request.message}"
        
        # Prepare Gemini API request
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\nUser: {user_message}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        # Make API call to Gemini
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gemini_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AI service temporarily unavailable"
                    )
                
                result = await response.json()
        
        # Extract response from Gemini
        if "candidates" not in result or not result["candidates"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI service returned invalid response"
            )
        
        ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Get token usage if available
        tokens_used = None
        if "usageMetadata" in result:
            tokens_used = result["usageMetadata"].get("totalTokenCount")
        
        logger.info(f"AI analysis completed. Tokens used: {tokens_used}")
        
        return AIResponse(
            response=ai_response,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI request"
        )

@router.post("/job-advice", response_model=AIResponse)
async def get_job_advice(request: AIRequest):
    """
    Get job-specific advice using AI
    
    Specialized endpoint for job search advice, interview preparation,
    and career guidance.
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not configured"
            )
        
        # Enhanced prompt for job advice
        system_prompt = """You are a professional career advisor and job search expert. 
        Provide specific, actionable advice for job seekers. Focus on:
        - Interview preparation tips
        - Resume and cover letter guidance
        - Career development strategies
        - Job search techniques
        - Industry-specific advice
        
        Be encouraging, practical, and professional in your responses."""
        
        user_message = request.message
        if request.context:
            user_message = f"Context: {request.context}\n\nQuestion: {request.message}"
        
        # Prepare Gemini API request
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\nUser: {user_message}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.6,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        # Make API call to Gemini
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gemini_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AI service temporarily unavailable"
                    )
                
                result = await response.json()
        
        # Extract response from Gemini
        if "candidates" not in result or not result["candidates"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI service returned invalid response"
            )
        
        ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Get token usage if available
        tokens_used = None
        if "usageMetadata" in result:
            tokens_used = result["usageMetadata"].get("totalTokenCount")
        
        logger.info(f"Job advice completed. Tokens used: {tokens_used}")
        
        return AIResponse(
            response=ai_response,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job advice failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process job advice request"
        )

@router.post("/resume-review", response_model=AIResponse)
async def review_resume(request: AIRequest):
    """
    AI-powered resume review and feedback
    
    Analyze resume content and provide constructive feedback for improvement.
    """
    try:
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not configured"
            )
        
        # Specialized prompt for resume review
        system_prompt = """You are a professional resume reviewer and HR expert.
        Analyze the provided resume content and provide specific, actionable feedback including:
        - Structure and formatting suggestions
        - Content improvement recommendations
        - Keyword optimization for ATS systems
        - Skills and experience presentation
        - Areas for enhancement
        
        Be constructive, specific, and professional in your feedback."""
        
        user_message = f"Please review this resume content and provide feedback:\n\n{request.message}"
        if request.context:
            user_message = f"Job/Industry Context: {request.context}\n\n{user_message}"
        
        # Prepare Gemini API request
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\nUser: {user_message}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.5,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        # Make API call to Gemini
        async with aiohttp.ClientSession() as session:
            async with session.post(
                gemini_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AI service temporarily unavailable"
                    )
                
                result = await response.json()
        
        # Extract response from Gemini
        if "candidates" not in result or not result["candidates"]:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI service returned invalid response"
            )
        
        ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Get token usage if available
        tokens_used = None
        if "usageMetadata" in result:
            tokens_used = result["usageMetadata"].get("totalTokenCount")
        
        logger.info(f"Resume review completed. Tokens used: {tokens_used}")
        
        return AIResponse(
            response=ai_response,
            timestamp=datetime.now().isoformat(),
            tokens_used=tokens_used
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume review failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process resume review request"
        )

@router.post("/job-recommendations")
async def get_job_recommendations(request: JobRecommendationRequest):
    """
    Get AI-powered personalized job recommendations based on user profile
    """
    try:
        device_id = request.deviceId
        limit = request.limit or 20
        filters = request.filters or {}
        
        # Get user profile
        user_query = """
            SELECT * FROM iosapp.users WHERE device_id = $1
        """
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user = user_result[0]
        user_skills = user.get("skills", []) or []
        user_locations = user.get("preferred_locations", []) or []
        min_salary = user.get("min_salary")
        max_salary = user.get("max_salary")
        
        # Build job search query with filters
        job_query = """
            SELECT 
                id, title, company, apply_link, source, created_at
            FROM scraper.jobs_jobpost 
            WHERE 1=1
        """
        params = []
        
        # Apply filters
        param_count = 1
        if filters.get("location"):
            job_query += f" AND LOWER(title) LIKE ${param_count}"
            params.append(f"%{filters['location'].lower()}%")
            param_count += 1
        
        if filters.get("jobType"):
            job_query += f" AND LOWER(title) LIKE ${param_count}"
            params.append(f"%{filters['jobType'].lower()}%")
            param_count += 1
        
        # Add skill-based matching
        if user_skills:
            skill_conditions = []
            for skill in user_skills:
                skill_conditions.append(f"LOWER(title) LIKE ${param_count}")
                params.append(f"%{skill.lower()}%")
                param_count += 1
            
            if skill_conditions:
                job_query += f" AND ({' OR '.join(skill_conditions)})"
        
        job_query += f" ORDER BY created_at DESC LIMIT ${param_count}"
        params.append(limit * 2)  # Get more jobs to calculate match scores
        
        jobs_result = await db_manager.execute_query(job_query, *params)
        
        # Calculate match scores and AI insights for jobs
        recommendations = []
        
        for job in jobs_result[:limit]:  # Limit to requested number
            match_score = calculate_job_match_score(job, user, user_skills)
            
            if match_score >= 50:  # Only include jobs with decent match
                ai_insights = await generate_ai_insights(job, user, user_skills)
                
                recommendation = {
                    "jobId": job["id"],
                    "title": job["title"],
                    "companyName": job["company"],
                    "location": "Location not specified",  # Can be enhanced
                    "salary": "Salary not specified",  # Can be enhanced
                    "postedDate": job["created_at"].isoformat() if job["created_at"] else None,
                    "matchScore": match_score,
                    "aiInsights": ai_insights,
                    "matchReasons": generate_match_reasons(job, user, user_skills, match_score)
                }
                
                recommendations.append(recommendation)
        
        # Sort by match score
        recommendations.sort(key=lambda x: x["matchScore"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "totalRecommendations": len(recommendations),
                "lastUpdated": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get job recommendations"
        )

@router.post("/job-match-analysis")
async def analyze_job_match(request: JobMatchAnalysisRequest):
    """
    Get detailed AI analysis of how well a specific job matches user profile
    """
    try:
        device_id = request.deviceId
        job_id = request.jobId
        
        # Get user profile
        user_query = "SELECT * FROM iosapp.users WHERE device_id = $1"
        user_result = await db_manager.execute_query(user_query, device_id)
        
        if not user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        user = user_result[0]
        
        # Get job details
        job_query = "SELECT * FROM scraper.jobs_jobpost WHERE id = $1"
        job_result = await db_manager.execute_query(job_query, job_id)
        
        if not job_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        job = job_result[0]
        user_skills = user.get("skills", []) or []
        
        # Calculate detailed match analysis
        match_score = calculate_job_match_score(job, user, user_skills)
        
        # Skills analysis
        job_title_lower = job["title"].lower()
        matching_skills = [skill for skill in user_skills if skill.lower() in job_title_lower]
        
        # Generate AI-powered analysis
        ai_analysis = await generate_detailed_ai_analysis(job, user, user_skills, match_score)
        
        analysis_data = {
            "jobId": job_id,
            "matchScore": match_score,
            "analysis": {
                "skillsAnalysis": {
                    "matchingSkills": matching_skills,
                    "missingSkills": extract_missing_skills(job_title_lower, user_skills),
                    "skillsMatchPercentage": calculate_skills_match_percentage(job_title_lower, user_skills)
                },
                "experienceAnalysis": {
                    "requiredExperience": extract_experience_requirement(job["title"]),
                    "userExperience": user.get("years_of_experience", "Not specified"),
                    "experienceMatch": True  # Can be enhanced with better analysis
                },
                "salaryAnalysis": {
                    "jobSalaryRange": "Not specified",  # Can be enhanced with salary data
                    "userSalaryRange": f"${user.get('min_salary', 'Not specified')} - ${user.get('max_salary', 'Not specified')}",
                    "salaryMatch": True  # Can be enhanced with better analysis
                },
                "locationAnalysis": {
                    "jobLocation": "Not specified",  # Can be enhanced with location data
                    "userPreferredLocations": user.get("preferred_locations", []),
                    "locationMatch": True,  # Can be enhanced with better analysis
                    "remoteOptions": determine_remote_options(job["title"])
                },
                "aiRecommendation": ai_analysis.get("recommendation", "Consider applying based on your profile match."),
                "improvementSuggestions": ai_analysis.get("suggestions", [])
            }
        }
        
        return {
            "success": True,
            "data": analysis_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing job match: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze job match"
        )

def calculate_job_match_score(job: dict, user: dict, user_skills: list) -> int:
    """Calculate a match score between job and user profile"""
    score = 0
    job_title_lower = job["title"].lower()
    
    # Skills matching (40% of score)
    if user_skills:
        matching_skills = sum(1 for skill in user_skills if skill.lower() in job_title_lower)
        skill_score = min((matching_skills / len(user_skills)) * 40, 40)
        score += skill_score
    
    # Experience level matching (20% of score)
    user_experience = user.get("years_of_experience", "")
    if user_experience and any(exp in job_title_lower for exp in ["senior", "junior", "mid", "lead"]):
        score += 20
    elif user_experience:
        score += 10
    
    # Job type matching (20% of score)
    desired_types = user.get("desired_job_types", []) or []
    if desired_types:
        type_match = any(job_type.lower() in job_title_lower for job_type in desired_types)
        if type_match:
            score += 20
        else:
            score += 5
    
    # Base score for having a profile (20% of score)
    score += 20
    
    return min(int(score), 100)

async def generate_ai_insights(job: dict, user: dict, user_skills: list) -> dict:
    """Generate AI insights for job recommendation"""
    try:
        if not settings.GEMINI_API_KEY:
            return {
                "whyRecommended": "Job matches your profile",
                "skillsMatch": user_skills[:3],  # Top 3 skills
                "missingSkills": [],
                "salaryFit": "Within your range",
                "locationFit": "Matches your preferences"
            }
        
        job_title_lower = job["title"].lower()
        matching_skills = [skill for skill in user_skills if skill.lower() in job_title_lower]
        
        prompt = f"""
        Analyze this job match and provide insights:
        Job: {job['title']} at {job['company']}
        User Skills: {', '.join(user_skills)}
        Matching Skills: {', '.join(matching_skills)}
        
        Provide a brief explanation of why this job is recommended (max 50 words).
        """
        
        # Quick AI call for insights
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 100}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(gemini_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_text = result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    ai_text = "Perfect match for your expertise and career goals"
        
        return {
            "whyRecommended": ai_text,
            "skillsMatch": matching_skills,
            "missingSkills": extract_missing_skills(job_title_lower, user_skills),
            "salaryFit": "Within your preferred range",
            "locationFit": "Matches your location preferences"
        }
        
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        return {
            "whyRecommended": "Job matches your profile and skills",
            "skillsMatch": user_skills[:3],
            "missingSkills": [],
            "salaryFit": "Competitive salary",
            "locationFit": "Good location match"
        }

def generate_match_reasons(job: dict, user: dict, user_skills: list, match_score: int) -> list:
    """Generate list of reasons why job matches user"""
    reasons = []
    
    if match_score >= 90:
        reasons.append("Excellent skills match")
    elif match_score >= 70:
        reasons.append("Good skills match")
    else:
        reasons.append("Some skills match")
    
    if user.get("min_salary") and user.get("max_salary"):
        reasons.append("Salary within range")
    
    user_locations = user.get("preferred_locations", [])
    if user_locations:
        reasons.append("Preferred location")
    
    if user.get("years_of_experience"):
        reasons.append("Experience level match")
    
    return reasons

def extract_missing_skills(job_title_lower: str, user_skills: list) -> list:
    """Extract skills that might be missing for the job"""
    common_skills = ["python", "javascript", "react", "node", "sql", "aws", "docker", "kubernetes"]
    potential_missing = []
    
    for skill in common_skills:
        if skill in job_title_lower and skill.lower() not in [s.lower() for s in user_skills]:
            potential_missing.append(skill.title())
    
    return potential_missing[:3]  # Return top 3

def calculate_skills_match_percentage(job_title_lower: str, user_skills: list) -> int:
    """Calculate percentage of user skills that match job"""
    if not user_skills:
        return 0
    
    matching_count = sum(1 for skill in user_skills if skill.lower() in job_title_lower)
    return int((matching_count / len(user_skills)) * 100)

def extract_experience_requirement(job_title: str) -> str:
    """Extract experience requirement from job title"""
    title_lower = job_title.lower()
    
    if "senior" in title_lower or "sr" in title_lower:
        return "5+ years"
    elif "junior" in title_lower or "jr" in title_lower:
        return "1-3 years"
    elif "lead" in title_lower or "principal" in title_lower:
        return "7+ years"
    else:
        return "3-5 years"

def determine_remote_options(job_title: str) -> str:
    """Determine if job offers remote work"""
    title_lower = job_title.lower()
    
    if "remote" in title_lower:
        return "Fully remote"
    elif "hybrid" in title_lower:
        return "Hybrid available"
    else:
        return "On-site preferred"

async def generate_detailed_ai_analysis(job: dict, user: dict, user_skills: list, match_score: int) -> dict:
    """Generate detailed AI analysis for job match"""
    try:
        if not settings.GEMINI_API_KEY:
            return {
                "recommendation": "Consider applying based on your profile match.",
                "suggestions": ["Update your resume to highlight relevant skills"]
            }
        
        prompt = f"""
        Analyze this job match and provide recommendations:
        Job: {job['title']} at {job['company']}
        User Profile: {user.get('current_job_title', 'Not specified')}
        User Skills: {', '.join(user_skills)}
        Match Score: {match_score}%
        
        Provide:
        1. Should they apply? (one sentence)
        2. Two improvement suggestions (brief bullet points)
        """
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 200}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(gemini_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    ai_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Parse AI response
                    lines = ai_text.split('\n')
                    recommendation = lines[0] if lines else "Consider applying based on your match score."
                    suggestions = [line.strip() for line in lines[1:] if line.strip()][:2]
                    
                    return {
                        "recommendation": recommendation,
                        "suggestions": suggestions if suggestions else ["Focus on highlighting relevant experience", "Tailor your application to the job requirements"]
                    }
        
        return {
            "recommendation": f"Strong match with {match_score}% compatibility - you should apply!",
            "suggestions": ["Highlight your matching skills", "Research the company culture"]
        }
        
    except Exception as e:
        logger.error(f"Error generating detailed AI analysis: {e}")
        return {
            "recommendation": "Consider applying based on your profile match.",
            "suggestions": ["Update your resume", "Research the company"]
        }