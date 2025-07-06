"""
Main FastAPI application for iOS Job App Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.notification_scheduler import notification_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="iOS Job App Backend",
    description="Backend API for iOS Job Application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Application startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting iOS Job App Backend...")
    
    # Start notification scheduler
    await notification_scheduler.start_scheduler()
    logger.info("Notification scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    logger.info("Shutting down iOS Job App Backend...")
    
    # Stop notification scheduler
    await notification_scheduler.stop_scheduler()
    logger.info("Notification scheduler stopped")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "iOS Job App Backend",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Service is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)