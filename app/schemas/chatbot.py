from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ConversationMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")

class ChatRequest(BaseModel):
    device_id: str = Field(..., description="User's device identifier")
    message: str = Field(..., min_length=1, max_length=1000, description="User's message")
    conversation_history: Optional[List[ConversationMessage]] = Field(
        default=[], 
        description="Previous conversation messages for context"
    )
    include_user_context: bool = Field(
        default=True, 
        description="Whether to include user's job preferences in context"
    )

class ChatResponse(BaseModel):
    success: bool = True
    response: str = Field(..., description="Chatbot's response")
    timestamp: str = Field(..., description="Response timestamp")
    model: str = Field(default="gemini-2.5-flash", description="AI model used")
    error: Optional[str] = Field(None, description="Error message if any")

class JobRecommendationsRequest(BaseModel):
    device_id: str = Field(..., description="User's device identifier") 
    keywords: Optional[List[str]] = Field(
        default=None, 
        description="Job keywords to base recommendations on"
    )
    location: Optional[str] = Field(None, description="Preferred job location")

class JobRecommendationsResponse(BaseModel):
    success: bool = True
    recommendations: str = Field(..., description="Job search recommendations")
    keywords: List[str] = Field(..., description="Keywords used for recommendations")
    location: Optional[str] = Field(None, description="Location considered")
    timestamp: str = Field(..., description="Response timestamp")
    error: Optional[str] = Field(None, description="Error message if any")

class JobAnalysisRequest(BaseModel):
    device_id: str = Field(..., description="User's device identifier")
    job_id: Optional[int] = Field(None, description="Job ID from database")
    job_title: str = Field(..., description="Job title to analyze")
    job_company: str = Field(..., description="Company name")
    job_description: Optional[str] = Field(None, description="Job description text")

class JobAnalysisResponse(BaseModel):
    success: bool = True
    analysis: str = Field(..., description="Job analysis and insights")
    job_title: str = Field(..., description="Analyzed job title")
    company: str = Field(..., description="Company name")
    timestamp: str = Field(..., description="Response timestamp")
    error: Optional[str] = Field(None, description="Error message if any")

class ChatbotStatsResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any] = Field(..., description="Chatbot usage statistics")

class UserContext(BaseModel):
    """Internal model for user context"""
    keywords: List[str] = Field(default=[], description="User's job keywords")
    recent_jobs: List[Dict[str, Any]] = Field(default=[], description="Recently viewed jobs")
    location: Optional[str] = Field(None, description="User's location preference")