#!/usr/bin/env python3
"""
Direct script to set up keywords and trigger real notifications for a specific device
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.database import db_manager
from app.services.job_notification_service import job_notification_service
import json

async def setup_and_notify(device_id):
    """Setup keywords and trigger real notifications for device"""
    
    try:
        print(f"Setting up notifications for device: {device_id}")
        
        # 1. Setup keywords for the user
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
            print(f"✅ Keywords set: {keywords}")
            print(f"✅ Notifications enabled for user: {result[0]['id']}")
        else:
            print("❌ Failed to find or update user")
            return
        
        # 2. Run real job notification processing
        print("\n🔄 Running real job notification processing...")
        
        stats = await job_notification_service.process_job_notifications(
            source_filter=None,
            limit=100,
            dry_run=False  # REAL notifications
        )
        
        print(f"\n📊 Results:")
        print(f"   Processed Jobs: {stats.get('processed_jobs', 0)}")
        print(f"   Matched Users: {stats.get('matched_users', 0)}")
        print(f"   Notifications Sent: {stats.get('notifications_sent', 0)}")
        print(f"   Errors: {stats.get('errors', 0)}")
        
        if stats.get('notifications_sent', 0) > 0:
            print("\n🎉 SUCCESS! Real job notifications have been sent to your phone!")
        else:
            print("\n🤔 No new job matches found. This could mean:")
            print("   - No recent jobs match your keywords")
            print("   - You've already been notified about all matching jobs")
            print("   - The job scraper hasn't run recently")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    device_id = "518239b48c18c6fdc0f2becaa860e6d06b521298c6fd39e1b11bc8de77fb4e36"
    
    print("🚀 Starting real notification setup and delivery...")
    print("="*60)
    
    # Run the async function
    asyncio.run(setup_and_notify(device_id))
    
    print("="*60)
    print("✅ Script completed!")