#!/usr/bin/env python3
"""
Manual JWT token generation test to compare with Apple's JWT validator
"""
import jwt
import time
import json
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

print("=== Manual JWT Token Generation ===")

# Load the private key
private_key = serialization.load_pem_private_key(
    APNS_PRIVATE_KEY.encode('utf-8'),
    password=None
)

# Generate JWT token
now = int(time.time())
payload = {
    'iss': APNS_TEAM_ID,
    'iat': now,
    'exp': now + 3600  # 1 hour expiry
}

headers = {
    'alg': 'ES256',
    'kid': APNS_KEY_ID
}

# Generate JWT
token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
print(f"Generated JWT Token:")
print(token)
print()

# Decode and verify
try:
    decoded = jwt.decode(token, private_key, algorithms=['ES256'])
    print(f"JWT Payload: {json.dumps(decoded, indent=2)}")
    print(f"JWT Headers: {json.dumps(headers, indent=2)}")
    print()
    
    # Print token parts for manual verification
    parts = token.split('.')
    print(f"JWT Parts:")
    print(f"Header: {parts[0]}")
    print(f"Payload: {parts[1]}")
    print(f"Signature: {parts[2]}")
    
except Exception as e:
    print(f"JWT verification failed: {e}")