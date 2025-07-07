#!/usr/bin/env python3
"""
Test APNs with fresh connection to avoid token blacklisting
"""
import asyncio
import json
import time
import jwt
import sys
import os

# Add the project directory to path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from cryptography.hazmat.primitives import serialization

# APNs credentials
APNS_KEY_ID = 'S64YC3U4ZX'
APNS_TEAM_ID = 'KK5HUUQ3HR'
APNS_BUNDLE_ID = 'com.ismats.birjob'
APNS_PRIVATE_KEY = '''-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgFljk5QxwP0CLoUNi
/q5ueu5oQxM+oaobqAzll9I26M6gCgYIKoZIzj0DAQehRANCAATDbd3F1dpA9uvc
s1PIM1fkqJ03U86jfbDmTVk6m+XkA7UfNVLNBt26kRKVKoZf4oP3HQt+iDiNcC5N
bx1gyLzI
-----END PRIVATE KEY-----'''

DEVICE_TOKEN = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'

def create_fresh_jwt_token():
    """Create a fresh JWT token with current timestamp"""
    private_key = serialization.load_pem_private_key(
        APNS_PRIVATE_KEY.encode('utf-8'),
        password=None
    )
    
    # Use current timestamp - never reuse old tokens
    now = int(time.time())
    
    # Create minimal payload as per Apple specs
    payload = {
        "iss": APNS_TEAM_ID,
        "iat": now
    }
    
    # Create headers exactly as Apple specifies
    headers = {
        "alg": "ES256",
        "kid": APNS_KEY_ID
    }
    
    # Generate token
    token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    
    return token

async def test_fresh_connection():
    """Test with completely fresh connection and token"""
    print("=== Fresh Connection Test ===")
    
    try:
        # Import aioapns here to ensure fresh import
        from aioapns import APNs, NotificationRequest, PushType
        
        # Create fresh JWT token
        fresh_token = create_fresh_jwt_token()
        print(f"Fresh token created: {fresh_token[:50]}...")
        
        # Test different environments and configurations
        test_configs = [
            {
                "name": "Production with exact bundle ID",
                "use_sandbox": False,
                "topic": APNS_BUNDLE_ID  # com.ismats.birjob
            },
            {
                "name": "Sandbox with exact bundle ID", 
                "use_sandbox": True,
                "topic": APNS_BUNDLE_ID  # com.ismats.birjob
            }
        ]
        
        for config in test_configs:
            print(f"\n--- Testing: {config['name']} ---")
            
            try:
                # Create completely new APNs client for each test
                apns = APNs(
                    key=APNS_PRIVATE_KEY,
                    key_id=APNS_KEY_ID,
                    team_id=APNS_TEAM_ID,
                    topic=config['topic'],
                    use_sandbox=config['use_sandbox']
                )
                
                print(f"APNs client created for {config['name']}")
                print(f"Topic: {config['topic']}")
                print(f"Sandbox: {config['use_sandbox']}")
                
                # Create minimal notification payload
                request = NotificationRequest(
                    device_token=DEVICE_TOKEN,
                    message={
                        "aps": {
                            "alert": "Fresh connection test",
                            "badge": 1,
                            "sound": "default"
                        }
                    },
                    push_type=PushType.ALERT
                )
                
                # Send notification
                response = await apns.send_notification(request)
                
                print(f"Response successful: {response.is_successful}")
                if not response.is_successful:
                    print(f"Error: {response.description}")
                    print(f"Status: {response.status}")
                    print(f"Reason: {getattr(response, 'reason', 'Unknown')}")
                else:
                    print("✅ SUCCESS: Notification sent successfully!")
                    
            except Exception as e:
                print(f"❌ Exception in {config['name']}: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Overall test failed: {e}")
        import traceback
        traceback.print_exc()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_fresh_connection())