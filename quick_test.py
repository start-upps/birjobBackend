#!/usr/bin/env python3
"""
Quick API Endpoint Tester for BirJob Backend
"""

import requests
import time
from datetime import datetime

def test_endpoint(method, url, **kwargs):
    """Test a single endpoint"""
    start_time = time.time()
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        response_time = time.time() - start_time
        return {
            'status': response.status_code,
            'success': 200 <= response.status_code < 300,
            'time': response_time,
            'error': None
        }
    except Exception as e:
        response_time = time.time() - start_time
        return {
            'status': 0,
            'success': False,
            'time': response_time,
            'error': str(e)
        }

def main():
    base_url = "https://birjobbackend-ir3e.onrender.com"
    
    # Define all endpoints to test
    endpoints = [
        # Health endpoints
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/health/status/scraper"),
        ("GET", "/api/v1/health/scheduler-status"),
        ("GET", "/api/v1/health/check-user-tables"),
        ("GET", "/api/v1/health/db-debug"),
        
        # Jobs endpoints
        ("GET", "/api/v1/jobs/?limit=5"),
        ("GET", "/api/v1/jobs/stats/summary"),
        
        # Analytics endpoints
        ("GET", "/api/v1/analytics/jobs/overview"),
        ("GET", "/api/v1/analytics/jobs/by-source"),
        ("GET", "/api/v1/analytics/jobs/by-company?limit=10"),
        ("GET", "/api/v1/analytics/jobs/current-cycle"),
        ("GET", "/api/v1/analytics/jobs/keywords?limit=10"),
        ("GET", "/api/v1/analytics/jobs/search?keyword=developer"),
    ]
    
    results = []
    
    print(f"🚀 Testing {len(endpoints)} critical endpoints...")
    print(f"📍 Base URL: {base_url}")
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    
    for method, endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing {method:4} {endpoint[:50]:50}", end=" ... ")
        
        result = test_endpoint(method, url)
        results.append((method, endpoint, result))
        
        if result['success']:
            print(f"✅ {result['status']} ({result['time']:.2f}s)")
        else:
            print(f"❌ {result['status']} ({result['time']:.2f}s)")
            if result['error']:
                print(f"     Error: {result['error']}")
    
    # Generate summary
    total = len(results)
    successful = len([r for m, e, r in results if r['success']])
    failed = total - successful
    avg_time = sum(r['time'] for m, e, r in results) / total
    
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Total Endpoints: {total}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {(successful/total)*100:.1f}%")
    print(f"⏱️  Avg Response Time: {avg_time:.2f}s")
    
    if failed > 0:
        print(f"\n❌ FAILED ENDPOINTS:")
        for method, endpoint, result in results:
            if not result['success']:
                print(f"   {method} {endpoint} - Status: {result['status']}")
                if result['error']:
                    print(f"      Error: {result['error']}")
    
    print(f"\n⏰ Completed: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()