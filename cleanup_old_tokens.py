#!/usr/bin/env python3
"""
Clean up old placeholder tokens
"""
import asyncio
from app.core.database import db_manager

async def cleanup_old_tokens():
    """Clean up old placeholder tokens"""
    print("🧹 Cleaning up old placeholder tokens...")
    
    # Get all device tokens for the user
    tokens_query = """
        SELECT dt.id, dt.device_token, dt.device_id, dt.registered_at
        FROM iosapp.device_tokens dt
        JOIN iosapp.users u ON dt.user_id = u.id
        WHERE u.email = 'ismetsemedov@gmail.com'
        ORDER BY dt.registered_at DESC
    """
    
    tokens = await db_manager.execute_query(tokens_query)
    print(f"📊 Found {len(tokens)} device tokens for ismetsemedov@gmail.com:")
    
    valid_tokens = []
    placeholder_tokens = []
    
    for token in tokens:
        print(f"\n🔍 Token {token['id']}:")
        print(f"   Device token: {token['device_token'][:50]}...")
        print(f"   Device ID: {token['device_id']}")
        print(f"   Registered: {token['registered_at']}")
        
        # Check if it's a placeholder token
        if 'placeholder' in token['device_token'].lower():
            placeholder_tokens.append(token)
            print(f"   ❌ Placeholder token")
        else:
            valid_tokens.append(token)
            print(f"   ✅ Valid token")
    
    print(f"\n📊 Summary:")
    print(f"✅ Valid tokens: {len(valid_tokens)}")
    print(f"❌ Placeholder tokens: {len(placeholder_tokens)}")
    
    # Remove placeholder tokens
    for token in placeholder_tokens:
        print(f"\n🗑️ Removing placeholder token {token['id']}")
        
        # Delete push notifications for this device
        await db_manager.execute_command(
            "DELETE FROM iosapp.push_notifications WHERE device_id = $1",
            token['id']
        )
        
        # Delete device token
        await db_manager.execute_command(
            "DELETE FROM iosapp.device_tokens WHERE id = $1",
            token['id']
        )
        
        print(f"   ✅ Removed")
    
    # Verify final state
    print(f"\n📋 Final verification:")
    final_tokens = await db_manager.execute_query(tokens_query)
    
    for token in final_tokens:
        print(f"✅ Token {token['id']}: {token['device_token'][:30]}...")
        print(f"   Device ID: {token['device_id']}")
        print(f"   Registered: {token['registered_at']}")
    
    print(f"\n✅ Cleanup completed!")

if __name__ == "__main__":
    asyncio.run(cleanup_old_tokens())