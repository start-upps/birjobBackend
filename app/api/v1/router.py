from fastapi import APIRouter

from app.api.v1.endpoints import devices, health, jobs, users, analytics, chatbot, notifications, debug
# from app.api.v1.endpoints import keywords  # Disabled - requires KeywordSubscription model

api_router = APIRouter()

api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
# api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])  # Disabled - requires KeywordSubscription model
# api_router.include_router(matches.router, prefix="/matches", tags=["matches"])  # Disabled - complex dependencies
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["chatbot"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(debug.router, prefix="/debug", tags=["debug"])