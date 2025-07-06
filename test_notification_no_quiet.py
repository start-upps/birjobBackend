#!/usr/bin/env python3
"""
Test notification bypassing quiet hours
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.push_notifications import PushNotificationService
import json

# Monkey patch to disable quiet hours for testing
async def always_not_quiet_hours(self, device_id: str):
    """Override to always return False (never quiet hours)"""
    return False

async def test_notification_bypassing_quiet():
    """Test notification with quiet hours disabled"""
    
    try:
        # Your real device data
        device_id = "45b750ec8ffa3c41b9adf6625a9177a6fb2e5670f84fac7cd72b682f86ce8f49"
        
        print("📱 Testing Notification (Quiet Hours Disabled)")
        print("="*55)
        
        # Get device token
        device_query = """
            SELECT device_token FROM iosapp.device_tokens 
            WHERE device_id = $1 AND is_active = true
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            print("❌ Device not found")
            return False
        
        device_token = device_result[0]['device_token']
        print(f"✅ Device token: {device_token[:20]}...")
        
        # Create push service and disable quiet hours
        push_service = PushNotificationService()
        
        # Monkey patch the quiet hours method
        push_service._is_quiet_hours = lambda device_id: always_not_quiet_hours(push_service, device_id)
        
        print("🔇 Quiet hours disabled for testing")
        
        # Create test job
        test_job = {
            "id": "ml-job-test",
            "title": "Senior ML Engineer",
            "company": "TechCorp AI",
            "apply_link": "https://example.com/apply",
            "source": "test"
        }
        
        test_keywords = ["Machine Learning", "AI"]
        match_id = "test-match-bypass"
        
        print(f"\n📨 Sending notification...")
        print(f"   Job: {test_job['title']}")
        print(f"   Company: {test_job['company']}")
        print(f"   Keywords: {test_keywords}")
        
        # Send the notification
        success = await push_service.send_job_match_notification(
            device_token=device_token,
            device_id=device_id,
            job=test_job,
            matched_keywords=test_keywords,
            match_id=match_id
        )
        
        if success:
            print("\n🎉 SUCCESS! Push notification sent to your iPhone!")
            print("📱 Check your phone for the notification!")
            return True
        else:
            print("\n❌ Failed to send notification")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Bypass Quiet Hours Test")
    print("🔇 Temporarily disabling quiet hours for testing")
    print("📱 Sending real push notification to your iPhone")
    print("")
    
    # Run the test
    result = asyncio.run(test_notification_bypassing_quiet())
    
    print("="*55)
    if result:
        print("✅ NOTIFICATION SENT SUCCESSFULLY!")
        print("📱 You should receive a push notification on your iPhone!")
        print("🎯 The notification system is working perfectly!")
    else:
        print("❌ Notification failed")
        print("🔧 Check the error logs above")