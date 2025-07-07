#!/usr/bin/env python3
"""
Validate JWT token against Apple's exact specifications
"""
import jwt
import json
import time
import base64
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

print("=== JWT Token Validation Against Apple APNs Specs ===")

# Load private key
private_key = serialization.load_pem_private_key(
    APNS_PRIVATE_KEY.encode('utf-8'),
    password=None
)

# Create JWT token exactly as Apple specifies
now = int(time.time())

# Header (exactly as Apple specifies)
header = {
    "alg": "ES256",
    "kid": APNS_KEY_ID
}

# Claims payload (exactly as Apple specifies)
payload = {
    "iss": APNS_TEAM_ID,
    "iat": now
}

print(f"Header: {json.dumps(header, indent=2)}")
print(f"Payload: {json.dumps(payload, indent=2)}")

# Generate JWT token
token = jwt.encode(payload, private_key, algorithm='ES256', headers=header)
print(f"\nGenerated JWT Token: {token}")

# Validate token parts
parts = token.split('.')
print(f"\nToken Parts Count: {len(parts)}")
print(f"Header (Base64URL): {parts[0]}")
print(f"Payload (Base64URL): {parts[1]}")
print(f"Signature (Base64URL): {parts[2]}")

# Decode and verify each part
try:
    # Decode header
    header_padding = '=' * (4 - len(parts[0]) % 4)
    header_decoded = base64.urlsafe_b64decode(parts[0] + header_padding)
    print(f"\nDecoded Header: {header_decoded.decode('utf-8')}")
    
    # Decode payload
    payload_padding = '=' * (4 - len(parts[1]) % 4)
    payload_decoded = base64.urlsafe_b64decode(parts[1] + payload_padding)
    print(f"Decoded Payload: {payload_decoded.decode('utf-8')}")
    
    # Check for forbidden characters
    forbidden_chars = ['=', '+', '-']
    has_forbidden = any(char in token for char in forbidden_chars)
    print(f"\nToken contains forbidden characters (=, +, -): {has_forbidden}")
    
    # Check token length and format
    print(f"Token length: {len(token)} characters")
    print(f"Token format valid: {len(parts) == 3}")
    
    # Check timestamp
    print(f"Timestamp (iat): {payload['iat']}")
    print(f"Current time: {now}")
    print(f"Token age: {now - payload['iat']} seconds")
    
    # Verify with PyJWT
    decoded_token = jwt.decode(token, private_key, algorithms=['ES256'])
    print(f"\nPyJWT Verification: SUCCESS")
    print(f"Decoded Token: {json.dumps(decoded_token, indent=2)}")
    
except Exception as e:
    print(f"\nValidation Error: {e}")
    import traceback
    traceback.print_exc()

# Check key format
print(f"\nKey validation:")
print(f"Key starts with correct header: {APNS_PRIVATE_KEY.startswith('-----BEGIN PRIVATE KEY-----')}")
print(f"Key ends with correct footer: {APNS_PRIVATE_KEY.strip().endswith('-----END PRIVATE KEY-----')}")
print(f"Key ID length: {len(APNS_KEY_ID)} (should be 10)")
print(f"Team ID length: {len(APNS_TEAM_ID)} (should be 10)")