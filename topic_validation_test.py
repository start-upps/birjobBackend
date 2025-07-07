#!/usr/bin/env python3
"""
Test different topic configurations to identify bundle ID issues
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

DEVICE_TOKEN = 'a68b7b14e6ae95b0e1c9bd5c32d242957ac207501f7bf5389e4c59a7370e5b60'

def create_jwt_token():
    """Create JWT token"""
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

async def test_topic_variations():
    """Test different topic configurations"""
    print("=== Topic Validation Test ===")
    
    # Test different topic variations
    topic_tests = [
        {
            "name": "Exact Bundle ID",
            "topic": "com.ismats.birjob",
            "description": "Using exact bundle ID from configuration"
        },
        {
            "name": "Alternative Bundle ID format",
            "topic": "ismats.birjob",
            "description": "Testing without 'com.' prefix"
        },
        {
            "name": "Capitalized Bundle ID",
            "topic": "com.Ismats.birjob",
            "description": "Testing with capitalized name"
        },
        {
            "name": "iOS specific Bundle ID",
            "topic": "com.ismats.birjob.ios",
            "description": "Testing with iOS suffix"
        }
    ]
    
    # Test both environments
    environments = [
        {
            "name": "Production",
            "url": "https://api.push.apple.com",
            "description": "Production APNs environment"
        },
        {
            "name": "Sandbox", 
            "url": "https://api.sandbox.push.apple.com",
            "description": "Sandbox APNs environment"
        }
    ]
    
    token = create_jwt_token()
    print(f"Using JWT token: {token[:50]}...")
    
    # Create minimal payload
    payload = {
        "aps": {
            "alert": "Topic test",
            "badge": 1
        }
    }
    
    results = []
    
    for env in environments:
        print(f"\n--- Testing {env['name']} Environment ---")
        
        for topic_test in topic_tests:
            print(f"\nTesting: {topic_test['name']} ({topic_test['topic']})")
            
            try:
                url = f"{env['url']}/3/device/{DEVICE_TOKEN}"
                
                headers = {
                    'authorization': f'bearer {token}',
                    'apns-topic': topic_test['topic'],
                    'apns-push-type': 'alert',
                    'content-type': 'application/json'
                }
                
                async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    
                    result = {
                        'environment': env['name'],
                        'topic': topic_test['topic'],
                        'status': response.status_code,
                        'response': response.text
                    }
                    results.append(result)
                    
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        print("   ✅ SUCCESS!")
                    else:
                        print(f"   ❌ Error: {response.text}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                result = {
                    'environment': env['name'],
                    'topic': topic_test['topic'],
                    'status': 'Exception',
                    'response': str(e)
                }
                results.append(result)
    
    # Summary
    print("\n=== Test Results Summary ===")
    for result in results:
        status_emoji = "✅" if result['status'] == 200 else "❌"
        print(f"{status_emoji} {result['environment']} + {result['topic']}: {result['status']}")
    
    # Check for specific error patterns
    invalid_topic_errors = [r for r in results if 'BadDeviceToken' in r['response'] or 'BadTopic' in r['response']]
    invalid_token_errors = [r for r in results if 'InvalidProviderToken' in r['response']]
    
    print(f"\nInvalidProviderToken errors: {len(invalid_token_errors)}")
    print(f"Topic-related errors: {len(invalid_topic_errors)}")
    
    if len(invalid_token_errors) == len(results):
        print("\n🔍 DIAGNOSIS: All requests failed with InvalidProviderToken")
        print("This suggests the issue is with the APNs key configuration, not the topic")
        print("\nRecommendations:")
        print("1. Verify the APNs key is enabled in Apple Developer Console")
        print("2. Check if the key has proper permissions for push notifications")
        print("3. Ensure the bundle ID is correctly configured for push notifications")
        print("4. Consider regenerating the APNs key")
        print("5. Verify the Team ID and Key ID are correct")

# Run the test
asyncio.run(test_topic_variations())