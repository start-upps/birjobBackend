#!/usr/bin/env python3
"""
Deployment verification script for iOS Job App Backend
Tests all critical endpoints and analytics functionality
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Base URL - update this to your deployed URL
BASE_URL = "https://birjob-ios-api.onrender.com"  # Update with your actual deployment URL

class DeploymentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = httpx.AsyncClient(timeout=30.0)
        self.test_device_id = "TEST_DEVICE_DEPLOYMENT_123"
        self.session_id = None
        
    async def test_health_check(self):
        """Test health check endpoint"""
        print("🏥 Testing health check...")
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health check passed: {data['status']}")
                print(f"   📊 Services: {data['services']}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    async def test_root_endpoint(self):
        """Test root endpoint"""
        print("🏠 Testing root endpoint...")
        try:
            response = await self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Root endpoint: {data['message']}")
                return True
            else:
                print(f"   ❌ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Root endpoint error: {e}")
            return False
    
    async def test_device_registration(self):
        """Test device registration"""
        print("📱 Testing device registration...")
        try:
            payload = {
                "device_token": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456",
                "device_info": {
                    "osVersion": "17.0",
                    "appVersion": "1.0.0",
                    "deviceModel": "iPhone14,2",
                    "timezone": "America/New_York"
                }
            }
            response = await self.session.post(
                f"{self.base_url}/api/v1/devices/register",
                json=payload
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Device registered: {data['data']['device_id']}")
                return True
            else:
                print(f"   ❌ Device registration failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Device registration error: {e}")
            return False
    
    async def test_user_creation(self):
        """Test email-based user creation"""
        print("👤 Testing user creation...")
        try:
            response = await self.session.get(
                f"{self.base_url}/api/v1/users/by-email",
                params={"email": "deployment.test@example.com"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ User created: {data['data']['id']}")
                return True
            else:
                print(f"   ❌ User creation failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ User creation error: {e}")
            return False
    
    async def test_analytics_overview(self):
        """Test analytics overview"""
        print("📊 Testing analytics overview...")
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/analytics/overview")
            if response.status_code == 200:
                data = response.json()
                metrics = data['data']
                print(f"   ✅ Analytics overview working")
                print(f"   📈 Total users: {metrics['total_users']}")
                print(f"   🔥 Active users (24h): {metrics['active_users_24h']}")
                return True
            else:
                print(f"   ❌ Analytics overview failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Analytics overview error: {e}")
            return False
    
    async def test_session_management(self):
        """Test analytics session management"""
        print("⏱️ Testing session management...")
        try:
            # Start session
            start_payload = {
                "device_id": self.test_device_id,
                "app_version": "1.0.0",
                "os_version": "17.0"
            }
            response = await self.session.post(
                f"{self.base_url}/api/v1/analytics/sessions/start",
                json=start_payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data['data']['session_id']
                print(f"   ✅ Session started: {self.session_id}")
                
                # End session
                end_payload = {
                    "session_id": self.session_id,
                    "actions_count": 5,
                    "jobs_viewed_count": 3,
                    "jobs_saved_count": 1,
                    "searches_performed": 2
                }
                end_response = await self.session.post(
                    f"{self.base_url}/api/v1/analytics/sessions/end",
                    json=end_payload
                )
                
                if end_response.status_code == 200:
                    end_data = end_response.json()
                    print(f"   ✅ Session ended: {end_data['data']['duration_seconds']}s")
                    return True
                else:
                    print(f"   ❌ Session end failed: {end_response.status_code}")
                    return False
            else:
                print(f"   ❌ Session start failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Session management error: {e}")
            return False
    
    async def test_job_engagement(self):
        """Test job engagement tracking"""
        print("💼 Testing job engagement...")
        try:
            payload = {
                "device_id": self.test_device_id,
                "job_id": 99999,
                "job_title": "Deployment Test Engineer",
                "job_company": "Test Corp",
                "job_source": "deployment_test",
                "view_duration_seconds": 45
            }
            response = await self.session.post(
                f"{self.base_url}/api/v1/analytics/jobs/engagement",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Job engagement tracked: score {data['data']['engagement_score']}")
                return True
            else:
                print(f"   ❌ Job engagement failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Job engagement error: {e}")
            return False
    
    async def test_search_analytics(self):
        """Test search analytics"""
        print("🔍 Testing search analytics...")
        try:
            payload = {
                "device_id": self.test_device_id,
                "search_query": "deployment test engineer",
                "filters_applied": {
                    "location": "remote",
                    "test": "deployment"
                }
            }
            response = await self.session.post(
                f"{self.base_url}/api/v1/analytics/search/start",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Search analytics tracked: {data['data']['search_id']}")
                return True
            else:
                print(f"   ❌ Search analytics failed: {response.status_code}")
                print(f"   📄 Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Search analytics error: {e}")
            return False
    
    async def test_realtime_analytics(self):
        """Test real-time analytics"""
        print("⚡ Testing real-time analytics...")
        try:
            response = await self.session.get(f"{self.base_url}/api/v1/analytics/realtime")
            if response.status_code == 200:
                data = response.json()
                metrics = data['data']
                print(f"   ✅ Real-time analytics working")
                print(f"   👥 Active users now: {metrics['active_users_now']}")
                print(f"   📈 Sessions last hour: {metrics['sessions_last_hour']}")
                return True
            else:
                print(f"   ❌ Real-time analytics failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Real-time analytics error: {e}")
            return False
    
    async def test_job_operations(self):
        """Test job save/unsave operations"""
        print("💾 Testing job operations...")
        try:
            # Save job
            save_payload = {
                "device_id": self.test_device_id,
                "job_id": 99999
            }
            save_response = await self.session.post(
                f"{self.base_url}/api/v1/jobs/save",
                json=save_payload
            )
            
            if save_response.status_code == 200:
                print("   ✅ Job save working")
                
                # Get saved jobs
                get_response = await self.session.get(
                    f"{self.base_url}/api/v1/jobs/saved/{self.test_device_id}"
                )
                
                if get_response.status_code == 200:
                    data = get_response.json()
                    print(f"   ✅ Get saved jobs working: {len(data['data']['saved_jobs'])} jobs")
                    return True
                else:
                    print(f"   ❌ Get saved jobs failed: {get_response.status_code}")
                    return False
            else:
                print(f"   ❌ Job save failed: {save_response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Job operations error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all deployment tests"""
        print("🚀 Starting deployment verification tests...")
        print(f"🌐 Testing URL: {self.base_url}")
        print("=" * 60)
        
        tests = [
            ("Root Endpoint", self.test_root_endpoint),
            ("Health Check", self.test_health_check),
            ("Device Registration", self.test_device_registration),
            ("User Creation", self.test_user_creation),
            ("Analytics Overview", self.test_analytics_overview),
            ("Session Management", self.test_session_management),
            ("Job Engagement", self.test_job_engagement),
            ("Search Analytics", self.test_search_analytics),
            ("Real-time Analytics", self.test_realtime_analytics),
            ("Job Operations", self.test_job_operations),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
                print()  # Add spacing between tests
            except Exception as e:
                print(f"   ❌ {test_name} crashed: {e}")
                results.append((test_name, False))
                print()
        
        # Summary
        print("=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("=" * 60)
        print(f"📊 Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Deployment is successful!")
            return True
        else:
            print("⚠️ Some tests failed. Check the deployment.")
            return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

async def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    async with DeploymentTester(base_url) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())