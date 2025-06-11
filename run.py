#!/usr/bin/env python3
"""
Simple entry point for Render deployment
"""
import os

if __name__ == "__main__":
    # Get port from environment
    port = int(os.environ.get('PORT', 8000))
    
    # Import and run
    from application import app
    import uvicorn
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )