#!/usr/bin/env python3
"""
Debug notification sending with detailed logging
"""

import asyncio
import sys
import os
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.push_notifications import PushNotificationService
import json

async def debug_notification():
    """Debug notification sending process"""
    
    try:
        # Your real device data
        device_id = "45b750ec8ffa3c41b9adf6625a9177a6fb2e5670f84fac7cd72b682f86ce8f49"
        
        print("🔍 Debugging Notification Process")
        print("="*50)
        
        # 1. Check device in database
        device_query = """
            SELECT dt.device_token, dt.user_id, u.keywords, u.notifications_enabled 
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            print("❌ Device not found")
            return
        
        device_data = device_result[0]
        print(f"✅ Device found:")
        print(f"   Token: {device_data['device_token']}")
        print(f"   User ID: {device_data['user_id']}")
        print(f"   Keywords: {device_data['keywords']}")
        print(f"   Notifications enabled: {device_data['notifications_enabled']}")
        
        # 2. Test APNs client creation
        print(f"\n🔑 Testing APNs client...")
        push_service = PushNotificationService()
        
        if hasattr(push_service, '_apns_config') and push_service._apns_config:
            print("✅ APNs config exists")
            print(f"   Key ID: {push_service._apns_config.get('key_id')}")
            print(f"   Team ID: {push_service._apns_config.get('team_id')}")
            print(f"   Topic: {push_service._apns_config.get('topic')}")
            print(f"   Sandbox: {push_service._apns_config.get('use_sandbox')}")
        else:
            print("❌ No APNs config found")
            return
        
        # 3. Test APNs client creation
        apns_client = await push_service._get_apns_client()
        if apns_client:
            print("✅ APNs client created successfully")
        else:
            print("❌ Failed to create APNs client")
            return
        
        # 4. Test notification payload creation
        test_job = {
            "id": "debug-job",
            "title": "Machine Learning Engineer",
            "company": "Test Corp"
        }
        test_keywords = ["Machine Learning"]
        
        payload = push_service._create_job_match_payload(test_job, test_keywords, "debug-match")
        print(f"\n📨 Notification payload created:")
        print(json.dumps(payload, indent=2))
        
        # 5. Check device token format
        device_token = device_data['device_token']
        print(f"\n📱 Device token analysis:")
        print(f"   Length: {len(device_token)} characters")
        print(f"   Is hex: {all(c in '0123456789abcdefABCDEF' for c in device_token)}")
        print(f"   Starts with: {device_token[:10]}...")
        print(f"   Ends with: ...{device_token[-10:]}")
        
        # 6. Try to send notification with detailed error handling
        print(f"\n📤 Attempting to send notification...")
        
        try:
            success = await push_service.send_job_match_notification(
                device_token=device_token,
                device_id=device_id,
                job=test_job,
                matched_keywords=test_keywords,
                match_id="debug-match"
            )
            
            if success:
                print("🎉 SUCCESS! Notification sent!")
            else:
                print("❌ Notification failed")
                
        except Exception as e:
            print(f"❌ Exception during notification: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Notification Debug Mode")
    print("📝 This will show detailed logs to help identify issues")
    print("")
    
    # Run debug
    asyncio.run(debug_notification())