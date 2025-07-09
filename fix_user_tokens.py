#!/usr/bin/env python3
"""
Fix user tokens by transferring the valid token to the user with keywords
"""
import asyncio
from app.core.database import db_manager

async def fix_user_tokens():
    """Transfer valid device token to user with keywords"""
    print("🔄 Fixing user tokens...")
    
    # Get user with keywords but no device
    user_with_keywords = await db_manager.execute_query(
        "SELECT * FROM iosapp.users WHERE email = $1",
        "ismetsemedov@gmail.com"
    )
    
    if not user_with_keywords:
        print("❌ User with keywords not found")
        return
    
    keywords_user = user_with_keywords[0]
    print(f"👤 User with keywords: {keywords_user['email']}")
    print(f"📝 Keywords: {keywords_user['keywords']}")
    
    # Get user with device but no keywords
    user_with_device = await db_manager.execute_query(
        "SELECT u.*, dt.device_token, dt.device_id FROM iosapp.users u "
        "JOIN iosapp.device_tokens dt ON u.id = dt.user_id "
        "WHERE u.email IS NULL OR u.email = '' OR u.keywords IS NULL OR jsonb_array_length(u.keywords) = 0"
    )
    
    if not user_with_device:
        print("❌ User with device but no keywords not found")
        return
    
    device_user = user_with_device[0]
    print(f"📱 User with device: {device_user['email'] or 'No email'}")
    print(f"🔧 Device token: {device_user['device_token'][:30]}...")
    print(f"🆔 Device ID: {device_user['device_id']}")
    
    # Transfer device token to user with keywords
    print("\n🔄 Transferring device token to user with keywords...")
    
    await db_manager.execute_command(
        "UPDATE iosapp.device_tokens SET user_id = $1 WHERE user_id = $2",
        keywords_user['id'],
        device_user['id']
    )
    
    # Update the user with keywords to have email if needed
    if not keywords_user['email']:
        await db_manager.execute_command(
            "UPDATE iosapp.users SET email = $1 WHERE id = $2",
            "ismetsemedov@gmail.com",
            keywords_user['id']
        )
    
    # Delete the empty user
    await db_manager.execute_command(
        "DELETE FROM iosapp.users WHERE id = $1",
        device_user['id']
    )
    
    print("✅ Device token transferred successfully!")
    
    # Verify the setup
    print("\n📋 Verification:")
    final_users = await db_manager.execute_query(
        """
        SELECT u.id, u.email, u.keywords, 
               COUNT(dt.id) as device_count,
               STRING_AGG(dt.device_token, ', ') as tokens
        FROM iosapp.users u
        LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id
        GROUP BY u.id, u.email, u.keywords
        ORDER BY u.id
        """
    )
    
    for user in final_users:
        print(f"  User {user['id']}: {user['email'] or 'No email'}")
        print(f"    Keywords: {user['keywords']}")
        print(f"    Device count: {user['device_count']}")
        if user['tokens']:
            print(f"    Tokens: {user['tokens'][:50]}...")
        print()

if __name__ == "__main__":
    asyncio.run(fix_user_tokens())