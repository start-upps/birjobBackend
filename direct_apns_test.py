#!/usr/bin/env python3
"""
Direct APNs test - bypassing database UUID issues
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.services.push_notifications import PushNotificationService
import json

async def direct_apns_test():
    """Send notification directly through APNs"""
    
    try:
        # Your real device token (64 character hex string)
        device_token = "45b750ec8ffa3c41b9adf6625a9177a6fb2e5670f84fac7cd72b682f86ce8f49"
        
        print("📱 Direct APNs Push Notification Test")
        print("="*50)
        print(f"Device Token: {device_token[:20]}...")
        
        # Create push service
        push_service = PushNotificationService()
        
        # Test APNs client
        apns_client = await push_service._get_apns_client()
        if not apns_client:
            print("❌ Failed to create APNs client")
            return False
        
        print("✅ APNs client created successfully")
        
        # Create notification payload
        payload = {
            "aps": {
                "alert": {
                    "title": "🎯 Job Match Found!",
                    "subtitle": "Machine Learning Engineer",
                    "body": "Perfect match for your AI/ML keywords!"
                },
                "badge": 1,
                "sound": "default",
                "category": "JOB_MATCH"
            },
            "custom_data": {
                "type": "job_match",
                "job_id": "direct-test-001",
                "keywords": ["Machine Learning", "AI"],
                "deep_link": "birjob://job/direct-test-001"
            }
        }
        
        print(f"\n📨 Sending notification payload:")
        print(json.dumps(payload, indent=2))
        
        # Import NotificationRequest and PushType
        try:
            from aioapns import NotificationRequest, PushType
            
            # Create notification request
            request = NotificationRequest(
                device_token=device_token,
                message=payload,
                push_type=PushType.ALERT
            )
            
            print(f"\n📤 Sending push notification...")
            
            # Send the notification
            response = await apns_client.send_notification(request)
            
            print(f"\n📋 APNs Response:")
            print(f"   Success: {response.is_successful}")
            print(f"   Status: {response.status}")
            
            if hasattr(response, 'description') and response.description:
                print(f"   Description: {response.description}")
            
            if response.is_successful:
                print(f"\n🎉 SUCCESS! Push notification sent to your iPhone!")
                print(f"📱 Check your phone in Baku for the notification!")
                return True
            else:
                print(f"\n❌ APNs returned failure")
                print(f"   Status: {response.status}")
                if hasattr(response, 'description'):
                    print(f"   Description: {response.description}")
                return False
                
        except ImportError:
            print("❌ aioapns library not available")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Direct APNs Test")
    print("🏢 Bypassing database - direct APNs communication")
    print("🇦🇿 Sending to device in Baku, Azerbaijan")
    print("📱 Using real device token from iOS app")
    print("")
    
    # Run the test
    result = asyncio.run(direct_apns_test())
    
    print("="*50)
    if result:
        print("✅ DIRECT APNS TEST SUCCESSFUL!")
        print("📱 You should receive a push notification!")
        print("🎯 Your notification system is working!")
    else:
        print("❌ Direct APNs test failed")
        print("🔧 Check APNs configuration or device token")