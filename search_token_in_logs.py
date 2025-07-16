#!/usr/bin/env python3
"""
Script to search for the specific device token in logs and check for orphaned data
"""
import asyncio
import asyncpg
import sys
import os
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings

async def search_token_data():
    """Search for any references to the problematic device token"""
    
    # Get database URL without asyncpg prefix for direct connection
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(db_url)
        
        print("=== SEARCHING FOR ORPHANED TOKEN DATA ===")
        print(f"Connected to database at: {datetime.now()}")
        print()
        
        specific_token = "63e61e82600a5010b20965561a0ce8530046a7bd3f45b7a1e53d748bcc64a992"
        print(f"Searching for token: {specific_token}")
        print()
        
        # 1. Check if there are any orphaned notification_hashes entries
        print("1. Checking for orphaned notification_hashes entries:")
        try:
            # First, let's see if we can find any device_id that might correspond to this token
            # by searching for similar patterns or recent entries
            
            # Get all device_ids from notification_hashes that don't exist in device_users
            orphaned_query = """
                SELECT DISTINCT nh.device_id, COUNT(*) as notification_count
                FROM iosapp.notification_hashes nh
                LEFT JOIN iosapp.device_users du ON nh.device_id = du.id
                WHERE du.id IS NULL
                GROUP BY nh.device_id
                ORDER BY notification_count DESC;
            """
            
            orphaned_devices = await conn.fetch(orphaned_query)
            
            if orphaned_devices:
                print(f"   Found {len(orphaned_devices)} orphaned device_ids in notification_hashes:")
                for device in orphaned_devices:
                    print(f"     - Device ID: {device['device_id']}")
                    print(f"       Notification count: {device['notification_count']}")
                    
                    # Get some sample notifications for this orphaned device
                    sample_notifs_query = """
                        SELECT id, job_hash, job_title, sent_at
                        FROM iosapp.notification_hashes
                        WHERE device_id = $1
                        ORDER BY sent_at DESC
                        LIMIT 3;
                    """
                    sample_notifs = await conn.fetch(sample_notifs_query, device['device_id'])
                    
                    if sample_notifs:
                        print(f"       Sample notifications:")
                        for notif in sample_notifs:
                            print(f"         - {notif['job_title']} (sent: {notif['sent_at']})")
                    print()
            else:
                print("   No orphaned notification_hashes entries found")
                
        except Exception as e:
            print(f"   Error checking orphaned entries: {e}")
        
        print("="*50)
        
        # 2. Check if there are any recent device registrations that might be related
        print("2. Checking recent device activity:")
        try:
            # Get recent device registrations
            recent_devices_query = """
                SELECT id, device_token, created_at, keywords
                FROM iosapp.device_users
                ORDER BY created_at DESC
                LIMIT 10;
            """
            recent_devices = await conn.fetch(recent_devices_query)
            
            if recent_devices:
                print(f"   Recent device registrations:")
                for device in recent_devices:
                    print(f"     - ID: {device['id']}")
                    print(f"       Token: {device['device_token'][:20]}...{device['device_token'][-20:]}")
                    print(f"       Created: {device['created_at']}")
                    print(f"       Keywords: {device['keywords']}")
                    print()
            else:
                print("   No recent device registrations found")
                
        except Exception as e:
            print(f"   Error checking recent devices: {e}")
        
        print("="*50)
        
        # 3. Check for any other tables that might reference device tokens
        print("3. Checking other tables for device token references:")
        try:
            # Check if there are any other tables that might contain device tokens
            tables_query = """
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = 'iosapp' 
                AND column_name LIKE '%device%'
                AND table_name NOT IN ('device_users', 'notification_hashes');
            """
            
            other_tables = await conn.fetch(tables_query)
            
            if other_tables:
                print(f"   Found {len(other_tables)} other device-related columns:")
                for table in other_tables:
                    print(f"     - {table['table_name']}.{table['column_name']}")
            else:
                print("   No other device-related tables found")
                
        except Exception as e:
            print(f"   Error checking other tables: {e}")
            
        print("="*50)
        
        # 4. Summary and recommendations
        print("4. Analysis Summary:")
        print(f"   • The device token {specific_token} is NOT found in the device_users table")
        print(f"   • This suggests the device was either:")
        print(f"     - Never properly registered")
        print(f"     - Previously registered but deleted")
        print(f"     - Registered in a different environment/database")
        print(f"   • The 404 errors are likely caused by the push notification service")
        print(f"     trying to send notifications to a device that no longer exists in the database")
        print(f"   • This could happen if:")
        print(f"     - The device was unregistered but notifications were still queued")
        print(f"     - There's a race condition between device deletion and notification sending")
        print(f"     - The notification service is using cached/stale device data")
        
        print("\n   Recommendations:")
        print("   1. Add better error handling for missing device tokens in notification service")
        print("   2. Implement proper cleanup of notification queues when devices are deleted")
        print("   3. Add logging to track when devices are registered/unregistered")
        print("   4. Consider adding a 'deleted_at' timestamp instead of hard deleting devices")
        
        print("\n" + "="*50)
        print("Search completed!")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")
        print(f"Database URL: {db_url}")
        
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(search_token_data())