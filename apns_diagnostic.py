#!/usr/bin/env python3
"""
Comprehensive APNs diagnostic to identify the root cause
"""
import json
import time
import base64
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import hashlib

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

print("=== APNs Comprehensive Diagnostic ===")

# 1. Validate key format and content
print("\n1. Key Validation:")
print(f"   Key ID: {APNS_KEY_ID} (length: {len(APNS_KEY_ID)})")
print(f"   Team ID: {APNS_TEAM_ID} (length: {len(APNS_TEAM_ID)})")
print(f"   Bundle ID: {APNS_BUNDLE_ID}")
print(f"   Key starts correctly: {APNS_PRIVATE_KEY.startswith('-----BEGIN PRIVATE KEY-----')}")
print(f"   Key ends correctly: {APNS_PRIVATE_KEY.strip().endswith('-----END PRIVATE KEY-----')}")

# 2. Load and validate private key
print("\n2. Private Key Analysis:")
try:
    private_key = serialization.load_pem_private_key(
        APNS_PRIVATE_KEY.encode('utf-8'),
        password=None
    )
    print(f"   Key type: {type(private_key)}")
    print(f"   Key algorithm: {private_key.algorithm.name}")
    print(f"   Key size: {private_key.key_size} bits")
    
    if isinstance(private_key, ec.EllipticCurvePrivateKey):
        print(f"   Curve: {private_key.curve.name}")
        print(f"   Curve key size: {private_key.curve.key_size}")
        
        # Check if it's the correct curve for ES256
        if private_key.curve.name == 'secp256r1':
            print("   ✓ Correct curve for ES256 (P-256)")
        else:
            print("   ✗ Wrong curve for ES256")
    
except Exception as e:
    print(f"   ✗ Key loading failed: {e}")

# 3. Generate and analyze JWT token
print("\n3. JWT Token Analysis:")
try:
    now = int(time.time())
    
    # Test different token configurations
    configurations = [
        {
            "name": "Standard JWT",
            "payload": {"iss": APNS_TEAM_ID, "iat": now},
            "headers": {"alg": "ES256", "kid": APNS_KEY_ID}
        },
        {
            "name": "With Expiry",
            "payload": {"iss": APNS_TEAM_ID, "iat": now, "exp": now + 3600},
            "headers": {"alg": "ES256", "kid": APNS_KEY_ID}
        },
        {
            "name": "Minimal Headers",
            "payload": {"iss": APNS_TEAM_ID, "iat": now},
            "headers": {"alg": "ES256", "kid": APNS_KEY_ID}
        }
    ]
    
    for config in configurations:
        print(f"\n   {config['name']}:")
        try:
            token = jwt.encode(
                config["payload"], 
                private_key, 
                algorithm='ES256', 
                headers=config["headers"]
            )
            
            # Analyze token
            parts = token.split('.')
            print(f"   Token: {token[:50]}...")
            print(f"   Parts: {len(parts)}")
            
            # Check for problematic characters
            forbidden_chars = ['=', '+']
            has_forbidden = any(char in token for char in forbidden_chars)
            print(f"   Contains =,+: {has_forbidden}")
            
            # Verify token can be decoded
            decoded = jwt.decode(token, private_key, algorithms=['ES256'])
            print(f"   Verification: ✓ Success")
            print(f"   Decoded ISS: {decoded.get('iss')}")
            print(f"   Decoded IAT: {decoded.get('iat')}")
            
        except Exception as e:
            print(f"   Generation failed: {e}")

except Exception as e:
    print(f"   JWT analysis failed: {e}")

# 4. Key fingerprint analysis
print("\n4. Key Fingerprint Analysis:")
try:
    private_key = serialization.load_pem_private_key(
        APNS_PRIVATE_KEY.encode('utf-8'),
        password=None
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Get public key in PEM format
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Calculate SHA256 fingerprint
    fingerprint = hashlib.sha256(pem_public).hexdigest()
    print(f"   Public Key Fingerprint: {fingerprint}")
    
    # Get key coordinates for debugging
    public_numbers = public_key.public_numbers()
    print(f"   Public Key X: {hex(public_numbers.x)}")
    print(f"   Public Key Y: {hex(public_numbers.y)}")
    
except Exception as e:
    print(f"   Fingerprint analysis failed: {e}")

# 5. Common issues checklist
print("\n5. Common Issues Checklist:")
issues = [
    ("Key ID format", len(APNS_KEY_ID) == 10),
    ("Team ID format", len(APNS_TEAM_ID) == 10),
    ("Bundle ID format", '.' in APNS_BUNDLE_ID),
    ("Key PEM format", APNS_PRIVATE_KEY.startswith('-----BEGIN PRIVATE KEY-----')),
    ("Key completeness", APNS_PRIVATE_KEY.strip().endswith('-----END PRIVATE KEY-----')),
]

for issue, check in issues:
    status = "✓" if check else "✗"
    print(f"   {status} {issue}")

print("\n6. Recommendations:")
print("   - Verify Key ID and Team ID in Apple Developer Console")
print("   - Check if the APNs key is enabled and not revoked")
print("   - Ensure the key has proper permissions for the bundle ID")
print("   - Consider regenerating the APNs key if issues persist")
print("   - Verify the app is properly configured for push notifications")
print("   - Check if the bundle ID matches exactly (case sensitive)")