#!/usr/bin/env python3
"""
Production startup script for iOS Job App Backend
"""

import os
import uvicorn
from main import app

if __name__ == "__main__":
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Start the application
    uvicorn.run(
        app,
        host=host,
        port=port,
        access_log=True,
        log_level="info"
    )