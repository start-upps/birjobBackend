#!/usr/bin/env python3
"""
Test unified user endpoints
"""

import sys
import asyncio
from fastapi.testclient import TestClient

# Add the app directory to Python path
sys.path.append('/Users/ismatsamadov/birjobBackend')

from application import app

client = TestClient(app)

def test_create_user_profile():
    """Test creating a user profile"""
    print("🔍 Testing POST /api/v1/users/profile")
    
    try:
        profile_data = {
            "device_id": "test-unified-device",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "location": "San Francisco",
            "current_job_title": "Software Engineer",
            "skills": ["python", "javascript", "react"],
            "match_keywords": ["python", "backend", "api"],
            "desired_job_types": ["Full-time", "Remote"],
            "min_salary": 80000,
            "max_salary": 120000
        }
        
        response = client.post("/api/v1/users/profile", json=profile_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
            return result["data"]["deviceId"]
        else:
            print(f"❌ Error Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")
        return None

def test_get_user_profile(device_id):
    """Test getting a user profile"""
    print(f"\n🔍 Testing GET /api/v1/users/profile/{device_id}")
    
    try:
        response = client.get(f"/api/v1/users/profile/{device_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: Profile retrieved")
            print(f"   Name: {result['data']['personalInfo']['firstName']} {result['data']['personalInfo']['lastName']}")
            print(f"   Keywords: {result['data']['jobPreferences']['matchKeywords']}")
            print(f"   Completeness: {result['data']['profileCompleteness']}%")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")

def test_get_keywords(device_id):
    """Test getting profile keywords"""
    print(f"\n🔍 Testing GET /api/v1/users/{device_id}/profile/keywords")
    
    try:
        response = client.get(f"/api/v1/users/{device_id}/profile/keywords")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['data']['keywordCount']} keywords")
            print(f"   Keywords: {result['data']['matchKeywords']}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")

def test_add_keyword(device_id):
    """Test adding a keyword"""
    print(f"\n🔍 Testing POST /api/v1/users/{device_id}/profile/keywords/add")
    
    try:
        response = client.post(
            f"/api/v1/users/{device_id}/profile/keywords/add",
            json={"keyword": "docker"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            print(f"   Total keywords: {result['data']['keywordCount']}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")

def test_update_keywords(device_id):
    """Test updating keywords list"""
    print(f"\n🔍 Testing POST /api/v1/users/{device_id}/profile/keywords")
    
    try:
        response = client.post(
            f"/api/v1/users/{device_id}/profile/keywords",
            json={"match_keywords": ["python", "react", "docker", "kubernetes", "aws"]}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            print(f"   Updated keywords: {result['data']['matchKeywords']}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")

def test_get_matches(device_id):
    """Test getting job matches"""
    print(f"\n🔍 Testing GET /api/v1/users/{device_id}/profile/matches")
    
    try:
        response = client.get(f"/api/v1/users/{device_id}/profile/matches?limit=3")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            matches = result['data']['matches']
            print(f"✅ Success: Found {len(matches)} matches")
            if matches:
                top_match = matches[0]
                print(f"   Top match: {top_match['title']} (Score: {top_match.get('matchScore', 0)})")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")

def test_remove_keyword(device_id):
    """Test removing a keyword"""
    print(f"\n🔍 Testing DELETE /api/v1/users/{device_id}/profile/keywords/kubernetes")
    
    try:
        response = client.delete(f"/api/v1/users/{device_id}/profile/keywords/kubernetes")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            print(f"   Remaining keywords: {result['data']['keywordCount']}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception occurred: {e}")

if __name__ == "__main__":
    print("🧪 Testing unified user endpoints...")
    
    # Test 1: Create profile
    device_id = test_create_user_profile()
    
    if device_id:
        # Test 2: Get profile
        test_get_user_profile(device_id)
        
        # Test 3: Get keywords
        test_get_keywords(device_id)
        
        # Test 4: Add keyword
        test_add_keyword(device_id)
        
        # Test 5: Update keywords
        test_update_keywords(device_id)
        
        # Test 6: Get matches
        test_get_matches(device_id)
        
        # Test 7: Remove keyword
        test_remove_keyword(device_id)
    
    print("\n🏁 Testing completed!")