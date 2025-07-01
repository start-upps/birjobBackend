#!/usr/bin/env python3
"""
Comprehensive API Test Suite for BirJob Backend
Tests all endpoints with real API calls and validates responses
"""

import asyncio
import httpx
import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import sys

# API Configuration
BASE_URL = "https://birjobbackend-ir3e.onrender.com/api/v1"
API_KEY = "birjob-ios-api-key-2024"
TIMEOUT = 30.0

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
            "User-Agent": "BirJob-API-Tester/1.0"
        }
        self.test_device_id = None
        self.test_user_id = None
        self.test_data = {}
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "test_details": []
        }

    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {},
                    "headers": dict(response.headers),
                    "success": 200 <= response.status_code < 300
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "data": {"error": str(e)},
                    "headers": {},
                    "success": False,
                    "exception": str(e)
                }

    def log_test(self, test_name: str, success: bool, details: str, response: Dict = None):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed"] += 1
            status = "✅ PASS"
        else:
            self.results["failed"] += 1
            status = "❌ FAIL"
            self.results["errors"].append(f"{test_name}: {details}")
        
        test_detail = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if response:
            test_detail["response_code"] = response.get("status_code")
            test_detail["response_data"] = response.get("data")
        
        self.results["test_details"].append(test_detail)
        print(f"{status} {test_name}: {details}")

    # ================== DEVICE MANAGEMENT TESTS ==================

    async def test_device_registration(self):
        """Test device registration endpoint"""
        test_name = "Device Registration"
        
        device_token = f"test_device_token_{uuid.uuid4().hex[:16]}"
        test_data = {
            "device_token": device_token,
            "device_info": {
                "os_version": "17.2",
                "app_version": "1.0.0",
                "device_model": "iPhone15,2",
                "timezone": "America/Los_Angeles"
            }
        }
        
        response = await self.make_request("POST", "/devices/register", test_data)
        
        if response["success"] and response["status_code"] == 200:
            if "data" in response["data"] and "device_id" in response["data"]["data"]:
                self.test_device_id = response["data"]["data"]["device_id"]
                self.test_user_id = response["data"]["data"].get("user_id")
                self.test_data["device_token"] = device_token
                self.log_test(test_name, True, f"Device registered successfully, ID: {self.test_device_id}", response)
            else:
                self.log_test(test_name, False, "Response missing device_id", response)
        else:
            self.log_test(test_name, False, f"Registration failed: {response['data']}", response)

    async def test_device_status(self):
        """Test device status endpoint"""
        test_name = "Device Status Check"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available from registration")
            return
        
        response = await self.make_request("GET", f"/devices/{self.test_device_id}/status")
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "data" in data and "device_id" in data["data"]:
                self.log_test(test_name, True, "Device status retrieved successfully", response)
            else:
                self.log_test(test_name, False, "Invalid device status response", response)
        else:
            self.log_test(test_name, False, f"Status check failed: {response['data']}", response)

    # ================== USER PROFILE TESTS ==================

    async def test_user_profile_creation(self):
        """Test user profile creation/update"""
        test_name = "User Profile Creation"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available")
            return
        
        profile_data = {
            "deviceId": self.test_device_id,
            "profile": {
                "name": "Test User",
                "email": "test@example.com",
                "skills": ["Swift", "iOS", "SwiftUI"],
                "experience": "3-5 years",
                "location": "San Francisco, CA",
                "resume_url": "https://example.com/resume",
                "preferences": {
                    "remote_work": True,
                    "salary_min": 100000,
                    "job_types": ["full-time"]
                }
            }
        }
        
        response = await self.make_request("POST", "/users/profile", profile_data)
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "User profile created successfully", response)
        else:
            self.log_test(test_name, False, f"Profile creation failed: {response['data']}", response)

    async def test_user_profile_retrieval(self):
        """Test user profile retrieval"""
        test_name = "User Profile Retrieval"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available")
            return
        
        response = await self.make_request("GET", f"/users/profile/{self.test_device_id}")
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "User profile retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Profile retrieval failed: {response['data']}", response)

    # ================== JOB MANAGEMENT TESTS ==================

    async def test_jobs_listing(self):
        """Test jobs listing with pagination"""
        test_name = "Jobs Listing"
        
        params = {
            "limit": 5,
            "offset": 0,
            "search": "developer"
        }
        
        response = await self.make_request("GET", "/jobs/", params=params)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "data" in data and "jobs" in data["data"]:
                jobs_count = len(data["data"]["jobs"])
                self.log_test(test_name, True, f"Retrieved {jobs_count} jobs successfully", response)
            else:
                self.log_test(test_name, False, "Invalid jobs response format", response)
        else:
            self.log_test(test_name, False, f"Jobs listing failed: {response['data']}", response)

    async def test_job_stats(self):
        """Test job statistics endpoint"""
        test_name = "Job Statistics"
        
        response = await self.make_request("GET", "/jobs/stats/summary")
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "data" in data and "total_jobs" in data["data"]:
                total_jobs = data["data"]["total_jobs"]
                self.log_test(test_name, True, f"Job stats retrieved: {total_jobs} total jobs", response)
            else:
                self.log_test(test_name, False, "Invalid job stats response", response)
        else:
            self.log_test(test_name, False, f"Job stats failed: {response['data']}", response)

    async def test_job_search(self):
        """Test job search functionality"""
        test_name = "Job Search"
        
        params = {
            "search": "iOS",
            "limit": 3,
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        response = await self.make_request("GET", "/jobs/", params=params)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "data" in data and "jobs" in data["data"]:
                self.log_test(test_name, True, f"Search returned {len(data['data']['jobs'])} results", response)
            else:
                self.log_test(test_name, False, "Invalid search response", response)
        else:
            self.log_test(test_name, False, f"Job search failed: {response['data']}", response)

    # ================== AI FEATURES TESTS ==================

    async def test_ai_analyze(self):
        """Test AI analysis endpoint"""
        test_name = "AI Analysis"
        
        ai_data = {
            "message": "What skills are most in demand for iOS developers in 2025?"
        }
        
        response = await self.make_request("POST", "/ai/analyze", ai_data)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "response" in data:
                self.log_test(test_name, True, "AI analysis completed successfully", response)
            else:
                self.log_test(test_name, False, "Invalid AI response format", response)
        else:
            self.log_test(test_name, False, f"AI analysis failed: {response['data']}", response)

    async def test_ai_job_advice(self):
        """Test AI job advice endpoint"""
        test_name = "AI Job Advice"
        
        advice_data = {
            "message": "How can I improve my iOS developer resume for senior positions?"
        }
        
        response = await self.make_request("POST", "/ai/job-advice", advice_data)
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "response" in data:
                self.log_test(test_name, True, "AI job advice generated successfully", response)
            else:
                self.log_test(test_name, False, "Invalid AI advice response", response)
        else:
            self.log_test(test_name, False, f"AI job advice failed: {response['data']}", response)

    # ================== KEYWORD MANAGEMENT TESTS ==================

    async def test_keyword_subscription(self):
        """Test keyword subscription"""
        test_name = "Keyword Subscription"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available")
            return
        
        keyword_data = {
            "device_id": self.test_device_id,
            "keywords": ["Swift", "iOS Developer", "Mobile"],
            "sources": ["linkedin", "indeed"]
        }
        
        response = await self.make_request("POST", "/keywords", keyword_data)
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "Keywords subscribed successfully", response)
        else:
            self.log_test(test_name, False, f"Keyword subscription failed: {response['data']}", response)

    async def test_keyword_retrieval(self):
        """Test keyword retrieval"""
        test_name = "Keyword Retrieval"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available")
            return
        
        response = await self.make_request("GET", f"/keywords/{self.test_device_id}")
        
        if response["success"]:
            self.log_test(test_name, True, "Keywords retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Keyword retrieval failed: {response['data']}", response)

    # ================== ANALYTICS TESTS ==================

    async def test_analytics_overview(self):
        """Test analytics overview"""
        test_name = "Analytics Overview"
        
        response = await self.make_request("GET", "/analytics/jobs/overview")
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "Analytics overview retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Analytics overview failed: {response['data']}", response)

    async def test_analytics_by_source(self):
        """Test analytics by source"""
        test_name = "Analytics by Source"
        
        response = await self.make_request("GET", "/analytics/jobs/by-source")
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "Analytics by source retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Analytics by source failed: {response['data']}", response)

    async def test_analytics_keywords(self):
        """Test popular keywords analytics"""
        test_name = "Popular Keywords Analytics"
        
        params = {"limit": 10}
        response = await self.make_request("GET", "/analytics/jobs/keywords", params=params)
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "Keywords analytics retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Keywords analytics failed: {response['data']}", response)

    # ================== HEALTH CHECK TESTS ==================

    async def test_health_check(self):
        """Test system health check"""
        test_name = "Health Check"
        
        response = await self.make_request("GET", "/health")
        
        if response["success"] and response["status_code"] == 200:
            data = response["data"]
            if "status" in data and data["status"] == "healthy":
                self.log_test(test_name, True, "System is healthy", response)
            else:
                self.log_test(test_name, False, f"System health issue: {data}", response)
        else:
            self.log_test(test_name, False, f"Health check failed: {response['data']}", response)

    async def test_scraper_status(self):
        """Test scraper status"""
        test_name = "Scraper Status"
        
        response = await self.make_request("GET", "/health/status/scraper")
        
        if response["success"] and response["status_code"] == 200:
            self.log_test(test_name, True, "Scraper status retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Scraper status failed: {response['data']}", response)

    # ================== MATCHES TESTS ==================

    async def test_job_matches(self):
        """Test job matches endpoint"""
        test_name = "Job Matches"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available")
            return
        
        params = {"limit": 5}
        response = await self.make_request("GET", f"/matches/{self.test_device_id}", params=params)
        
        if response["success"]:
            self.log_test(test_name, True, "Job matches retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Job matches failed: {response['data']}", response)

    async def test_unread_matches_count(self):
        """Test unread matches count"""
        test_name = "Unread Matches Count"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available")
            return
        
        response = await self.make_request("GET", f"/matches/{self.test_device_id}/unread-count")
        
        if response["success"]:
            self.log_test(test_name, True, "Unread matches count retrieved successfully", response)
        else:
            self.log_test(test_name, False, f"Unread matches count failed: {response['data']}", response)

    # ================== CLEANUP TESTS ==================

    async def test_device_cleanup(self):
        """Test device unregistration (cleanup)"""
        test_name = "Device Cleanup"
        
        if not self.test_device_id:
            self.log_test(test_name, False, "No device ID available for cleanup")
            return
        
        response = await self.make_request("DELETE", f"/devices/{self.test_device_id}")
        
        if response["success"]:
            self.log_test(test_name, True, "Device unregistered successfully", response)
        else:
            self.log_test(test_name, False, f"Device cleanup failed: {response['data']}", response)

    # ================== MAIN TEST RUNNER ==================

    async def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive API Test Suite")
        print(f"📡 Testing API: {self.base_url}")
        print(f"⏰ Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 80)
        
        test_groups = [
            ("Device Management", [
                self.test_device_registration,
                self.test_device_status,
            ]),
            ("User Profile Management", [
                self.test_user_profile_creation,
                self.test_user_profile_retrieval,
            ]),
            ("Job Management", [
                self.test_jobs_listing,
                self.test_job_stats,
                self.test_job_search,
            ]),
            ("AI Features", [
                self.test_ai_analyze,
                self.test_ai_job_advice,
            ]),
            ("Keyword Management", [
                self.test_keyword_subscription,
                self.test_keyword_retrieval,
            ]),
            ("Analytics", [
                self.test_analytics_overview,
                self.test_analytics_by_source,
                self.test_analytics_keywords,
            ]),
            ("Health & Monitoring", [
                self.test_health_check,
                self.test_scraper_status,
            ]),
            ("Job Matching", [
                self.test_job_matches,
                self.test_unread_matches_count,
            ]),
            ("Cleanup", [
                self.test_device_cleanup,
            ])
        ]
        
        for group_name, tests in test_groups:
            print(f"\n📋 {group_name} Tests")
            print("-" * 40)
            
            for test_func in tests:
                try:
                    await test_func()
                except Exception as e:
                    self.log_test(test_func.__name__, False, f"Exception: {str(e)}")
                
                # Small delay between tests
                await asyncio.sleep(0.5)
        
        # Print final results
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n🚨 FAILED TESTS ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"  • {error}")
        
        print(f"\n🔧 Test Data Generated:")
        if self.test_device_id:
            print(f"  • Device ID: {self.test_device_id}")
        if self.test_user_id:
            print(f"  • User ID: {self.test_user_id}")
        if self.test_data:
            print(f"  • Additional Data: {len(self.test_data)} items")
        
        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! API is functioning correctly.")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")

    def export_test_results(self, format_type: str = "json"):
        """Export test results in different formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "json":
            filename = f"api_test_results_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
        
        elif format_type == "csv":
            import csv
            filename = f"api_test_results_{timestamp}.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Test Name', 'Status', 'Details', 'Response Code', 'Timestamp'])
                for test in self.results["test_details"]:
                    writer.writerow([
                        test['test'],
                        test['status'],
                        test['details'],
                        test.get('response_code', 'N/A'),
                        test['timestamp']
                    ])
        
        print(f"📄 Results exported to: {filename}")
        return filename

async def main():
    """Main function to run tests"""
    tester = APITester()
    
    try:
        await tester.run_all_tests()
        
        # Export results in multiple formats
        tester.export_test_results("json")
        
        # Exit with proper code
        sys.exit(0 if tester.results["failed"] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Fatal error during testing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if required packages are available
    try:
        import httpx
    except ImportError:
        print("❌ Error: httpx package not found. Install with: pip install httpx")
        sys.exit(1)
    
    print("🧪 BirJob API Comprehensive Test Suite")
    print("⚡ Starting async test runner...")
    
    # Run the async tests
    asyncio.run(main())