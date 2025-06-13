#!/usr/bin/env python3
import requests
import json

# Test the deployed API
BASE_URL = "https://birjobbackend-ir3e.onrender.com"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_jobs_endpoint():
    """Test jobs endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/jobs/?limit=5")
        print(f"Jobs endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total jobs: {data['data']['pagination']['total']}")
            print(f"Jobs returned: {len(data['data']['jobs'])}")
        return response.status_code == 200
    except Exception as e:
        print(f"Jobs test failed: {e}")
        return False

def test_job_stats():
    """Test job stats endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/jobs/stats/summary")
        print(f"Job stats: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Total jobs in DB: {data['data']['total_jobs']}")
            print(f"Recent jobs (24h): {data['data']['recent_jobs_24h']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Stats test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing deployed API...")
    print("=" * 50)
    
    # Run tests
    health_ok = test_health()
    jobs_ok = test_jobs_endpoint()
    stats_ok = test_job_stats()
    
    print("=" * 50)
    print(f"Health: {'✅' if health_ok else '❌'}")
    print(f"Jobs: {'✅' if jobs_ok else '❌'}")
    print(f"Stats: {'✅' if stats_ok else '❌'}")
    
    if all([health_ok, jobs_ok, stats_ok]):
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the logs above.")