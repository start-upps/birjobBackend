#!/usr/bin/env python3
"""
Fix duplicate user creation issue
"""
import asyncio
import sys
sys.path.append('.')

from app.core.database import db_manager

async def fix_duplicate_users():
    """Remove duplicate users and fix the registration logic"""
    
    print("🔧 Fixing duplicate user creation...")
    
    # 1. Find and merge duplicate users
    duplicate_query = """
        SELECT device_id, COUNT(*) as count
        FROM iosapp.device_tokens 
        WHERE is_active = true
        GROUP BY device_id
        HAVING COUNT(*) > 1
    """
    
    duplicates = await db_manager.execute_query(duplicate_query)
    
    if duplicates:
        print(f"Found {len(duplicates)} devices with duplicate users")
        
        for duplicate in duplicates:
            device_id = duplicate['device_id']
            print(f"\n🔄 Fixing duplicates for device: {device_id}")
            
            # Get all device_tokens for this device_id
            device_tokens_query = """
                SELECT dt.id, dt.user_id, dt.device_token, u.email, u.keywords, u.created_at
                FROM iosapp.device_tokens dt
                JOIN iosapp.users u ON dt.user_id = u.id
                WHERE dt.device_id = $1
                ORDER BY u.created_at ASC
            """
            
            tokens = await db_manager.execute_query(device_tokens_query, device_id)
            
            if len(tokens) > 1:
                # Keep the first (oldest) user, merge data from others
                primary_token = tokens[0]
                primary_user_id = primary_token['user_id']
                
                print(f"   Primary user: {primary_user_id} (email: {primary_token['email']})")
                
                # Collect all emails and keywords from duplicates
                emails = [t['email'] for t in tokens if t['email']]
                all_keywords = []
                valid_device_token = None
                
                for token in tokens:
                    # Get the real device token (not placeholder)
                    if token['device_token'] and len(token['device_token']) == 64 and not token['device_token'].startswith('placeholder'):
                        valid_device_token = token['device_token']
                    
                    # Collect keywords
                    if token['keywords']:
                        import json
                        try:
                            keywords = json.loads(token['keywords']) if isinstance(token['keywords'], str) else token['keywords']
                            all_keywords.extend(keywords)
                        except:
                            pass
                
                # Remove duplicates from keywords
                unique_keywords = list(set(all_keywords))
                primary_email = emails[0] if emails else None
                
                print(f"   Merging keywords: {unique_keywords}")
                print(f"   Using email: {primary_email}")
                print(f"   Valid device token: {valid_device_token[:20] + '...' if valid_device_token else 'None'}")
                
                # Update primary user with merged data
                update_primary_query = """
                    UPDATE iosapp.users 
                    SET email = $1, keywords = $2, updated_at = NOW()
                    WHERE id = $3
                """
                await db_manager.execute_command(
                    update_primary_query,
                    primary_email,
                    json.dumps(unique_keywords),
                    primary_user_id
                )
                
                # Update primary device token with valid token
                if valid_device_token:
                    update_device_query = """
                        UPDATE iosapp.device_tokens 
                        SET device_token = $1, updated_at = NOW()
                        WHERE user_id = $2 AND device_id = $3
                    """
                    await db_manager.execute_command(
                        update_device_query,
                        valid_device_token,
                        primary_user_id,
                        device_id
                    )
                
                # Delete duplicate users and their device tokens
                for token in tokens[1:]:
                    user_id_to_delete = token['user_id']
                    print(f"   Deleting duplicate user: {user_id_to_delete}")
                    
                    # Delete device token first
                    await db_manager.execute_command(
                        "DELETE FROM iosapp.device_tokens WHERE user_id = $1",
                        user_id_to_delete
                    )
                    
                    # Delete user (CASCADE should handle related data)
                    await db_manager.execute_command(
                        "DELETE FROM iosapp.users WHERE id = $1",
                        user_id_to_delete
                    )
    
    # 2. Clean up any orphaned device tokens
    print("\n🧹 Cleaning up orphaned device tokens...")
    orphan_query = """
        DELETE FROM iosapp.device_tokens 
        WHERE user_id NOT IN (SELECT id FROM iosapp.users)
    """
    await db_manager.execute_command(orphan_query)
    
    # 3. Show final state
    print("\n✅ Final device state:")
    final_query = """
        SELECT 
            dt.device_id,
            dt.device_token,
            u.email,
            u.keywords,
            u.notifications_enabled
        FROM iosapp.device_tokens dt
        JOIN iosapp.users u ON dt.user_id = u.id
        WHERE dt.is_active = true
        ORDER BY dt.device_id
    """
    
    final_devices = await db_manager.execute_query(final_query)
    
    for device in final_devices:
        token_preview = device['device_token'][:20] + "..." if device['device_token'] else "None"
        print(f"   Device: {device['device_id']}")
        print(f"   Email: {device['email']}")
        print(f"   Keywords: {device['keywords']}")
        print(f"   Token: {token_preview}")
        print()
    
    print("🎉 Duplicate user fix completed!")

if __name__ == "__main__":
    asyncio.run(fix_duplicate_users())