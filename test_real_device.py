#!/usr/bin/env python3
"""
Test real push notifications with actual device token from iOS app
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.job_notification_service import job_notification_service
import json

async def test_real_device():
    """Test with real device data from iOS app"""
    
    try:
        # Real device data from your iOS app logs
        device_id = "45b750ec8ffa3c41b9adf6625a9177a6fb2e5670f84fac7cd72b682f86ce8f49"
        user_id = "807c2ae3-19b9-43ea-9e29-36ae094aed56"
        
        print("📱 Testing Real iOS Device Push Notifications")
        print("="*60)
        print(f"Device ID: {device_id}")
        print(f"User ID: {user_id}")
        
        # 1. Check if device exists in database
        device_query = """
            SELECT dt.*, u.keywords, u.notifications_enabled 
            FROM iosapp.device_tokens dt
            JOIN iosapp.users u ON dt.user_id = u.id
            WHERE dt.device_id = $1 AND dt.is_active = true
        """
        
        device_result = await db_manager.execute_query(device_query, device_id)
        
        if device_result:
            device_data = device_result[0]
            print(f"✅ Device found in database")
            print(f"   User ID: {device_data['user_id']}")
            print(f"   Device Token: {device_data['device_token']}")
            print(f"   Keywords: {device_data['keywords']}")
            print(f"   Notifications Enabled: {device_data['notifications_enabled']}")
            
            # Check if this is a real device token (not placeholder)
            if len(device_data['device_token']) == 64 and device_data['device_token'] != device_id:
                print("✅ Real APNs device token detected!")
            else:
                print("⚠️  Device token appears to be placeholder")
                
        else:
            print(f"❌ Device not found in database: {device_id}")
            return False
        
        # 2. Update keywords if needed (use the keywords from your app)
        app_keywords = ["Machine Learning", "AI", "Data Science", "Analytics"]
        
        # Check if keywords match what your app set
        current_keywords = json.loads(device_data['keywords']) if device_data['keywords'] else []
        
        if current_keywords != app_keywords:
            print(f"🔧 Updating keywords to match iOS app...")
            
            update_query = """
                UPDATE iosapp.users 
                SET keywords = $1, notifications_enabled = true, updated_at = NOW()
                WHERE id = $2
                RETURNING id
            """
            
            result = await db_manager.execute_query(update_query, json.dumps(app_keywords), device_data['user_id'])
            
            if result:
                print(f"✅ Keywords updated: {app_keywords}")
            else:
                print("❌ Failed to update keywords")
                return False
        else:
            print(f"✅ Keywords already match: {current_keywords}")
        
        # 3. Run real job notification processing
        print(f"\n🔄 Running job notification processing...")
        
        stats = await job_notification_service.process_job_notifications(
            source_filter=None,
            limit=50,
            dry_run=False  # REAL notifications
        )
        
        print(f"\n📊 Notification Results:")
        print(f"   Processed Jobs: {stats.get('processed_jobs', 0)}")
        print(f"   Matched Users: {stats.get('matched_users', 0)}")
        print(f"   Notifications Sent: {stats.get('notifications_sent', 0)}")
        print(f"   Errors: {stats.get('errors', 0)}")
        
        # 4. Check recent notification history
        print(f"\n📱 Checking notification history...")
        
        history_query = """
            SELECT pn.*, jnh.job_title, jnh.job_company 
            FROM iosapp.push_notifications pn
            LEFT JOIN iosapp.job_notification_history jnh ON pn.job_notification_id = jnh.id
            WHERE pn.user_id = $1
            ORDER BY pn.created_at DESC
            LIMIT 5
        """
        
        try:
            history_result = await db_manager.execute_query(history_query, device_data['user_id'])
            
            if history_result:
                print(f"📱 Recent notifications ({len(history_result)}):")
                for notif in history_result:
                    print(f"   - {notif['notification_type']}: {notif['status']} at {notif['created_at']}")
                    if notif.get('job_title'):
                        print(f"     Job: {notif['job_title']} at {notif['job_company']}")
            else:
                print("📱 No notification history found")
        except Exception as e:
            print(f"⚠️  Could not fetch history: {e}")
        
        # 5. Results summary
        if stats.get('notifications_sent', 0) > 0:
            print(f"\n🎉 SUCCESS! {stats['notifications_sent']} real notifications sent!")
            print("📱 Check your iPhone for the push notifications!")
            return True
        else:
            print(f"\n🤔 No new notifications sent. Possible reasons:")
            print("   - No recent jobs match your keywords (ML, AI, Data Science, Analytics)")
            print("   - You've already been notified about all matching jobs")
            print("   - Job scraper hasn't run recently with new data")
            
            # Show some recent jobs to help debug
            jobs_query = """
                SELECT title, company, source, created_at 
                FROM iosapp.jobs 
                ORDER BY created_at DESC 
                LIMIT 5
            """
            jobs_result = await db_manager.execute_query(jobs_query)
            
            if jobs_result:
                print(f"\n📋 Recent jobs in database:")
                for job in jobs_result:
                    print(f"   - {job['title']} at {job['company']} ({job['source']}) - {job['created_at']}")
            
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing with Real iOS Device Token")
    print("🔑 Using local AuthKey_S64YC3U4ZX.p8 file")
    print("📱 Device from iOS app logs")
    print("")
    
    # Run the test
    result = asyncio.run(test_real_device())
    
    print("="*60)
    if result:
        print("✅ Real device test PASSED! Notifications sent to your iPhone!")
    else:
        print("❌ No new notifications sent - but system is working")
        print("💡 Try adding some test jobs with ML/AI keywords to trigger notifications")