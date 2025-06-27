#!/usr/bin/env python3
"""
Comprehensive API Endpoint Tester for BirJob Backend
Tests all 31 endpoints and generates detailed report
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    endpoint: str
    method: str
    status_code: int
    success: bool
    response_time: float
    error_message: str = ""
    response_data: Dict = None

class BirJobAPITester:
    def __init__(self, base_url: str = "https://birjobbackend-ir3e.onrender.com"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.test_device_id = str(uuid.uuid4())
        self.test_job_id = None
        self.test_subscription_id = None
        self.test_match_id = None
        
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[int, Dict, float]:
        """Make HTTP request and return status, response, and timing"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    response_time = time.time() - start_time
                    try:
                        data = await response.json()
                    except:
                        data = {"text": await response.text()}
                    return response.status, data, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return 0, {"error": str(e)}, response_time

    def add_result(self, endpoint: str, method: str, status: int, data: Dict, response_time: float):
        """Add test result to results list"""
        success = 200 <= status < 300
        error_msg = ""
        
        if not success:
            if isinstance(data, dict):
                error_msg = data.get("detail", data.get("error", str(data)))
            else:
                error_msg = str(data)
        
        result = TestResult(
            endpoint=endpoint,
            method=method,
            status_code=status,
            success=success,
            response_time=response_time,
            error_message=error_msg,
            response_data=data if success else None
        )
        self.results.append(result)

    async def test_health_endpoints(self):
        """Test all health endpoints"""
        print("Testing Health Endpoints...")
        
        # Basic health check
        status, data, time_taken = await self.make_request("GET", "/api/v1/health")
        self.add_result("/api/v1/health", "GET", status, data, time_taken)
        
        # Scraper status
        status, data, time_taken = await self.make_request("GET", "/api/v1/health/status/scraper")
        self.add_result("/api/v1/health/status/scraper", "GET", status, data, time_taken)
        
        # Scheduler status
        status, data, time_taken = await self.make_request("GET", "/api/v1/health/scheduler-status")
        self.add_result("/api/v1/health/scheduler-status", "GET", status, data, time_taken)
        
        # Check user tables
        status, data, time_taken = await self.make_request("GET", "/api/v1/health/check-user-tables")
        self.add_result("/api/v1/health/check-user-tables", "GET", status, data, time_taken)
        
        # DB debug
        status, data, time_taken = await self.make_request("GET", "/api/v1/health/db-debug")
        self.add_result("/api/v1/health/db-debug", "GET", status, data, time_taken)
        
        # Trigger matching (POST)
        status, data, time_taken = await self.make_request("POST", "/api/v1/health/trigger-matching")
        self.add_result("/api/v1/health/trigger-matching", "POST", status, data, time_taken)
        
        # Create user tables (POST)
        status, data, time_taken = await self.make_request("POST", "/api/v1/health/create-user-tables")
        self.add_result("/api/v1/health/create-user-tables", "POST", status, data, time_taken)

    async def test_jobs_endpoints(self):
        """Test all jobs endpoints"""
        print("Testing Jobs Endpoints...")
        
        # Get jobs list
        status, data, time_taken = await self.make_request("GET", "/api/v1/jobs/?limit=5")
        self.add_result("/api/v1/jobs/", "GET", status, data, time_taken)
        
        # Extract a job ID for other tests
        if status == 200 and data.get("jobs"):
            self.test_job_id = data["jobs"][0].get("id")
        
        # Get specific job (if we have a job ID)
        if self.test_job_id:
            status, data, time_taken = await self.make_request("GET", f"/api/v1/jobs/{self.test_job_id}")
            self.add_result(f"/api/v1/jobs/{self.test_job_id}", "GET", status, data, time_taken)
        else:
            # Test with a dummy ID
            status, data, time_taken = await self.make_request("GET", "/api/v1/jobs/999999")
            self.add_result("/api/v1/jobs/{job_id}", "GET", status, data, time_taken)
        
        # Get jobs stats
        status, data, time_taken = await self.make_request("GET", "/api/v1/jobs/stats/summary")
        self.add_result("/api/v1/jobs/stats/summary", "GET", status, data, time_taken)

    async def test_analytics_endpoints(self):
        """Test all analytics endpoints"""
        print("Testing Analytics Endpoints...")
        
        # Overview
        status, data, time_taken = await self.make_request("GET", "/api/v1/analytics/jobs/overview")
        self.add_result("/api/v1/analytics/jobs/overview", "GET", status, data, time_taken)
        
        # By source
        status, data, time_taken = await self.make_request("GET", "/api/v1/analytics/jobs/by-source")
        self.add_result("/api/v1/analytics/jobs/by-source", "GET", status, data, time_taken)
        
        # By company
        status, data, time_taken = await self.make_request("GET", "/api/v1/analytics/jobs/by-company?limit=10")
        self.add_result("/api/v1/analytics/jobs/by-company", "GET", status, data, time_taken)
        
        # Current cycle
        status, data, time_taken = await self.make_request("GET", "/api/v1/analytics/jobs/current-cycle")
        self.add_result("/api/v1/analytics/jobs/current-cycle", "GET", status, data, time_taken)
        
        # Keywords
        status, data, time_taken = await self.make_request("GET", "/api/v1/analytics/jobs/keywords?limit=10")
        self.add_result("/api/v1/analytics/jobs/keywords", "GET", status, data, time_taken)
        
        # Search
        status, data, time_taken = await self.make_request("GET", "/api/v1/analytics/jobs/search?keyword=developer")
        self.add_result("/api/v1/analytics/jobs/search", "GET", status, data, time_taken)

    async def test_devices_endpoints(self):
        """Test device endpoints"""
        print("Testing Device Endpoints...")
        
        # Register device
        device_data = {
            "device_token": f"test_token_{int(time.time())}",
            "device_info": {
                "model": "iPhone14",
                "os_version": "17.0",
                "app_version": "1.0.0"
            }
        }
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/devices/register",
            json=device_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/devices/register", "POST", status, data, time_taken)
        
        # Get device status
        status, data, time_taken = await self.make_request("GET", f"/api/v1/devices/{self.test_device_id}/status")
        self.add_result(f"/api/v1/devices/{self.test_device_id}/status", "GET", status, data, time_taken)
        
        # Delete device
        status, data, time_taken = await self.make_request("DELETE", f"/api/v1/devices/{self.test_device_id}")
        self.add_result(f"/api/v1/devices/{self.test_device_id}", "DELETE", status, data, time_taken)

    async def test_keywords_endpoints(self):
        """Test keyword endpoints"""
        print("Testing Keywords Endpoints...")
        
        # Create keyword subscription
        keyword_data = {
            "device_id": self.test_device_id,
            "keywords": ["python", "developer"],
            "sources": ["Djinni"],
            "location_filters": []
        }
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/keywords",
            json=keyword_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/keywords", "POST", status, data, time_taken)
        
        if status == 200 and data.get("subscription_id"):
            self.test_subscription_id = data["subscription_id"]
        
        # Get keywords for device
        status, data, time_taken = await self.make_request("GET", f"/api/v1/keywords/{self.test_device_id}")
        self.add_result(f"/api/v1/keywords/{self.test_device_id}", "GET", status, data, time_taken)
        
        # Update keywords (if we have subscription ID)
        if self.test_subscription_id:
            update_data = {
                "device_id": self.test_device_id,
                "keywords": ["python", "developer", "backend"],
                "sources": ["Djinni", "Glorri"],
                "location_filters": []
            }
            status, data, time_taken = await self.make_request(
                "PUT", f"/api/v1/keywords/{self.test_subscription_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            self.add_result(f"/api/v1/keywords/{self.test_subscription_id}", "PUT", status, data, time_taken)
            
            # Delete keywords
            status, data, time_taken = await self.make_request(
                "DELETE", f"/api/v1/keywords/{self.test_subscription_id}?device_id={self.test_device_id}"
            )
            self.add_result(f"/api/v1/keywords/{self.test_subscription_id}", "DELETE", status, data, time_taken)
        else:
            # Test with dummy IDs
            status, data, time_taken = await self.make_request("PUT", f"/api/v1/keywords/{str(uuid.uuid4())}", json=keyword_data)
            self.add_result("/api/v1/keywords/{subscription_id}", "PUT", status, data, time_taken)
            
            status, data, time_taken = await self.make_request("DELETE", f"/api/v1/keywords/{str(uuid.uuid4())}?device_id={self.test_device_id}")
            self.add_result("/api/v1/keywords/{subscription_id}", "DELETE", status, data, time_taken)

    async def test_matches_endpoints(self):
        """Test match endpoints"""
        print("Testing Matches Endpoints...")
        
        # Get matches for device
        status, data, time_taken = await self.make_request("GET", f"/api/v1/matches/{self.test_device_id}?limit=5")
        self.add_result(f"/api/v1/matches/{self.test_device_id}", "GET", status, data, time_taken)
        
        # Get unread count
        status, data, time_taken = await self.make_request("GET", f"/api/v1/matches/{self.test_device_id}/unread-count")
        self.add_result(f"/api/v1/matches/{self.test_device_id}/unread-count", "GET", status, data, time_taken)
        
        # Mark match as read (test with dummy match ID)
        dummy_match_id = str(uuid.uuid4())
        status, data, time_taken = await self.make_request(
            "POST", f"/api/v1/matches/{dummy_match_id}/read?device_id={self.test_device_id}"
        )
        self.add_result(f"/api/v1/matches/{dummy_match_id}/read", "POST", status, data, time_taken)

    async def test_ai_endpoints(self):
        """Test AI endpoints"""
        print("Testing AI Endpoints...")
        
        # Basic AI analyze
        ai_data = {"message": "What are the best programming languages for backend development?"}
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/ai/analyze",
            json=ai_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/ai/analyze", "POST", status, data, time_taken)
        
        # Job advice
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/ai/job-advice",
            json=ai_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/ai/job-advice", "POST", status, data, time_taken)
        
        # Resume review
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/ai/resume-review",
            json=ai_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/ai/resume-review", "POST", status, data, time_taken)
        
        # Job recommendations
        rec_data = {"deviceId": self.test_device_id, "limit": 5}
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/ai/job-recommendations",
            json=rec_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/ai/job-recommendations", "POST", status, data, time_taken)
        
        # Job match analysis
        if self.test_job_id:
            match_data = {"deviceId": self.test_device_id, "jobId": self.test_job_id}
            status, data, time_taken = await self.make_request(
                "POST", "/api/v1/ai/job-match-analysis",
                json=match_data,
                headers={"Content-Type": "application/json"}
            )
            self.add_result("/api/v1/ai/job-match-analysis", "POST", status, data, time_taken)
        else:
            # Test with dummy job ID
            match_data = {"deviceId": self.test_device_id, "jobId": 999999}
            status, data, time_taken = await self.make_request(
                "POST", "/api/v1/ai/job-match-analysis",
                json=match_data,
                headers={"Content-Type": "application/json"}
            )
            self.add_result("/api/v1/ai/job-match-analysis", "POST", status, data, time_taken)

    async def test_users_endpoints(self):
        """Test user endpoints"""
        print("Testing Users Endpoints...")
        
        # Create user profile
        profile_data = {
            "device_id": self.test_device_id,
            "full_name": "Test User",
            "email": f"test{int(time.time())}@example.com",
            "skills": ["Python", "FastAPI"],
            "experience_level": "mid",
            "location": "Baku",
            "resume": {"summary": "Test summary"}
        }
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/users/profile",
            json=profile_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/users/profile", "POST", status, data, time_taken)
        
        # Get user profile
        status, data, time_taken = await self.make_request("GET", f"/api/v1/users/profile/{self.test_device_id}")
        self.add_result(f"/api/v1/users/profile/{self.test_device_id}", "GET", status, data, time_taken)
        
        # Save job
        if self.test_job_id:
            save_data = {"jobId": self.test_job_id, "notes": "Test save"}
            status, data, time_taken = await self.make_request(
                "POST", f"/api/v1/users/{self.test_device_id}/saved-jobs",
                json=save_data,
                headers={"Content-Type": "application/json"}
            )
            self.add_result(f"/api/v1/users/{self.test_device_id}/saved-jobs", "POST", status, data, time_taken)
        
        # Get saved jobs
        status, data, time_taken = await self.make_request("GET", f"/api/v1/users/{self.test_device_id}/saved-jobs")
        self.add_result(f"/api/v1/users/{self.test_device_id}/saved-jobs", "GET", status, data, time_taken)
        
        # Delete saved job
        if self.test_job_id:
            status, data, time_taken = await self.make_request(
                "DELETE", f"/api/v1/users/{self.test_device_id}/saved-jobs/{self.test_job_id}"
            )
            self.add_result(f"/api/v1/users/{self.test_device_id}/saved-jobs/{self.test_job_id}", "DELETE", status, data, time_taken)
        
        # Get user analytics
        status, data, time_taken = await self.make_request("GET", f"/api/v1/users/{self.test_device_id}/analytics")
        self.add_result(f"/api/v1/users/{self.test_device_id}/analytics", "GET", status, data, time_taken)
        
        # Record job view
        if self.test_job_id:
            view_data = {
                "jobId": self.test_job_id,
                "viewDuration": 30,
                "source": "app",
                "timestamp": datetime.now().isoformat()
            }
            status, data, time_taken = await self.make_request(
                "POST", f"/api/v1/users/{self.test_device_id}/job-views",
                json=view_data,
                headers={"Content-Type": "application/json"}
            )
            self.add_result(f"/api/v1/users/{self.test_device_id}/job-views", "POST", status, data, time_taken)
        
        # Get applications
        status, data, time_taken = await self.make_request("GET", f"/api/v1/users/{self.test_device_id}/applications")
        self.add_result(f"/api/v1/users/{self.test_device_id}/applications", "GET", status, data, time_taken)
        
        # Profile sync
        sync_data = {"sourceDeviceId": self.test_device_id, "targetDeviceId": str(uuid.uuid4())}
        status, data, time_taken = await self.make_request(
            "POST", "/api/v1/users/profile/sync",
            json=sync_data,
            headers={"Content-Type": "application/json"}
        )
        self.add_result("/api/v1/users/profile/sync", "POST", status, data, time_taken)

    async def run_all_tests(self):
        """Run all endpoint tests"""
        print(f"🚀 Starting comprehensive API test for BirJob Backend")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🆔 Test Device ID: {self.test_device_id}")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_jobs_endpoints()
        await self.test_analytics_endpoints()
        await self.test_devices_endpoints()
        await self.test_keywords_endpoints()
        await self.test_matches_endpoints()
        await self.test_ai_endpoints()
        await self.test_users_endpoints()
        
        self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        total_endpoints = len(self.results)
        successful = len([r for r in self.results if r.success])
        failed = total_endpoints - successful
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE API TEST REPORT")
        print("=" * 80)
        
        print(f"📈 SUMMARY:")
        print(f"   Total Endpoints Tested: {total_endpoints}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {(successful/total_endpoints)*100:.1f}%")
        
        # Calculate average response time
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results)
        print(f"   ⏱️  Average Response Time: {avg_response_time:.2f}s")
        
        print(f"\n🔍 DETAILED RESULTS:")
        print("-" * 80)
        
        # Group by status
        success_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        if success_results:
            print(f"\n✅ SUCCESSFUL ENDPOINTS ({len(success_results)}):")
            for result in success_results:
                print(f"   {result.method:6} {result.endpoint:45} | {result.status_code} | {result.response_time:.2f}s")
        
        if failed_results:
            print(f"\n❌ FAILED ENDPOINTS ({len(failed_results)}):")
            for result in failed_results:
                print(f"   {result.method:6} {result.endpoint:45} | {result.status_code} | {result.response_time:.2f}s")
                if result.error_message:
                    print(f"         Error: {result.error_message}")
        
        # Performance analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        print("-" * 40)
        fastest = min(self.results, key=lambda x: x.response_time)
        slowest = max(self.results, key=lambda x: x.response_time)
        print(f"   Fastest: {fastest.endpoint} ({fastest.response_time:.2f}s)")
        print(f"   Slowest: {slowest.endpoint} ({slowest.response_time:.2f}s)")
        
        # Endpoint categories analysis
        print(f"\n📋 ENDPOINT CATEGORIES:")
        print("-" * 40)
        categories = {}
        for result in self.results:
            category = result.endpoint.split('/')[3] if len(result.endpoint.split('/')) > 3 else 'root'
            if category not in categories:
                categories[category] = {'total': 0, 'success': 0}
            categories[category]['total'] += 1
            if result.success:
                categories[category]['success'] += 1
        
        for category, stats in categories.items():
            success_rate = (stats['success'] / stats['total']) * 100
            print(f"   {category.capitalize():12} | {stats['success']:2}/{stats['total']:2} | {success_rate:5.1f}%")
        
        print(f"\n📄 RECOMMENDATIONS:")
        print("-" * 40)
        if failed > 0:
            print(f"   • {failed} endpoints need attention")
            print(f"   • Focus on failed endpoints for debugging")
        if avg_response_time > 2.0:
            print(f"   • Average response time is high ({avg_response_time:.2f}s)")
            print(f"   • Consider performance optimization")
        if successful == total_endpoints:
            print(f"   • 🎉 All endpoints are working perfectly!")
            print(f"   • API is production ready")
        
        print(f"\n⏰ Test completed at: {datetime.now().isoformat()}")
        print("=" * 80)

async def main():
    """Main function to run the test suite"""
    tester = BirJobAPITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())