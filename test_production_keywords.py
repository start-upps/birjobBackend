#!/usr/bin/env python3
"""
Test new keyword endpoints in production
"""

import requests
import json
import time

BASE_URL = "https://birjobbackend-ir3e.onrender.com"

def test_endpoint(method, endpoint, data=None):
    """Test an endpoint and return results"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        return {
            "status": response.status_code,
            "success": 200 <= response.status_code < 300,
            "data": response.json() if response.text else {},
            "error": None
        }
    except Exception as e:
        return {
            "status": 0,
            "success": False,
            "data": {},
            "error": str(e)
        }

def main():
    print("🧪 Testing Profile Keyword Endpoints in Production")
    print("=" * 60)
    
    device_id = "test-device-123"
    
    # Test 1: Get keywords (should work with sample profile)
    print("1. Testing GET keywords...")
    result = test_endpoint("GET", f"/api/v1/users/{device_id}/profile/keywords")
    print(f"   Status: {result['status']} | Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['data'].get('detail', result['error'])}")
    else:
        print(f"   Keywords: {result['data'].get('data', {}).get('matchKeywords', [])}")
    
    # Test 2: Add a keyword
    print("\n2. Testing ADD keyword...")
    result = test_endpoint("POST", f"/api/v1/users/{device_id}/profile/keywords/add", 
                          {"keyword": "docker"})
    print(f"   Status: {result['status']} | Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['data'].get('detail', result['error'])}")
    else:
        print(f"   Added: {result['data'].get('data', {}).get('addedKeyword')}")
        print(f"   Total: {result['data'].get('data', {}).get('keywordCount')} keywords")
    
    # Test 3: Update keywords list
    print("\n3. Testing UPDATE keywords...")
    result = test_endpoint("POST", f"/api/v1/users/{device_id}/profile/keywords", 
                          {"matchKeywords": ["python", "react", "docker", "kubernetes"]})
    print(f"   Status: {result['status']} | Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['data'].get('detail', result['error'])}")
    else:
        print(f"   Updated: {result['data'].get('data', {}).get('keywordCount')} keywords")
    
    # Test 4: Get matches
    print("\n4. Testing GET matches...")
    result = test_endpoint("GET", f"/api/v1/users/{device_id}/profile/matches?limit=3")
    print(f"   Status: {result['status']} | Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['data'].get('detail', result['error'])}")
    else:
        matches = result['data'].get('data', {}).get('matches', [])
        print(f"   Found: {len(matches)} matches")
        if matches:
            top_match = matches[0]
            print(f"   Top match: {top_match.get('title')} (Score: {top_match.get('matchScore', 0)})")
    
    # Test 5: Remove a keyword
    print("\n5. Testing DELETE keyword...")
    result = test_endpoint("DELETE", f"/api/v1/users/{device_id}/profile/keywords/kubernetes")
    print(f"   Status: {result['status']} | Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['data'].get('detail', result['error'])}")
    else:
        print(f"   Removed: {result['data'].get('data', {}).get('removedKeyword')}")
        print(f"   Remaining: {result['data'].get('data', {}).get('keywordCount')} keywords")
    
    # Test 6: Test with different device (should fail)
    print("\n6. Testing with non-existent device...")
    result = test_endpoint("GET", f"/api/v1/users/non-existent-device/profile/keywords")
    print(f"   Status: {result['status']} | Success: {result['success']}")
    if not result['success']:
        print(f"   Error: {result['data'].get('detail', result['error'])}")
    
    print("\n" + "=" * 60)
    print("🏁 Testing completed!")

if __name__ == "__main__":
    main()