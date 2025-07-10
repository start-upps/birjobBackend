#!/usr/bin/env python3
"""
Fix device_token schema to allow NULL values
"""
import asyncio
import sys
sys.path.append('.')

from app.core.database import db_manager

async def fix_schema():
    """Modify device_tokens table to allow NULL device_token"""
    
    print("🔧 Fixing device_tokens schema to prevent crashes...")
    
    try:
        # Step 1: Remove NOT NULL constraint from device_token
        print("\n1. Removing NOT NULL constraint from device_token...")
        alter_query = """
            ALTER TABLE iosapp.device_tokens 
            ALTER COLUMN device_token DROP NOT NULL;
        """
        await db_manager.execute_command(alter_query)
        print("   ✅ NOT NULL constraint removed")
        
        # Step 2: Clean up any existing temp/fake tokens
        print("\n2. Cleaning up temporary/fake tokens...")
        cleanup_query = """
            UPDATE iosapp.device_tokens 
            SET device_token = NULL 
            WHERE device_token LIKE 'temp_%' 
               OR device_token LIKE 'placeholder_%'
               OR LENGTH(device_token) != 64
               OR device_token ~ '[^0-9a-fA-F]';
        """
        result = await db_manager.execute_command(cleanup_query)
        print(f"   ✅ Cleaned up fake tokens")
        
        # Step 3: Verify the change
        print("\n3. Verifying schema change...")
        verify_query = """
            SELECT 
                column_name,
                is_nullable,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'iosapp' 
            AND table_name = 'device_tokens'
            AND column_name = 'device_token';
        """
        result = await db_manager.execute_query(verify_query)
        
        if result and result[0]['is_nullable'] == 'YES':
            print("   ✅ device_token now allows NULL values")
        else:
            print("   ❌ Schema change failed")
            return False
        
        # Step 4: Show current state
        print("\n4. Current device tokens state:")
        status_query = """
            SELECT 
                COUNT(*) as total_devices,
                COUNT(device_token) as devices_with_tokens,
                COUNT(*) - COUNT(device_token) as devices_without_tokens
            FROM iosapp.device_tokens
            WHERE is_active = true;
        """
        stats = await db_manager.execute_query(status_query)
        
        if stats:
            stat = stats[0]
            print(f"   📊 Total active devices: {stat['total_devices']}")
            print(f"   📊 With real tokens: {stat['devices_with_tokens']}")
            print(f"   📊 Without tokens: {stat['devices_without_tokens']}")
        
        print("\n🎉 Schema fix completed successfully!")
        print("\n💡 Benefits:")
        print("   ✅ No more database crashes from NULL device_token")
        print("   ✅ No more fake/temporary tokens cluttering database")
        print("   ✅ Clean separation: profile creation vs token registration")
        print("   ✅ Real APNs tokens only when available from iOS app")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error fixing schema: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_schema())
    if success:
        print("\n🚀 Database is now crash-proof for device registration!")
    else:
        print("\n💥 Schema fix failed - manual intervention needed")