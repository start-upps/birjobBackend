#!/usr/bin/env python3
"""
Main entry point for the iOS Backend API
This handles startup issues and provides better error messages
"""
import sys
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(__file__))
        
        logger.info("🚀 Starting iOS Backend API...")
        logger.info(f"Python path: {sys.path[:3]}...")
        logger.info(f"Current directory: {os.getcwd()}")
        
        # Import the FastAPI app
        from app import app
        
        logger.info("✅ FastAPI app imported successfully")
        
        # Get port from environment
        port = int(os.getenv('PORT', 8000))
        
        # Import uvicorn and run
        import uvicorn
        
        logger.info(f"🌐 Starting server on 0.0.0.0:{port}")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Available modules in current directory:")
        try:
            import os
            for item in os.listdir('.'):
                if not item.startswith('.'):
                    logger.error(f"  - {item}")
        except:
            pass
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()