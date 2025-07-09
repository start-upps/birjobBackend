#!/usr/bin/env python3
"""
Cleanup script to remove placeholder device tokens from the database
"""
import asyncio
import re
from app.core.database import db_manager

def validate_device_token(token: str) -> bool:
    """Validate that device token is a valid APNs token format"""
    if not token:
        return False
    
    # Check for obvious placeholder patterns first
    placeholder_indicators = [
        'placeholder', 'test', 'fake', 'dummy', 'simulator',
        'B6BDBB52', '0B43E135', 'ABCDEF', 'abcdef',
        '1C1108D7', 'B71F57C9', 'xxxx', '____', '----', 'chars_min'
    ]
    
    token_lower = token.lower()
    for indicator in placeholder_indicators:
        if indicator.lower() in token_lower:
            return False
    
    # Remove any spaces, hyphens, underscores
    clean_token = token.replace(" ", "").replace("-", "").replace("_", "")
    
    # APNs tokens must be exactly 64 hex characters (32 bytes)
    if len(clean_token) != 64:
        return False
    
    # Check if it's all hex characters
    if not re.match(r'^[0-9a-fA-F]+$', clean_token):
        return False
    
    # Check for common placeholder patterns
    placeholder_patterns = [
        r'^0+$',  # All zeros
        r'^1+$',  # All ones
        r'^[fF]+$',  # All Fs
        r'^(123456)+',  # Repeating 123456
        r'^(abcdef)+',  # Repeating abcdef
        r'^(fedcba)+',  # Repeating fedcba
    ]
    
    for pattern in placeholder_patterns:
        if re.match(pattern, clean_token):
            return False
    
    return True

async def cleanup_placeholder_tokens():
    """Remove placeholder device tokens from database"""
    print("🧹 Starting placeholder token cleanup...")
    
    # Get all device tokens
    query = """
        SELECT dt.id, dt.device_token, dt.device_id, dt.user_id, u.email
        FROM iosapp.device_tokens dt
        LEFT JOIN iosapp.users u ON dt.user_id = u.id
        ORDER BY dt.id DESC
    """
    
    device_tokens = await db_manager.execute_query(query)
    print(f"📱 Found {len(device_tokens)} device tokens to check")
    
    invalid_tokens = []
    valid_tokens = []
    
    for token_record in device_tokens:
        device_token = token_record['device_token']
        if validate_device_token(device_token):
            valid_tokens.append(token_record)
            print(f"✅ Valid token: {device_token[:20]}...")
        else:
            invalid_tokens.append(token_record)
            print(f"❌ Invalid token: {device_token[:50]}...")
    
    print(f"\n📊 Summary:")
    print(f"✅ Valid tokens: {len(valid_tokens)}")
    print(f"❌ Invalid tokens: {len(invalid_tokens)}")
    
    if invalid_tokens:
        print(f"\n🗑️ Removing {len(invalid_tokens)} invalid tokens...")
        
        # Remove device tokens
        for token_record in invalid_tokens:
            try:
                # Delete push notifications for this device
                await db_manager.execute_command(
                    "DELETE FROM iosapp.push_notifications WHERE device_id = $1",
                    token_record['id']
                )
                print(f"   Deleted push notifications for device {token_record['device_id']}")
                
                # Delete device token
                await db_manager.execute_command(
                    "DELETE FROM iosapp.device_tokens WHERE id = $1",
                    token_record['id']
                )
                print(f"   Deleted device token {token_record['device_token'][:30]}...")
                
                # Check if user has any other devices
                remaining_devices = await db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM iosapp.device_tokens WHERE user_id = $1",
                    token_record['user_id']
                )
                
                if remaining_devices[0]['count'] == 0:
                    # User has no devices left - check if they have email and keywords
                    user_data = await db_manager.execute_query(
                        "SELECT email, keywords FROM iosapp.users WHERE id = $1",
                        token_record['user_id']
                    )
                    
                    if user_data and user_data[0]:
                        user = user_data[0]
                        has_email = user['email'] and user['email'].strip()
                        has_keywords = user['keywords'] and len(user['keywords']) > 0
                        
                        if not has_email and not has_keywords:
                            # Remove user with no email and no keywords
                            await db_manager.execute_command(
                                "DELETE FROM iosapp.users WHERE id = $1",
                                token_record['user_id']
                            )
                            print(f"   Deleted user {token_record['user_id']} (no email, no keywords)")
                
            except Exception as e:
                print(f"   Error removing token {token_record['device_token'][:30]}: {e}")
    
    print("\n✅ Cleanup completed!")

if __name__ == "__main__":
    asyncio.run(cleanup_placeholder_tokens())