#!/usr/bin/env python3
"""
Production API Test Suite
Tests all production endpoints with real data
"""

import asyncio
import json
import time
import aiohttp
from datetime import datetime
from typing import Dict, Any

# Production Configuration
PROD_URL = "https://birjobbackend-ir3e.onrender.com/api/v1"
TEST_DEVICE = "prod-test-device-2025"

class ProductionTester:
    def __init__(self):
        self.base_url = PROD_URL
        self.session = None
        self.passed = 0
        self.failed = 0
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log(self, test: str, status: str, details: str = ""):
        if status == "PASS":
            self.passed += 1
            print(f"✅ {test}")
        else:
            self.failed += 1
            print(f"❌ {test} - {details}")
        
        self.results.append({
            "test": test,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None):
        """Make request to production API"""
        url = f"{self.base_url}{endpoint}"
        try:
            kwargs = {}
            if params:
                kwargs['params'] = params
            if data:
                kwargs['json'] = data
                
            async with self.session.request(method, url, **kwargs) as response:
                try:
                    result = await response.json()
                except:
                    result = await response.text()
                return result, response.status
        except Exception as e:
            return None, str(e)
    
    async def test_health_endpoints(self):
        """Test system health"""
        print("\n🏥 HEALTH ENDPOINTS")
        
        # Main health check
        data, status = await self.request('GET', '/health')
        if status == 200:
            self.log("Health Check", "PASS")
        else:
            self.log("Health Check", "FAIL", f"Status: {status}")
            
        # Scraper status
        data, status = await self.request('GET', '/health/status/scraper')
        if status == 200:
            self.log("Scraper Status", "PASS")
        else:
            self.log("Scraper Status", "FAIL", f"Status: {status}")
    
    async def test_job_endpoints(self):
        """Test job data endpoints"""
        print("\n💼 JOB ENDPOINTS")
        
        # Get jobs
        data, status = await self.request('GET', '/jobs/', params={'limit': 5})
        if status == 200 and isinstance(data, dict) and 'data' in data:
            jobs = data['data'].get('jobs', [])
            self.log("Jobs List", "PASS", f"{len(jobs)} jobs retrieved")
        else:
            self.log("Jobs List", "FAIL", f"Status: {status}")
            
        # Job stats
        data, status = await self.request('GET', '/jobs/stats/summary')
        if status == 200 and isinstance(data, dict) and 'data' in data:
            total = data['data'].get('total_jobs', 0)
            self.log("Job Stats", "PASS", f"{total} total jobs")
        else:
            self.log("Job Stats", "FAIL", f"Status: {status}")
    
    async def test_analytics_endpoints(self):
        """Test analytics endpoints"""
        print("\n📊 ANALYTICS ENDPOINTS")
        
        endpoints = [
            ('/analytics/jobs/overview', 'Overview'),
            ('/analytics/jobs/by-source', 'By Source'),
            ('/analytics/jobs/by-company', 'By Company'),
            ('/analytics/jobs/current-cycle', 'Current Cycle'),
        ]
        
        for endpoint, name in endpoints:
            data, status = await self.request('GET', endpoint)
            if status == 200:
                self.log(f"Analytics {name}", "PASS")
            else:
                self.log(f"Analytics {name}", "FAIL", f"Status: {status}")
                
        # Keywords with correct limit
        data, status = await self.request('GET', '/analytics/jobs/keywords', params={'limit': 10})
        if status == 200:
            self.log("Analytics Keywords", "PASS")
        else:
            self.log("Analytics Keywords", "FAIL", f"Status: {status}")
            
        # Search
        data, status = await self.request('GET', '/analytics/jobs/search', params={'keyword': 'python'})
        if status == 200:
            self.log("Analytics Search", "PASS")
        else:
            self.log("Analytics Search", "FAIL", f"Status: {status}")
    
    async def test_user_unified_system(self):
        """Test unified user system"""
        print("\n👤 UNIFIED USER SYSTEM")
        
        # Create profile
        profile_data = {
            "device_id": TEST_DEVICE,
            "first_name": "Test",
            "last_name": "User",
            "email": "test@production.com",
            "location": "Remote",
            "current_job_title": "Software Engineer",
            "skills": ["python", "react", "fastapi"],
            "match_keywords": ["python", "backend", "api"],
            "min_salary": 100000,
            "max_salary": 150000,
            "job_matches_enabled": True,
            "profile_visibility": "private"
        }
        
        data, status = await self.request('POST', '/users/profile', data=profile_data)
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Create Profile", "PASS")
        else:
            self.log("Create Profile", "FAIL", f"Status: {status}")
            
        # Get profile
        data, status = await self.request('GET', f'/users/profile/{TEST_DEVICE}')
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Get Profile", "PASS")
        else:
            self.log("Get Profile", "FAIL", f"Status: {status}")
    
    async def test_keyword_management(self):
        """Test keyword management system"""
        print("\n🔑 KEYWORD MANAGEMENT")
        
        # Get keywords
        data, status = await self.request('GET', f'/users/{TEST_DEVICE}/profile/keywords')
        if status == 200 and isinstance(data, dict) and data.get('success'):
            keywords = data['data'].get('matchKeywords', [])
            self.log("Get Keywords", "PASS", f"{len(keywords)} keywords")
        else:
            self.log("Get Keywords", "FAIL", f"Status: {status}")
            
        # Add keyword
        add_data = {"keyword": "docker"}
        data, status = await self.request('POST', f'/users/{TEST_DEVICE}/profile/keywords/add', data=add_data)
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Add Keyword", "PASS")
        else:
            self.log("Add Keyword", "FAIL", f"Status: {status}")
            
        # Update keywords
        update_data = {"match_keywords": ["python", "fastapi", "docker", "kubernetes"]}
        data, status = await self.request('POST', f'/users/{TEST_DEVICE}/profile/keywords', data=update_data)
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Update Keywords", "PASS")
        else:
            self.log("Update Keywords", "FAIL", f"Status: {status}")
            
        # Remove keyword
        data, status = await self.request('DELETE', f'/users/{TEST_DEVICE}/profile/keywords/kubernetes')
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Remove Keyword", "PASS")
        else:
            self.log("Remove Keyword", "FAIL", f"Status: {status}")
    
    async def test_job_matching(self):
        """Test intelligent job matching"""
        print("\n🎯 JOB MATCHING")
        
        data, status = await self.request('GET', f'/users/{TEST_DEVICE}/profile/matches', params={'limit': 10})
        if status == 200 and isinstance(data, dict) and data.get('success'):
            matches = data['data'].get('matches', [])
            self.log("Job Matches", "PASS", f"{len(matches)} matches found")
        else:
            self.log("Job Matches", "FAIL", f"Status: {status}")
    
    async def test_device_management(self):
        """Test device registration"""
        print("\n📱 DEVICE MANAGEMENT")
        
        device_data = {
            "device_token": "a" * 64,
            "device_info": {
                "osVersion": "17.0",
                "appVersion": "1.0.0",
                "deviceModel": "iPhone15,2",
                "timezone": "UTC"
            }
        }
        
        data, status = await self.request('POST', '/devices/register', data=device_data)
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Device Registration", "PASS")
        else:
            self.log("Device Registration", "FAIL", f"Status: {status}")
    
    async def test_ai_services(self):
        """Test AI endpoints"""
        print("\n🤖 AI SERVICES")
        
        ai_tests = [
            ("/ai/analyze", "AI Analyze", {
                "message": "Senior Python Developer with FastAPI experience",
                "context": "Job application analysis"
            }),
            ("/ai/job-advice", "AI Job Advice", {
                "message": "Career advice for a Python developer with 3 years experience",
                "context": "Career guidance"
            }),
            ("/ai/resume-review", "AI Resume Review", {
                "message": "Review my resume: Software Engineer, Python, React, 5 years",
                "context": "Resume feedback"
            })
        ]
        
        for endpoint, name, test_data in ai_tests:
            data, status = await self.request('POST', endpoint, data=test_data)
            if status == 200:
                self.log(name, "PASS")
            else:
                self.log(name, "FAIL", f"Status: {status}")
    
    async def test_legacy_endpoints(self):
        """Test legacy compatibility"""
        print("\n🔄 LEGACY COMPATIBILITY")
        
        data, status = await self.request('POST', '/users/profile/sync', 
                                        params={'sourceDeviceId': TEST_DEVICE, 'targetDeviceId': 'target-test'})
        if status == 200 and isinstance(data, dict) and data.get('success'):
            self.log("Profile Sync", "PASS")
        else:
            self.log("Profile Sync", "FAIL", f"Status: {status}")
    
    async def run_all_tests(self):
        """Run comprehensive production tests"""
        print("🚀 PRODUCTION API TESTS")
        print(f"Testing: {self.base_url}")
        print("=" * 50)
        
        start_time = time.time()
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_job_endpoints()
        await self.test_analytics_endpoints()
        await self.test_user_unified_system()
        await self.test_keyword_management()
        await self.test_job_matching()
        await self.test_device_management()
        await self.test_ai_services()
        await self.test_legacy_endpoints()
        
        duration = time.time() - start_time
        total = self.passed + self.failed
        
        # Results summary
        print("\n" + "=" * 50)
        print("📊 PRODUCTION TEST RESULTS")
        print(f"✅ WORKING: {self.passed}")
        print(f"❌ NOT WORKING: {self.failed}")
        print(f"📈 SUCCESS RATE: {(self.passed/total*100):.1f}%")
        print(f"⏱️  DURATION: {duration:.1f}s")
        
        # Save results
        with open('production_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'passed': self.passed,
                    'failed': self.failed,
                    'total': total,
                    'success_rate': round(self.passed/total*100, 1),
                    'duration': round(duration, 1)
                },
                'details': self.results
            }, f, indent=2)
        
        print(f"💾 Results saved to: production_test_results.json")
        return self.failed == 0

async def main():
    """Run production tests"""
    try:
        async with ProductionTester() as tester:
            success = await tester.run_all_tests()
            return 0 if success else 1
    except Exception as e:
        print(f"❌ Test error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)