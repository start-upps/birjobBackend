#!/usr/bin/env python3
"""
Send a single test notification to your real iOS device
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.push_notifications import PushNotificationService
import json

async def send_single_test_notification():
    """Send one test notification to your real device"""
    
    try:
        # Your real device data from iOS app logs
        device_id = "45b750ec8ffa3c41b9adf6625a9177a6fb2e5670f84fac7cd72b682f86ce8f49"
        user_id = "807c2ae3-19b9-43ea-9e29-36ae094aed56"
        
        print("📱 Sending Single Test Notification")
        print("="*50)
        print(f"Device ID: {device_id}")
        print(f"User ID: {user_id}")
        
        # 1. Get device token from database
        device_query = """
            SELECT device_token FROM iosapp.device_tokens 
            WHERE device_id = $1 AND is_active = true
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            print("❌ Device not found in database")
            return False
        
        device_token = device_result[0]['device_token']
        print(f"✅ Device token: {device_token[:20]}...")
        
        # 2. Create push notification service
        push_service = PushNotificationService()
        
        # 3. Create a test job
        test_job = {
            "id": "test-ml-job-001",
            "title": "Senior Machine Learning Engineer",
            "company": "AI Innovations Corp",
            "apply_link": "https://example.com/apply",
            "source": "test"
        }
        
        test_keywords = ["Machine Learning", "AI"]
        match_id = "test-match-001"
        
        print(f"\n📨 Sending test notification...")
        print(f"   Job: {test_job['title']}")
        print(f"   Company: {test_job['company']}")
        print(f"   Keywords: {test_keywords}")
        
        # 4. Send the notification
        success = await push_service.send_job_match_notification(
            device_token=device_token,
            device_id=device_id,
            job=test_job,
            matched_keywords=test_keywords,
            match_id=match_id
        )
        
        if success:
            print("\n🎉 SUCCESS! Test notification sent!")
            print("📱 Check your iPhone for the push notification!")
            return True
        else:
            print("\n❌ Failed to send test notification")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Single Notification Test")
    print("🔑 Using real device token from iOS app")
    print("📱 Target: Your iPhone with Machine Learning keywords")
    print("")
    
    # Run the test
    result = asyncio.run(send_single_test_notification())
    
    print("="*50)
    if result:
        print("✅ Test notification sent successfully!")
        print("📱 You should see a push notification on your iPhone!")
    else:
        print("❌ Test notification failed")
        print("🔧 Check APNs configuration and device token")