#!/usr/bin/env python3
"""
Test APNs configuration in production environment
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.services.push_notifications import PushNotificationService
from app.core.config import settings

async def test_apns_production():
    """Test APNs configuration"""
    
    print("🔑 Testing APNs Configuration")
    print("="*50)
    
    # Create push service
    push_service = PushNotificationService()
    
    # Check environment variables
    print(f"APNS_PRIVATE_KEY present: {bool(settings.APNS_PRIVATE_KEY)}")
    print(f"APNS_KEY_ID: {settings.APNS_KEY_ID}")
    print(f"APNS_TEAM_ID: {settings.APNS_TEAM_ID}")
    print(f"APNS_BUNDLE_ID: {settings.APNS_BUNDLE_ID}")
    print(f"APNS_SANDBOX: {settings.APNS_SANDBOX}")
    
    if settings.APNS_PRIVATE_KEY:
        key_preview = settings.APNS_PRIVATE_KEY[:50].replace('\n', '\\n')
        print(f"Key preview: {key_preview}...")
        
        # Check for quotes
        if settings.APNS_PRIVATE_KEY.startswith('"'):
            print("⚠️  WARNING: Key starts with quote")
        if settings.APNS_PRIVATE_KEY.endswith('"'):
            print("⚠️  WARNING: Key ends with quote")
            
        # Check PEM format
        if settings.APNS_PRIVATE_KEY.strip().startswith('-----BEGIN PRIVATE KEY-----'):
            print("✅ Key appears to be in PEM format")
        else:
            print("❌ Key is NOT in PEM format")
    
    # Test APNs client creation
    print(f"\n🔧 Testing APNs Client Creation...")
    
    try:
        apns_client = await push_service._get_apns_client()
        if apns_client:
            print("✅ APNs client created successfully!")
            print("🎉 Your APNs configuration is working!")
            return True
        else:
            print("❌ Failed to create APNs client")
            return False
    except Exception as e:
        print(f"❌ Error creating APNs client: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_apns_production())
    
    print("="*50)
    if result:
        print("✅ APNs is ready for production notifications!")
    else:
        print("❌ APNs configuration needs fixing")