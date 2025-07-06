#!/usr/bin/env python3
"""
Validate the APNs key file format
"""

from cryptography.hazmat.primitives.serialization import load_pem_private_key

def validate_apns_key():
    """Validate the APNs key file"""
    
    key_path = "/Users/ismatsamadov/birjobBackend/AuthKey_S64YC3U4ZX.p8"
    
    try:
        print(f"🔑 Validating APNs key: {key_path}")
        
        # Read the file
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        print(f"📄 File size: {len(key_data)} bytes")
        print(f"📄 First 50 chars: {key_data[:50]}")
        print(f"📄 Last 50 chars: {key_data[-50:]}")
        
        # Try to load the private key
        private_key = load_pem_private_key(key_data, password=None)
        
        print("✅ Private key loaded successfully!")
        print(f"🔐 Key type: {type(private_key)}")
        
        # Get key size info
        if hasattr(private_key, 'key_size'):
            print(f"🔐 Key size: {private_key.key_size} bits")
        
        return True
        
    except Exception as e:
        print(f"❌ Key validation failed: {e}")
        print(f"🔧 Error type: {type(e)}")
        return False

if __name__ == "__main__":
    validate_apns_key()