from fastapi import APIRouter

from app.api.v1.endpoints import devices, keywords, matches, health

api_router = APIRouter()

api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])  
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(health.router, prefix="/health", tags=["health"])