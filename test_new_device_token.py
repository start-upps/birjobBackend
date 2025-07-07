#!/usr/bin/env python3
"""
Test push notifications with the new device token
"""
import asyncio
import json
import time
import jwt
import httpx
from cryptography.hazmat.primitives import serialization

# NEW APNs credentials
APNS_KEY_ID = '834XDMQ3QB'
APNS_TEAM_ID = 'KK5HUUQ3HR'
APNS_BUNDLE_ID = 'com.ismats.birjob'
APNS_PRIVATE_KEY = '''-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQggxlj6lJV54N4+M8q
NSnjn8RpdWHEKOQ2rlcbKUh0pHagCgYIKoZIzj0DAQehRANCAARuiyXZoGGQgEbf
X1Ga3at2+nYN4weIObuq386k6AD3fsJQkPmAlJgNL5KX+dIcKjRmcj7UZVy/AJrN
8f3rSnjk
-----END PRIVATE KEY-----'''

# NEW device token from iOS app logs
NEW_DEVICE_TOKEN = '328b1bcf9414e941a07f5d102260b4e48245f83cc07291e62ff2eb16c478a442'

def create_jwt_token():
    """Create JWT token with new key"""
    private_key = serialization.load_pem_private_key(
        APNS_PRIVATE_KEY.encode('utf-8'),
        password=None
    )
    
    now = int(time.time())
    payload = {
        "iss": APNS_TEAM_ID,
        "iat": now
    }
    
    headers = {
        "alg": "ES256",
        "kid": APNS_KEY_ID
    }
    
    token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    return token

async def test_new_device_token():
    """Test push notifications with new device token from iOS app"""
    print("=== Testing New Device Token ===")
    print(f"Device Token: {NEW_DEVICE_TOKEN}")
    print(f"Key ID: {APNS_KEY_ID}")
    print(f"Bundle ID: {APNS_BUNDLE_ID}")
    
    # Create JWT token
    token = create_jwt_token()
    print(f"JWT Token: {token[:50]}...")
    
    # Test payload
    payload = {
        "aps": {
            "alert": {
                "title": "🎉 Push Notifications Fixed!",
                "body": "Your job app is now receiving notifications"
            },
            "badge": 1,
            "sound": "default"
        },
        "custom_data": {
            "type": "test",
            "message": "APNs working with new key"
        }
    }
    
    # Test both environments
    environments = [
        ("Sandbox", "https://api.sandbox.push.apple.com"),
        ("Production", "https://api.push.apple.com")
    ]
    
    for env_name, base_url in environments:
        print(f"\n--- Testing {env_name} ---")
        
        try:
            url = f"{base_url}/3/device/{NEW_DEVICE_TOKEN}"
            
            headers = {
                'authorization': f'bearer {token}',
                'apns-topic': APNS_BUNDLE_ID,
                'apns-push-type': 'alert',
                'content-type': 'application/json'
            }
            
            async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ SUCCESS: Push notification sent!")
                    print("📱 Check your iPhone for the notification!")
                else:
                    print(f"❌ Error: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_new_device_token())