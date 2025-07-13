from fastapi import APIRouter

from app.api.v1.endpoints import health, jobs_minimal
from app.api.v1.endpoints import device_registration, minimal_notifications, device_notifications, device_management, device_chatbot

api_router = APIRouter()

# Active endpoints
api_router.include_router(jobs_minimal.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(device_registration.router, prefix="/device", tags=["device-registration"])
api_router.include_router(minimal_notifications.router, prefix="/minimal-notifications", tags=["minimal-notifications"])
api_router.include_router(device_notifications.router, prefix="/notifications", tags=["device-notifications"])
api_router.include_router(device_management.router, prefix="/devices", tags=["device-management"])
api_router.include_router(device_chatbot.router, prefix="/chatbot", tags=["device-chatbot"])
