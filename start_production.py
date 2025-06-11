#!/usr/bin/env python3
"""
Production startup script for Render
This bypasses Alembic since we already have the schema
"""
import os
import sys
import subprocess
import logging

def main():
    """Start the production server"""
    print("🚀 Starting iOS Backend API in production...")
    
    # Check if we're on Render
    if os.getenv('RENDER'):
        print("✅ Running on Render.com")
    
    # Get the port from environment
    port = os.getenv('PORT', '8000')
    print(f"📡 Starting server on port {port}")
    
    # Start uvicorn
    cmd = [
        'uvicorn', 
        'app:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--workers', '1'  # Single worker for Render's memory limits
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    try:
        # Start the server
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()