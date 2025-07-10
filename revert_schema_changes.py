#!/usr/bin/env python3
"""
Revert device_token schema changes to maintain data integrity
"""
import asyncio
import sys
sys.path.append('.')

from app.core.database import db_manager

async def revert_schema():
    """Restore NOT NULL constraint on device_token to prevent wrong data entry"""
    
    print("🔧 Reverting schema changes to maintain data integrity...")
    
    try:
        # Step 1: Clean up any NULL device tokens first
        print("\n1. Cleaning up NULL device tokens...")
        cleanup_query = """
            DELETE FROM iosapp.device_tokens 
            WHERE device_token IS NULL;
        """
        result = await db_manager.execute_command(cleanup_query)
        print(f"   ✅ Removed NULL device tokens")
        
        # Step 2: Clean up invalid device tokens (not 64 hex characters)
        print("\n2. Cleaning up invalid device tokens...")
        invalid_cleanup_query = """
            DELETE FROM iosapp.device_tokens 
            WHERE device_token IS NOT NULL 
            AND (LENGTH(device_token) != 64 OR device_token ~ '[^0-9a-fA-F]');
        """
        await db_manager.execute_command(invalid_cleanup_query)
        print(f"   ✅ Removed invalid device tokens")
        
        # Step 3: Restore NOT NULL constraint
        print("\n3. Restoring NOT NULL constraint on device_token...")
        alter_query = """
            ALTER TABLE iosapp.device_tokens 
            ALTER COLUMN device_token SET NOT NULL;
        """
        await db_manager.execute_command(alter_query)
        print("   ✅ NOT NULL constraint restored")
        
        # Step 4: Verify the change
        print("\n4. Verifying schema restoration...")
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
        
        if result and result[0]['is_nullable'] == 'NO':
            print("   ✅ device_token now requires NOT NULL (data integrity enforced)")
        else:
            print("   ❌ Schema restoration failed")
            return False
        
        # Step 5: Show current clean state
        print("\n5. Current device tokens state:")
        status_query = """
            SELECT 
                COUNT(*) as total_devices,
                COUNT(CASE WHEN LENGTH(device_token) = 64 THEN 1 END) as valid_tokens
            FROM iosapp.device_tokens
            WHERE is_active = true;
        """
        stats = await db_manager.execute_query(status_query)
        
        if stats:
            stat = stats[0]
            print(f"   📊 Total active devices: {stat['total_devices']}")
            print(f"   📊 Valid APNs tokens: {stat['valid_tokens']}")
        
        print("\n🎉 Schema restoration completed successfully!")
        print("\n💡 Data Integrity Benefits:")
        print("   ✅ NOT NULL constraint prevents invalid data entry")
        print("   ✅ Database enforces valid device token requirement")
        print("   ✅ No more workarounds needed - proper validation instead")
        print("   ✅ Clean separation: only real APNs tokens allowed")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error reverting schema: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(revert_schema())
    if success:
        print("\n🚀 Database now enforces data integrity with proper constraints!")
    else:
        print("\n💥 Schema reversion failed - manual intervention needed")