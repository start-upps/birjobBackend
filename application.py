from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
import os

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.api.v1.router import api_router
# from app.core.monitoring import setup_monitoring  # Disabled - module doesn't exist
# from app.core.security import setup_security_headers  # Disabled - module doesn't exist
# from app.services.match_engine import job_scheduler  # Disabled - complex dependencies

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting iOS Backend API...")
    
    # Initialize database and Redis
    await init_db()
    await init_redis()
    logger.info("Database and Redis initialized")
    
    # Check if we're in production and ensure migrations are up to date
    if os.getenv("RENDER"):
        logger.info("Production environment detected - migration check skipped (handled by start command)")
    
    # Job matching scheduler disabled - complex dependencies
    logger.info("Job matching scheduler disabled in simplified version")
    
    yield
    
    # Shutdown
    logger.info("Shutting down iOS Backend API...")

app = FastAPI(
    title="iOS Native App Backend",
    description="Backend API for iOS job matching app with push notifications",
    version="1.0.0",
    lifespan=lifespan
)

# Note: HTTPS redirect not needed on Render - handled by infrastructure

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring and security - disabled in simplified version
# setup_monitoring(app)  # Disabled - module doesn't exist
# setup_security_headers(app)  # Disabled - module doesn't exist

# Mount static files
# app.mount("/1", StaticFiles(directory="1"), name="icons")  # Removed as directory doesn't exist

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "iOS Native App Backend API", "version": "1.0.0"}

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon at standard location"""
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/api")
async def api_root():
    return {"message": "iOS Native App Backend API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)