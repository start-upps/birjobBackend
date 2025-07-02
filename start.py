#!/usr/bin/env python3
"""
Production startup script for iOS Job App Backend
Optimized for Render.com deployment
"""

import os
import sys
import uvicorn
from application import app

def main():
    """Start the FastAPI application with production settings"""
    
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    
    # Get host (0.0.0.0 for containers)
    host = os.getenv("HOST", "0.0.0.0")
    
    # Production settings
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=1,  # Single worker for now, can be increased based on needs
        access_log=True,
        log_level="info",
        loop="auto",
        http="auto"
    )

if __name__ == "__main__":
    main()