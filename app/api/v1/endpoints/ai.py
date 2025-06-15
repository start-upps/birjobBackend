from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import json
import aiohttp
from datetime import datetime

from app.core.config import settings

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