#!/usr/bin/env python3
"""
Test new APNs key configuration
"""
import asyncio
import json
import time
import jwt
import httpx
from cryptography.hazmat.primitives import serialization

# NEW APNs credentials
APNS_KEY_ID = '834XDMQ3QB'  # New Key ID
APNS_TEAM_ID = 'KK5HUUQ3HR'  # Same Team ID
APNS_BUNDLE_ID = 'com.ismats.birjob'  # Same Bundle ID

# NEW private key content
APNS_PRIVATE_KEY = '''-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQggxlj6lJV54N4+M8q
NSnjn8RpdWHEKOQ2rlcbKUh0pHagCgYIKoZIzj0DAQehRANCAARuiyXZoGGQgEbf
X1Ga3at2+nYN4weIObuq386k6AD3fsJQkPmAlJgNL5KX+dIcKjRmcj7UZVy/AJrN
8f3rSnjk
-----END PRIVATE KEY-----'''

DEVICE_TOKEN = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'

def create_jwt_token_with_new_key():
    """Create JWT token with new key ID"""
    try:
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
            "kid": APNS_KEY_ID  # Using new Key ID
        }
        
        token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
        return token
    except Exception as e:
        print(f"Token creation failed: {e}")
        return None

async def test_new_key():
    """Test with new APNs key configuration"""
    print("=== Testing New APNs Key Configuration ===")
    print(f"New Key ID: {APNS_KEY_ID}")
    print(f"Team ID: {APNS_TEAM_ID}")
    print(f"Bundle ID: {APNS_BUNDLE_ID}")
    
    # Create JWT token
    token = create_jwt_token_with_new_key()
    if not token:
        print("❌ Failed to create JWT token")
        return
    
    print(f"JWT Token created: {token[:50]}...")
    
    # Test payload
    payload = {
        "aps": {
            "alert": {
                "title": "New Key Test",
                "body": "Testing with new APNs key"
            },
            "badge": 1,
            "sound": "default"
        }
    }
    
    # Test both environments
    environments = [
        ("Production", "https://api.push.apple.com"),
        ("Sandbox", "https://api.sandbox.push.apple.com")
    ]
    
    for env_name, base_url in environments:
        print(f"\n--- Testing {env_name} ---")
        
        try:
            url = f"{base_url}/3/device/{DEVICE_TOKEN}"
            
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
                else:
                    print(f"❌ Error: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

print("⚠️  Note: This test uses the old private key with new Key ID")
print("   You need to update APNS_PRIVATE_KEY with the new .p8 file content")
print("   for the test to work properly.")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_new_key())