#!/usr/bin/env python3
"""
Fixed APNs test with proper Base64URL encoding
"""
import asyncio
import json
import time
import base64
import sys
import os

# Add the project directory to path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from aioapns import APNs, NotificationRequest, PushType
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
import hashlib
import hmac

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

def base64url_encode(data):
    """Proper Base64URL encoding without padding"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')

def create_custom_jwt_token():
    """Create JWT token with proper Base64URL encoding"""
    
    # Load private key
    private_key = serialization.load_pem_private_key(
        APNS_PRIVATE_KEY.encode('utf-8'),
        password=None
    )
    
    # Create header
    header = {
        "alg": "ES256",
        "kid": APNS_KEY_ID
    }
    
    # Create payload
    now = int(time.time())
    payload = {
        "iss": APNS_TEAM_ID,
        "iat": now
    }
    
    # Encode header and payload
    header_encoded = base64url_encode(json.dumps(header, separators=(',', ':')))
    payload_encoded = base64url_encode(json.dumps(payload, separators=(',', ':')))
    
    # Create signing input
    signing_input = f"{header_encoded}.{payload_encoded}"
    
    # Sign with ES256
    signature = private_key.sign(
        signing_input.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )
    
    # Encode signature
    signature_encoded = base64url_encode(signature)
    
    # Create final token
    token = f"{signing_input}.{signature_encoded}"
    
    return token

print("=== Fixed APNs Test with Proper Base64URL Encoding ===")

async def test_fixed_apns():
    """Test APNs with properly encoded JWT token"""
    
    try:
        # Create custom JWT token
        custom_token = create_custom_jwt_token()
        print(f"Custom JWT Token: {custom_token}")
        
        # Check for forbidden characters
        forbidden_chars = ['=', '+']
        has_forbidden = any(char in custom_token for char in forbidden_chars)
        print(f"Token contains forbidden characters (=, +): {has_forbidden}")
        
        # Test with aioapns using the custom token approach
        # We'll need to monkey patch or create our own client
        print("\nTesting with aioapns library...")
        
        # Create APNs client
        apns = APNs(
            key=APNS_PRIVATE_KEY,
            key_id=APNS_KEY_ID,
            team_id=APNS_TEAM_ID,
            topic=APNS_BUNDLE_ID,
            use_sandbox=False
        )
        
        # Create notification request
        request = NotificationRequest(
            device_token=DEVICE_TOKEN,
            message={
                'aps': {
                    'alert': {
                        'title': 'Fixed Test',
                        'body': 'Testing with fixed JWT encoding'
                    },
                    'badge': 1,
                    'sound': 'default'
                }
            },
            push_type=PushType.ALERT
        )
        
        # Send notification
        response = await apns.send_notification(request)
        print(f"APNs Response Success: {response.is_successful}")
        
        if not response.is_successful:
            print(f"APNs Error: {response.description}")
            print(f"APNs Status: {response.status}")
        else:
            print("SUCCESS: Push notification sent successfully!")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

# Run the test
asyncio.run(test_fixed_apns())