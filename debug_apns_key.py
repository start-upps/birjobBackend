#!/usr/bin/env python3
"""
Debug APNs key environment variable
"""

import os
import sys
sys.path.append('/Users/ismatsamadov/birjobBackend')

from app.core.config import settings

def debug_apns_key():
    """Debug the APNs key format"""
    
    print("🔍 APNs Key Debug")
    print("="*50)
    
    # Check environment variable
    if settings.APNS_PRIVATE_KEY:
        key = settings.APNS_PRIVATE_KEY
        print(f"✅ Environment variable exists")
        print(f"📏 Length: {len(key)} characters")
        print(f"🔤 First 50 chars: {repr(key[:50])}")
        print(f"🔤 Last 50 chars: {repr(key[-50:])}")
        
        # Check for common issues
        if key.startswith('"') and key.endswith('"'):
            print("⚠️  Has outer quotes")
        
        if '\\n' in key:
            print("⚠️  Has escaped newlines")
            
        if not key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Does not start with BEGIN header")
        else:
            print("✅ Starts with correct header")
            
        if not key.strip().endswith('-----END PRIVATE KEY-----'):
            print("❌ Does not end with END footer")  
        else:
            print("✅ Ends with correct footer")
            
        # Try to clean it
        cleaned = key.strip()
        while cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()
        
        if '\\n' in cleaned:
            cleaned = cleaned.replace('\\n', '\n')
            
        print(f"\n🧹 After cleaning:")
        print(f"📏 Length: {len(cleaned)} characters")
        print(f"🔤 First 30 chars: {repr(cleaned[:30])}")
        print(f"🔤 Last 30 chars: {repr(cleaned[-30:])}")
        
        # Test with cryptography
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            private_key = load_pem_private_key(cleaned.encode(), password=None)
            print("✅ Successfully loaded with cryptography!")
            print(f"🔐 Key type: {type(private_key)}")
        except Exception as e:
            print(f"❌ Cryptography failed: {e}")
            
    else:
        print("❌ No APNS_PRIVATE_KEY environment variable")

if __name__ == "__main__":
    debug_apns_key()