#!/usr/bin/env python3
"""
Production notification test - tests the uploaded APNs key file
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.job_notification_service import job_notification_service
import json

async def production_notification_test():
    """Test real push notifications in production environment"""
    
    try:
        # Your actual device_id
        device_id = "518239b48c18c6fdc0f2becaa860e6d06b521298c6fd39e1b11bc8de77fb4e36"
        
        print("🚀 Production Push Notification Test")
        print("="*60)
        print(f"Testing for device: {device_id}")
        
        # 1. Check if the production key file exists
        production_key_path = "/etc/secrets/AuthKey_S64YC3U4ZX.p8"
        if os.path.exists(production_key_path):
            print(f"✅ Production key file found: {production_key_path}")
            
            # Read and validate the key
            try:
                with open(production_key_path, 'r') as f:
                    key_content = f.read()
                    if key_content.startswith('-----BEGIN PRIVATE KEY-----'):
                        print("✅ Key file is in proper PEM format")
                        print(f"✅ Key file size: {len(key_content)} bytes")
                    else:
                        print("❌ Key file is not in PEM format")
                        return False
            except Exception as e:
                print(f"❌ Cannot read key file: {e}")
                return False
        else:
            print(f"❌ Production key file not found: {production_key_path}")
            print("   This test should be run in the production environment")
            return False
        
        # 2. Setup user keywords
        keywords = ["iOS Developer", "Swift", "Mobile App", "iPhone", "React Native", "Apple"]
        
        user_setup_query = """
            UPDATE iosapp.users 
            SET keywords = $1, notifications_enabled = true, updated_at = NOW()
            WHERE id = (
                SELECT u.id FROM iosapp.users u
                JOIN iosapp.device_tokens dt ON u.id = dt.user_id
                WHERE dt.device_id = $2 AND dt.is_active = true
            )
            RETURNING id
        """
        
        result = await db_manager.execute_query(user_setup_query, json.dumps(keywords), device_id)
        
        if result:
            print(f"✅ Keywords set for user: {result[0]['id']}")
        else:
            print("❌ Failed to find or update user")
            return False
        
        # 3. Run real job notification processing
        print("🔄 Processing real job notifications...")
        
        stats = await job_notification_service.process_job_notifications(
            source_filter=None,
            limit=20,
            dry_run=False  # REAL notifications
        )
        
        print(f"\n📊 Results:")
        print(f"   Processed Jobs: {stats.get('processed_jobs', 0)}")
        print(f"   Matched Users: {stats.get('matched_users', 0)}")
        print(f"   Notifications Sent: {stats.get('notifications_sent', 0)}")
        print(f"   Errors: {stats.get('errors', 0)}")
        
        if stats.get('notifications_sent', 0) > 0:
            print("\n🎉 SUCCESS! Real notifications sent with production key!")
            print("📱 Check your iPhone for the notifications!")
            return True
        else:
            print("\n🤔 No notifications sent. Possible reasons:")
            print("   - No new job matches found")
            print("   - All matching jobs already notified")
            print("   - APNs delivery issues")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔑 This script tests production APNs with the uploaded key file")
    print("📁 Expected key location: /etc/secrets/AuthKey_S64YC3U4ZX.p8")
    print("📱 Expected Key ID: S64YC3U4ZX")
    print("")
    
    # Run the test
    result = asyncio.run(production_notification_test())
    
    print("="*60)
    if result:
        print("✅ Production notification test PASSED!")
    else:
        print("❌ Production notification test FAILED!")
        print("\n📝 Next steps:")
        print("   1. Ensure key file is uploaded to /etc/secrets/AuthKey_S64YC3U4ZX.p8")
        print("   2. Update APNS_KEY_ID environment variable to S64YC3U4ZX")
        print("   3. Deploy and run this script in production environment")