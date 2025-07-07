#!/usr/bin/env python3
"""
Test system time synchronization and APNs token timing issues
"""
import time
import datetime
import requests
import json
import jwt
from cryptography.hazmat.primitives import serialization

# APNs credentials
APNS_KEY_ID = 'S64YC3U4ZX'
APNS_TEAM_ID = 'KK5HUUQ3HR'
APNS_PRIVATE_KEY = '''-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgFljk5QxwP0CLoUNi
/q5ueu5oQxM+oaobqAzll9I26M6gCgYIKoZIzj0DAQehRANCAATDbd3F1dpA9uvc
s1PIM1fkqJ03U86jfbDmTVk6m+XkA7UfNVLNBt26kRKVKoZf4oP3HQt+iDiNcC5N
bx1gyLzI
-----END PRIVATE KEY-----'''

print("=== System Time and APNs Token Timing Test ===")

# 1. Check system time against NTP servers
print("\n1. System Time Validation:")
local_time = time.time()
local_datetime = datetime.datetime.fromtimestamp(local_time)
print(f"   Local time: {local_datetime} ({local_time})")

try:
    # Get time from world clock API
    response = requests.get('http://worldtimeapi.org/api/timezone/UTC', timeout=5)
    if response.status_code == 200:
        data = response.json()
        utc_time = data['unixtime']
        time_diff = abs(local_time - utc_time)
        print(f"   UTC time: {datetime.datetime.fromtimestamp(utc_time)} ({utc_time})")
        print(f"   Time difference: {time_diff:.2f} seconds")
        
        if time_diff > 60:  # More than 1 minute difference
            print("   ⚠️  WARNING: System time is significantly different from UTC!")
        else:
            print("   ✓ System time appears to be synchronized")
    else:
        print("   Could not fetch UTC time from API")
except Exception as e:
    print(f"   Error checking time: {e}")

# 2. Test JWT token generation with different timestamps
print("\n2. JWT Token Timing Test:")

private_key = serialization.load_pem_private_key(
    APNS_PRIVATE_KEY.encode('utf-8'),
    password=None
)

# Test different timestamp scenarios
test_cases = [
    ("Current time", int(time.time())),
    ("1 minute ago", int(time.time()) - 60),
    ("5 minutes ago", int(time.time()) - 300),
    ("30 minutes ago", int(time.time()) - 1800),
    ("1 hour ago", int(time.time()) - 3600),
    ("2 hours ago", int(time.time()) - 7200),
]

for case_name, timestamp in test_cases:
    print(f"\n   Testing {case_name} ({timestamp}):")
    
    try:
        # Create token with specific timestamp
        payload = {
            "iss": APNS_TEAM_ID,
            "iat": timestamp
        }
        
        headers = {
            "alg": "ES256",
            "kid": APNS_KEY_ID
        }
        
        # Generate token with compact JSON (no spaces)
        token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
        
        # Validate token format
        parts = token.split('.')
        print(f"      Token parts: {len(parts)}")
        print(f"      Token length: {len(token)}")
        print(f"      Contains forbidden chars: {'=' in token or '+' in token}")
        
        # Check token age
        age = int(time.time()) - timestamp
        print(f"      Token age: {age} seconds")
        
        if age > 3600:  # More than 1 hour
            print("      ⚠️  Token is older than 1 hour (will be rejected)")
        elif age > 1800:  # More than 30 minutes
            print("      ⚠️  Token is older than 30 minutes (risky)")
        else:
            print("      ✓ Token age is acceptable")
            
        # Try to decode the token
        decoded = jwt.decode(token, private_key, algorithms=['ES256'])
        print(f"      ✓ Token validation successful")
        
    except Exception as e:
        print(f"      ✗ Token generation failed: {e}")

# 3. Recommend fixes
print("\n3. Recommendations:")
print("   - If time difference > 60 seconds, synchronize system clock")
print("   - Use NTP to keep system time accurate")
print("   - Generate tokens with current timestamp only")
print("   - Refresh tokens every 20-30 minutes")
print("   - Avoid reusing expired tokens to prevent blacklisting")