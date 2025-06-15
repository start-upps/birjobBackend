from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
import logging
import os

from app.core.config import settings
from app.core.database import init_db
from app.core.redis_client import init_redis
from app.api.v1.router import api_router
from app.core.monitoring import setup_monitoring
from app.core.security import setup_security_headers
from app.services.match_engine import job_scheduler

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
    
    # Start the job matching scheduler in the background
    try:
        logger.info("Starting job matching scheduler...")
        asyncio.create_task(job_scheduler.start())
        logger.info("Job matching scheduler task created successfully")
    except Exception as e:
        logger.error(f"Failed to start job matching scheduler: {e}")
        # Don't fail the entire app if scheduler fails to start
    
    yield
    
    # Shutdown
    logger.info("Shutting down iOS Backend API...")

app = FastAPI(
    title="iOS Native App Backend",
    description="Backend API for iOS job matching app with push notifications",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup monitoring and security
setup_monitoring(app)
setup_security_headers(app)

# Mount static files
app.mount("/1", StaticFiles(directory="1"), name="icons")

# Include routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Serve the main website"""
    return FileResponse('website/index.html')

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon at standard location"""
    import os
    favicon_path = os.path.join("1", "web", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path, media_type="image/x-icon")
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/manifest.json")
async def manifest():
    """Serve web app manifest"""
    return FileResponse('website/manifest.json', media_type="application/json")

@app.get("/api")
async def api_root():
    return {"message": "iOS Native App Backend API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)