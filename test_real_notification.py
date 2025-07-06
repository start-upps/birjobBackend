#!/usr/bin/env python3
"""
Test real push notifications with proper device token handling
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.job_notification_service import job_notification_service
from app.services.push_notifications import PushNotificationService
import json

async def test_real_notification():
    """Test real push notification with your device"""
    
    try:
        # Your actual device_id from the database
        device_id = "518239b48c18c6fdc0f2becaa860e6d06b521298c6fd39e1b11bc8de77fb4e36"
        
        print(f"🔍 Testing notifications for device: {device_id}")
        print("="*70)
        
        # 1. Check your device registration
        device_query = """
            SELECT dt.*, u.keywords, u.notifications_enabled 
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if not device_result:
            print("❌ Device not found in database")
            return
        
        device_data = device_result[0]
        print(f"✅ Device found:")
        print(f"   User ID: {device_data['user_id']}")
        print(f"   Device Token: {device_data['device_token']}")
        print(f"   Keywords: {device_data['keywords']}")
        print(f"   Notifications Enabled: {device_data['notifications_enabled']}")
        
        # 2. Update keywords if needed
        if not device_data['keywords'] or not device_data['notifications_enabled']:
            print("🔧 Setting up keywords and enabling notifications...")
            
            keywords = ["iOS Developer", "Swift", "Mobile App", "iPhone", "React Native", "Apple"]
            
            update_query = """
                UPDATE iosapp.users 
                SET keywords = $1, notifications_enabled = true, updated_at = NOW()
                WHERE id = $2
                RETURNING id
            """
            
            result = await db_manager.execute_query(update_query, json.dumps(keywords), device_data['user_id'])
            
            if result:
                print(f"✅ Keywords updated: {keywords}")
            else:
                print("❌ Failed to update keywords")
                return
        
        # 3. Test APNs configuration
        push_service = PushNotificationService()
        print(f"\n🔑 APNs Configuration Status:")
        
        if hasattr(push_service, '_apns_config') and push_service._apns_config:
            print("✅ APNs config is available")
            
            # Get APNs client to test
            apns_client = await push_service._get_apns_client()
            if apns_client:
                print("✅ APNs client created successfully")
            else:
                print("❌ Failed to create APNs client")
        else:
            print("❌ No APNs configuration found")
        
        # 4. Create a test notification
        print(f"\n📱 Sending test notification...")
        
        # Create a fake job for testing
        test_job = {
            "id": "test-job-123",
            "title": "Senior iOS Developer",
            "company": "Apple Inc.",
            "apply_link": "https://jobs.apple.com/test",
            "source": "test"
        }
        
        test_keywords = ["iOS Developer", "Swift"]
        
        # Try to send notification
        success = await push_service.send_job_match_notification(
            device_token=device_data['device_token'],
            device_id=device_id,
            job=test_job,
            matched_keywords=test_keywords,
            match_id="test-match-123"
        )
        
        if success:
            print("🎉 SUCCESS! Test notification sent successfully!")
            print("📱 Check your phone for the notification")
        else:
            print("❌ Failed to send test notification")
        
        # 5. Check notification history
        print(f"\n📊 Checking notification history...")
        
        history_query = """
            SELECT pn.*, jnh.job_title, jnh.job_company 
            FROM iosapp.push_notifications pn
            LEFT JOIN iosapp.job_notification_history jnh ON pn.job_notification_id = jnh.id
            WHERE pn.device_id = $1
            ORDER BY pn.created_at DESC
            LIMIT 5
        """
        
        history_result = await db_manager.execute_query(history_query, device_data['device_id'])
        
        if history_result:
            print(f"📱 Recent notifications ({len(history_result)}):")
            for notif in history_result:
                print(f"   - {notif['notification_type']}: {notif['status']} at {notif['created_at']}")
                if notif.get('job_title'):
                    print(f"     Job: {notif['job_title']} at {notif['job_company']}")
        else:
            print("📱 No notification history found")
        
        # 6. Important notes
        print(f"\n📝 Important Notes:")
        print(f"   • Your current device_token appears to be a placeholder")
        print(f"   • For real APNs notifications, you need a valid device token from iOS")
        print(f"   • The device token should be obtained from your iOS app")
        print(f"   • Current token: {device_data['device_token'][:20]}...")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Real Push Notifications")
    print("="*70)
    
    # Run the async function
    result = asyncio.run(test_real_notification())
    
    print("="*70)
    if result:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed - check the logs above")