"""
Main FastAPI application for iOS Job App Backend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.services.notification_scheduler import notification_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)"""
    # Startup
    logger.info("Starting iOS Job App Backend...")
    await notification_scheduler.start_scheduler()
    logger.info("Notification scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down iOS Job App Backend...")
    await notification_scheduler.stop_scheduler()
    logger.info("Notification scheduler stopped")

# Create FastAPI app
app = FastAPI(
    title="iOS Job App Backend",
    description="Backend API for iOS Job Application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    from fastapi.responses import Response
    # Return empty response for favicon requests
    return Response(content="", media_type="image/x-icon", status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)