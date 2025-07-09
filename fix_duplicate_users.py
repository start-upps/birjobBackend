#!/usr/bin/env python3
"""
Fix duplicate users by merging device tokens to the user with email and keywords
"""
import asyncio
from app.core.database import db_manager

async def fix_duplicate_users():
    """Fix duplicate users by merging device tokens"""
    print("🔄 Fixing duplicate users...")
    
    # Get all users
    users_query = """
        SELECT u.id, u.email, u.keywords, u.notifications_enabled,
               dt.device_token, dt.device_id, dt.id as device_token_id
        FROM iosapp.users u
        LEFT JOIN iosapp.device_tokens dt ON u.id = dt.user_id
        ORDER BY u.created_at
    """
    
    users = await db_manager.execute_query(users_query)
    print(f"📊 Found {len(users)} user-device records:")
    
    # Identify the target user (with email and keywords)
    target_user = None
    empty_users = []
    
    for user in users:
        print(f"\n👤 User {user['id']}")
        print(f"   Email: {user['email']}")
        print(f"   Keywords: {user['keywords']}")
        print(f"   Device token: {user['device_token'][:30] + '...' if user['device_token'] else 'None'}")
        
        # Check if this user has email and keywords
        has_email = user['email'] and user['email'].strip()
        has_keywords = user['keywords'] and user['keywords'] not in ['[]', None]
        
        if has_email and has_keywords:
            target_user = user
            print(f"   ✅ Target user (has email and keywords)")
        elif not has_email and not has_keywords:
            empty_users.append(user)
            print(f"   ❌ Empty user (no email, no keywords)")
        else:
            print(f"   ⚠️ Partial user")
    
    if not target_user:
        print("❌ No target user found with email and keywords")
        return
    
    if not empty_users:
        print("✅ No empty users to clean up")
        return
    
    print(f"\n🔄 Target user: {target_user['email']} ({target_user['id']})")
    print(f"🗑️ Empty users to remove: {len(empty_users)}")
    
    # Move device tokens from empty users to target user
    for empty_user in empty_users:
        if empty_user['device_token']:
            print(f"\n🔄 Moving device token from user {empty_user['id']} to target user...")
            
            # Update device token to point to target user
            await db_manager.execute_command(
                "UPDATE iosapp.device_tokens SET user_id = $1 WHERE id = $2",
                target_user['id'],
                empty_user['device_token_id']
            )
            print(f"   ✅ Device token moved")
        
        # Delete empty user
        await db_manager.execute_command(
            "DELETE FROM iosapp.users WHERE id = $1",
            empty_user['id']
        )
        print(f"   🗑️ Empty user deleted")
    
    # Verify the final state
    print(f"\n📋 Final verification:")
    final_users = await db_manager.execute_query(users_query)
    
    for user in final_users:
        print(f"👤 User {user['id']}: {user['email']}")
        print(f"   Keywords: {user['keywords']}")
        print(f"   Device: {user['device_token'][:30] + '...' if user['device_token'] else 'None'}")
    
    print(f"\n✅ Duplicate users fixed!")

if __name__ == "__main__":
    asyncio.run(fix_duplicate_users())