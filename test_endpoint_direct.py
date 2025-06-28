#!/usr/bin/env python3
"""
Test individual keyword endpoint with detailed logging
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Add the app directory to Python path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from application import app

client = TestClient(app)

def test_get_keywords():
    """Test GET keywords endpoint"""
    print("🔍 Testing GET /api/v1/users/test-device-123/profile/keywords")
    
    try:
        response = client.get("/api/v1/users/test-device-123/profile/keywords")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Error Response: {response.text}")
            try:
                error_json = response.json()
                print(f"❌ Error JSON: {error_json}")
            except:
                pass
                
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        import traceback
        traceback.print_exc()

def test_add_keyword():
    """Test ADD keyword endpoint"""
    print("\n🔍 Testing POST /api/v1/users/test-device-123/profile/keywords/add")
    
    try:
        response = client.post(
            "/api/v1/users/test-device-123/profile/keywords/add",
            json={"keyword": "nodejs"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Success: {response.json()}")
        else:
            print(f"❌ Error Response: {response.text}")
            try:
                error_json = response.json()
                print(f"❌ Error JSON: {error_json}")
            except:
                pass
                
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing keyword endpoints directly...")
    test_get_keywords()
    test_add_keyword()
    print("🏁 Testing completed!")