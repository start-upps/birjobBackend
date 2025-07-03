"""
Gemini AI Chatbot Service for Job-related Conversations
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiChatbotService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("Gemini API key not configured")
            self.model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini chatbot service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.model = None
    
    def _create_job_context_prompt(self, user_keywords: List[str] = None, recent_jobs: List[Dict] = None) -> str:
        """Create context prompt based on user's job preferences and recent activity"""
        context = """You are a helpful job search assistant for an iOS job application. 
Your role is to help users with:
- Job search advice and career guidance
- Resume and interview tips
- Industry insights and trends
- Skill development recommendations
- Job market analysis

Keep responses concise, helpful, and focused on job-related topics."""
        
        if user_keywords:
            context += f"\n\nUser's job interests: {', '.join(user_keywords)}"
        
        if recent_jobs:
            job_titles = [job.get('title', '') for job in recent_jobs[:3]]
            context += f"\n\nUser recently viewed jobs: {', '.join(job_titles)}"
        
        context += "\n\nProvide helpful, actionable advice while being encouraging and professional."
        return context
    
    async def chat(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate chatbot response using Gemini AI
        
        Args:
            message: User's message
            conversation_history: Previous conversation messages
            user_context: User's job preferences, recent activity, etc.
        
        Returns:
            Dict containing response and metadata
        """
        if not self.model:
            return {
                "success": False,
                "error": "Chatbot service not available",
                "response": "I'm sorry, the chatbot service is currently unavailable. Please try again later."
            }
        
        try:
            # Extract user context
            user_keywords = user_context.get('keywords', []) if user_context else []
            recent_jobs = user_context.get('recent_jobs', []) if user_context else []
            
            # Build conversation prompt
            system_prompt = self._create_job_context_prompt(user_keywords, recent_jobs)
            
            # Build conversation history
            conversation_text = system_prompt + "\n\n"
            
            if conversation_history:
                for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    conversation_text += f"{role.capitalize()}: {content}\n"
            
            conversation_text += f"User: {message}\nAssistant:"
            
            # Generate response
            response = await self._generate_response(conversation_text)
            
            return {
                "success": True,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "model": "gemini-1.5-flash"
            }
            
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble processing your request right now. Please try rephrasing your question."
            }
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response from Gemini model"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    async def get_job_recommendations(self, user_keywords: List[str], user_location: str = None) -> Dict[str, Any]:
        """Get job search recommendations based on user's keywords"""
        if not self.model:
            return {
                "success": False,
                "error": "Chatbot service not available"
            }
        
        try:
            location_text = f" in {user_location}" if user_location else ""
            prompt = f"""As a job search expert, provide specific advice for someone looking for jobs related to: {', '.join(user_keywords)}{location_text}.

Include:
1. 3-5 specific job titles to search for
2. Key skills to highlight on resume
3. Industry trends and growth areas
4. Salary expectations and negotiation tips
5. Best job search platforms for these roles

Keep the response practical and actionable, under 300 words."""
            
            response = await self._generate_response(prompt)
            
            return {
                "success": True,
                "recommendations": response,
                "keywords": user_keywords,
                "location": user_location,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating job recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_job_description(self, job_title: str, job_company: str, job_description: str = None) -> Dict[str, Any]:
        """Analyze a job posting and provide insights"""
        if not self.model:
            return {
                "success": False,
                "error": "Chatbot service not available"
            }
        
        try:
            description_text = f"\n\nJob Description: {job_description}" if job_description else ""
            prompt = f"""Analyze this job posting and provide insights:

Job Title: {job_title}
Company: {job_company}{description_text}

Provide:
1. Key skills and qualifications required
2. Career level (entry, mid, senior)
3. Growth opportunities
4. Red flags or concerns (if any)
5. Questions to ask in interview
6. How to tailor resume for this role

Be concise and actionable, under 250 words."""
            
            response = await self._generate_response(prompt)
            
            return {
                "success": True,
                "analysis": response,
                "job_title": job_title,
                "company": job_company,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing job description: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
gemini_service = GeminiChatbotService()