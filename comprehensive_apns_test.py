#!/usr/bin/env python3
"""
Comprehensive APNs test to identify the exact issue
"""
import asyncio
import json
import time
import sys
import os

# Add the project directory to path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from aioapns import APNs, NotificationRequest, PushType
from cryptography.hazmat.primitives import serialization
import jwt

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

# Test device token (user's actual token)
DEVICE_TOKEN = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'

print("=== Comprehensive APNs Test ===")

async def test_apns_configuration():
    """Test different APNs configurations"""
    
    # Test 1: Production APNs
    print("\n1. Testing Production APNs...")
    try:
        apns = APNs(
            key=APNS_PRIVATE_KEY,
            key_id=APNS_KEY_ID,
            team_id=APNS_TEAM_ID,
            topic=APNS_BUNDLE_ID,
            use_sandbox=False
        )
        
        request = NotificationRequest(
            device_token=DEVICE_TOKEN,
            message={
                'aps': {
                    'alert': {
                        'title': 'Production Test',
                        'body': 'Testing production APNs'
                    },
                    'badge': 1,
                    'sound': 'default'
                }
            },
            push_type=PushType.ALERT
        )
        
        response = await apns.send_notification(request)
        print(f"Production APNs - Success: {response.is_successful}")
        if not response.is_successful:
            print(f"Production APNs - Error: {response.description}")
            print(f"Production APNs - Status: {response.status}")
        
    except Exception as e:
        print(f"Production APNs - Exception: {e}")
    
    # Test 2: Sandbox APNs  
    print("\n2. Testing Sandbox APNs...")
    try:
        apns = APNs(
            key=APNS_PRIVATE_KEY,
            key_id=APNS_KEY_ID,
            team_id=APNS_TEAM_ID,
            topic=APNS_BUNDLE_ID,
            use_sandbox=True
        )
        
        request = NotificationRequest(
            device_token=DEVICE_TOKEN,
            message={
                'aps': {
                    'alert': {
                        'title': 'Sandbox Test',
                        'body': 'Testing sandbox APNs'
                    },
                    'badge': 1,
                    'sound': 'default'
                }
            },
            push_type=PushType.ALERT
        )
        
        response = await apns.send_notification(request)
        print(f"Sandbox APNs - Success: {response.is_successful}")
        if not response.is_successful:
            print(f"Sandbox APNs - Error: {response.description}")
            print(f"Sandbox APNs - Status: {response.status}")
        
    except Exception as e:
        print(f"Sandbox APNs - Exception: {e}")
    
    # Test 3: Check JWT token generation
    print("\n3. Testing JWT Generation...")
    try:
        private_key = serialization.load_pem_private_key(
            APNS_PRIVATE_KEY.encode('utf-8'),
            password=None
        )
        
        now = int(time.time())
        payload = {
            'iss': APNS_TEAM_ID,
            'iat': now,
            'exp': now + 3600
        }
        
        headers = {
            'alg': 'ES256',
            'kid': APNS_KEY_ID
        }
        
        token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
        print(f"JWT Token Generated: {token[:50]}...")
        
        # Try to decode
        decoded = jwt.decode(token, private_key, algorithms=['ES256'])
        print(f"JWT Verification: SUCCESS")
        print(f"JWT ISS: {decoded['iss']}")
        print(f"JWT KID: {headers['kid']}")
        
    except Exception as e:
        print(f"JWT Generation - Exception: {e}")
    
    # Test 4: Try with different bundle ID format
    print("\n4. Testing with alternate bundle ID...")
    try:
        apns = APNs(
            key=APNS_PRIVATE_KEY,
            key_id=APNS_KEY_ID,
            team_id=APNS_TEAM_ID,
            topic=APNS_BUNDLE_ID,  # Keep the same bundle ID
            use_sandbox=False
        )
        
        # Try with minimal payload
        request = NotificationRequest(
            device_token=DEVICE_TOKEN,
            message={
                'aps': {
                    'alert': 'Simple test'
                }
            },
            push_type=PushType.ALERT
        )
        
        response = await apns.send_notification(request)
        print(f"Simple payload - Success: {response.is_successful}")
        if not response.is_successful:
            print(f"Simple payload - Error: {response.description}")
            print(f"Simple payload - Status: {response.status}")
        
    except Exception as e:
        print(f"Simple payload - Exception: {e}")

# Run the test
asyncio.run(test_apns_configuration())