#!/usr/bin/env python3
"""
Debug APNs JWT token generation to find the exact issue
"""
import os
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta

# Set environment
os.environ['APNS_KEY_ID'] = 'S64YC3U4ZX'
os.environ['APNS_TEAM_ID'] = 'KK5HUUQ3HR'
os.environ['APNS_BUNDLE_ID'] = 'com.ismats.birjob'
os.environ['APNS_SANDBOX'] = 'false'
os.environ['APNS_PRIVATE_KEY'] = '''-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgFljk5QxwP0CLoUNi
/q5ueu5oQxM+oaobqAzll9I26M6gCgYIKoZIzj0DAQehRANCAATDbd3F1dpA9uvc
s1PIM1fkqJ03U86jfbDmTVk6m+XkA7UfNVLNBt26kRKVKoZf4oP3HQt+iDiNcC5N
bx1gyLzI
-----END PRIVATE KEY-----'''

sys.path.append('/Users/ismatsamadov/birjobBackend')

try:
    from aioapns import APNs, NotificationRequest, PushType
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    import jwt
    
    print("=== APNs JWT Debug ===")
    
    # Test key loading
    private_key_content = os.environ['APNS_PRIVATE_KEY']
    print(f"Key length: {len(private_key_content)}")
    
    # Load the private key
    private_key = serialization.load_pem_private_key(
        private_key_content.encode('utf-8'),
        password=None
    )
    print(f"Key type: {type(private_key)}")
    print(f"Key curve: {private_key.curve.name}")
    print(f"Key size: {private_key.key_size}")
    
    # Generate JWT token manually
    now = int(time.time())
    payload = {
        'iss': os.environ['APNS_TEAM_ID'],
        'iat': now,
        'exp': now + 3600  # 1 hour expiry
    }
    
    headers = {
        'alg': 'ES256',
        'kid': os.environ['APNS_KEY_ID']
    }
    
    # Generate JWT
    token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    print(f"Generated JWT: {token[:50]}...")
    
    # Verify the JWT can be decoded
    decoded = jwt.decode(token, private_key, algorithms=['ES256'])
    print(f"JWT verification: SUCCESS")
    print(f"JWT payload: {decoded}")
    
    # Test APNs client creation
    async def test_apns():
        try:
            apns = APNs(
                key=private_key_content,
                key_id=os.environ['APNS_KEY_ID'],
                team_id=os.environ['APNS_TEAM_ID'],
                topic=os.environ['APNS_BUNDLE_ID'],
                use_sandbox=False
            )
            print("APNs client created successfully")
            
            # Try sending a test notification with the user's actual device token
            request = NotificationRequest(
                device_token='a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60',
                message={
                    'aps': {
                        'alert': 'Debug test',
                        'badge': 1,
                        'sound': 'default'
                    }
                },
                push_type=PushType.ALERT
            )
            
            response = await apns.send_notification(request)
            print(f"APNs Response: {response}")
            print(f"Success: {response.is_successful}")
            if not response.is_successful:
                print(f"Error: {response.description}")
                print(f"Status: {response.status}")
            
        except Exception as e:
            print(f"APNs test failed: {e}")
    
    asyncio.run(test_apns())
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()