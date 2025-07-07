#!/usr/bin/env python3
"""
Manual APNs HTTP/2 request to bypass library issues
"""
import asyncio
import json
import time
import jwt
import httpx
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

# Test device token
DEVICE_TOKEN = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'

# APNs URLs
APNS_PRODUCTION_URL = 'https://api.push.apple.com'
APNS_SANDBOX_URL = 'https://api.sandbox.push.apple.com'

def create_jwt_token():
    """Create JWT token exactly as Apple specifies"""
    
    # Load private key
    private_key = serialization.load_pem_private_key(
        APNS_PRIVATE_KEY.encode('utf-8'),
        password=None
    )
    
    # Create token with minimal payload (no exp field)
    now = int(time.time())
    payload = {
        "iss": APNS_TEAM_ID,
        "iat": now
    }
    
    headers = {
        "alg": "ES256",
        "kid": APNS_KEY_ID
    }
    
    # Use PyJWT with explicit algorithm
    token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    
    return token

async def send_manual_apns_request():
    """Send manual HTTP/2 request to APNs"""
    
    print("=== Manual APNs HTTP/2 Request ===")
    
    # Create JWT token
    token = create_jwt_token()
    print(f"JWT Token: {token}")
    
    # Create notification payload
    payload = {
        "aps": {
            "alert": {
                "title": "Manual Test",
                "body": "Testing direct APNs HTTP/2 request"
            },
            "badge": 1,
            "sound": "default"
        }
    }
    
    # Test both environments
    for env_name, base_url in [("Production", APNS_PRODUCTION_URL), ("Sandbox", APNS_SANDBOX_URL)]:
        print(f"\nTesting {env_name} environment...")
        
        try:
            # Create request URL
            url = f"{base_url}/3/device/{DEVICE_TOKEN}"
            
            # Create headers
            headers = {
                'authorization': f'bearer {token}',
                'apns-topic': APNS_BUNDLE_ID,
                'apns-push-type': 'alert',
                'content-type': 'application/json'
            }
            
            # Make HTTP/2 request
            async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                
                print(f"{env_name} Status: {response.status_code}")
                print(f"{env_name} Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print(f"{env_name} SUCCESS: Push notification sent!")
                else:
                    print(f"{env_name} Response: {response.text}")
                    
        except Exception as e:
            print(f"{env_name} Error: {e}")

# Run the test
asyncio.run(send_manual_apns_request())