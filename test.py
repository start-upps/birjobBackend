#!/usr/bin/env python3
"""
Comprehensive API endpoint testing for birjobBackend
Tests all endpoints against the deployed Render URL including:

🏥 Health & Monitoring
📱 Device Management (register, status, delete)
🔍 Keyword Subscriptions (create, list, manage)
💼 Job Matching (matches, unread count, processing)
💼 Job Database API (listing, search, filters, pagination, details, stats)
🔔 Push Notifications (planned)
👑 Admin Endpoints (planned)

Perfect for testing your mobile job app's default page and all functionality.
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://birjobbackend-ir3e.onrender.com"
API_KEY = "birjob-ios-api-key-2024"  # Default API key from .env
TIMEOUT = 30

class APITester:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "birjobBackend-Tester/1.0"
        })
        
        # Test data storage
        self.test_device_id = None
        self.test_device_token = f"test_token_{uuid.uuid4().hex}_{uuid.uuid4().hex}"  # 64+ chars
        self.test_keywords = ["python", "backend", "api"]
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, auth_required: bool = False) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add API key for admin endpoints
        if auth_required:
            if headers is None:
                headers = {}
            headers["X-API-Key"] = self.api_key
        
        try:
            self.log(f"{method} {endpoint}")
            
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=TIMEOUT)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Log response
            status_color = "✅" if 200 <= response.status_code < 300 else "❌"
            self.log(f"{status_color} {response.status_code} - {response.reason}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                return {
                    "status_code": response.status_code,
                    "data": response.json(),
                    "success": 200 <= response.status_code < 300
                }
            else:
                return {
                    "status_code": response.status_code,
                    "data": response.text,
                    "success": 200 <= response.status_code < 300
                }
                
        except requests.exceptions.Timeout:
            self.log("❌ Request timeout", "ERROR")
            return {"status_code": 0, "data": {"error": "timeout"}, "success": False}
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed: {e}", "ERROR")
            return {"status_code": 0, "data": {"error": str(e)}, "success": False}
    
    def test_health_endpoints(self):
        """Test health and monitoring endpoints"""
        self.log("\n🏥 Testing Health & Monitoring Endpoints", "INFO")
        
        # Health check
        result = self.make_request("GET", "/api/v1/health")
        if result["success"]:
            self.log("✅ Health check passed")
        else:
            self.log("❌ Health check failed")
        
        # Metrics (if available)
        result = self.make_request("GET", "/metrics")
        if result["success"]:
            self.log("✅ Metrics endpoint accessible")
        else:
            self.log("ℹ️ Metrics endpoint not available or requires auth")
    
    def test_device_management(self):
        """Test device management endpoints"""
        self.log("\n📱 Testing Device Management Endpoints", "INFO")
        
        # 1. Register device
        device_data = {
            "device_token": self.test_device_token,
            "device_info": {
                "os_version": "17.0",
                "app_version": "1.0.0",
                "device_model": "iPhone15,2",
                "timezone": "UTC"
            }
        }
        
        result = self.make_request("POST", "/api/v1/devices/register", device_data)
        if result["success"]:
            # Handle both possible response formats
            data = result.get("data", {})
            self.test_device_id = data.get("device_id") or data.get("data", {}).get("device_id")
            self.log(f"✅ Device registered with ID: {self.test_device_id}")
            if not self.test_device_id:
                self.log("⚠️ Device ID not found in response, trying to extract from full response")
                self.log(f"Response data: {data}")
        else:
            self.log(f"❌ Device registration failed: {result.get('data', 'Unknown error')}")
            return
        
        # 2. Get device info
        if self.test_device_id:
            result = self.make_request("GET", f"/api/v1/devices/{self.test_device_id}/status")
            if result["success"]:
                self.log("✅ Device info retrieved")
            else:
                self.log("❌ Failed to get device info")
        
        # 3. Update device (skip - no update endpoint available)
        self.log("ℹ️ Device update endpoint not implemented")
    
    def test_keyword_management(self):
        """Test keyword subscription endpoints"""
        self.log("\n🔍 Testing Keyword Management Endpoints", "INFO")
        
        if not self.test_device_id:
            self.log("⚠️ No test device available, testing with manual device registration")
            # Try to register a new device for testing
            test_data = {
                "device_token": f"keyword_test_{uuid.uuid4().hex}_{uuid.uuid4().hex}",
                "device_info": {
                    "os_version": "17.0",
                    "app_version": "1.0.0",
                    "device_model": "iPhone15,2",
                    "timezone": "UTC"
                }
            }
            result = self.make_request("POST", "/api/v1/devices/register", test_data)
            if result["success"]:
                data = result.get("data", {})
                self.test_device_id = data.get("device_id") or data.get("data", {}).get("device_id")
                self.log(f"✅ Created test device: {self.test_device_id}")
            else:
                self.log("❌ Could not create test device, skipping keyword tests")
                return
        
        # 1. Subscribe to keywords
        keyword_data = {
            "device_id": self.test_device_id,
            "keywords": self.test_keywords,
            "sources": ["linkedin", "indeed"],
            "location_filters": {
                "cities": ["Remote"],
                "remote_only": True
            }
        }
        
        result = self.make_request("POST", "/api/v1/keywords", keyword_data)
        if result["success"]:
            self.log(f"✅ Subscribed to keywords: {', '.join(self.test_keywords)}")
        else:
            self.log(f"❌ Failed to subscribe to keywords")
        
        # 2. Get device keywords
        result = self.make_request("GET", f"/api/v1/keywords/{self.test_device_id}")
        if result["success"]:
            subscriptions = result["data"].get("subscriptions", [])
            self.log(f"✅ Retrieved {len(subscriptions)} keyword subscriptions for device")
        else:
            self.log("❌ Failed to get device keywords")
    
    def test_job_matching(self):
        """Test job matching endpoints"""
        self.log("\n💼 Testing Job Matching Endpoints", "INFO")
        
        if not self.test_device_id:
            self.log("⚠️ No test device available, using fallback device registration")
            # Use the same device ID from keyword tests or create new one
            test_data = {
                "device_token": f"jobmatch_test_{uuid.uuid4().hex}_{uuid.uuid4().hex}",
                "device_info": {
                    "os_version": "17.0",
                    "app_version": "1.0.0",
                    "device_model": "iPhone15,2",
                    "timezone": "UTC"
                }
            }
            result = self.make_request("POST", "/api/v1/devices/register", test_data)
            if result["success"]:
                data = result.get("data", {})
                self.test_device_id = data.get("device_id") or data.get("data", {}).get("device_id")
                self.log(f"✅ Created test device for job matching: {self.test_device_id}")
            else:
                self.log("❌ Could not create test device, skipping job matching tests")
                return
        
        # 1. Get job matches
        result = self.make_request("GET", f"/api/v1/matches/{self.test_device_id}")
        if result["success"]:
            matches = result["data"].get("matches", [])
            self.log(f"✅ Retrieved {len(matches)} job matches")
            
            # 2. Mark a job as read (if matches exist)
            if matches:
                match_id = matches[0].get("match_id")
                if match_id:
                    result = self.make_request("POST", f"/api/v1/matches/{match_id}/read?device_id={self.test_device_id}")
                    if result["success"]:
                        self.log("✅ Job match marked as read")
                    else:
                        self.log("❌ Failed to mark job match as read")
        else:
            self.log("❌ Failed to get job matches")
        
        # 3. Get unread count
        result = self.make_request("GET", f"/api/v1/matches/{self.test_device_id}/unread-count")
        if result["success"]:
            unread_count = result["data"].get("unread_count", 0)
            self.log(f"✅ Retrieved unread count: {unread_count}")
        else:
            self.log("❌ Failed to get unread count")
    
    def test_jobs_endpoints(self):
        """Test comprehensive job listing endpoints for mobile app"""
        self.log("\n💼 Testing Job Database Endpoints", "INFO")
        
        # 1. Get job statistics first (most reliable endpoint)
        result = self.make_request("GET", "/api/v1/jobs/stats/summary")
        if result["success"]:
            stats = result["data"]
            total_jobs = stats.get('total_jobs', 0)
            recent_jobs = stats.get('recent_jobs_24h', 0)
            top_companies = stats.get('top_companies', [])
            job_sources = stats.get('job_sources', [])
            
            self.log(f"✅ Job statistics: {total_jobs} total, {recent_jobs} recent (24h)")
            self.log(f"   Top companies: {len(top_companies)} companies tracked")
            self.log(f"   Job sources: {len(job_sources)} sources integrated")
            
            if total_jobs > 0 and top_companies:
                # Store sample data for further testing
                sample_company = top_companies[0]['company'] if top_companies else "ABB"
                sample_job_id = 347120  # Known working job ID
                
                # 2. Test specific job details endpoint
                result = self.make_request("GET", f"/api/v1/jobs/{sample_job_id}")
                if result["success"]:
                    job = result["data"].get("job", {})
                    self.log(f"✅ Job details: '{job.get('title', 'N/A')}' at {job.get('company', 'N/A')}")
                    self.log(f"   Apply link: {job.get('apply_link', 'N/A')[:50]}...")
                else:
                    self.log("❌ Failed to get specific job details")
                
                # 3. Test main jobs listing (default app page) with pagination
                result = self.make_request("GET", "/api/v1/jobs?limit=5&offset=0")
                if result["success"]:
                    jobs = result["data"].get("jobs", [])
                    pagination = result["data"].get("pagination", {})
                    filters = result["data"].get("filters", {})
                    
                    self.log(f"✅ Main job listing: {len(jobs)} jobs displayed")
                    self.log(f"   Pagination: page {pagination.get('current_page', 1)} of {pagination.get('total_pages', 1)}")
                    self.log(f"   Has more: {pagination.get('has_more', False)}")
                    
                    # Test job data structure
                    if jobs:
                        first_job = jobs[0]
                        required_fields = ['id', 'title', 'company', 'apply_link', 'source', 'posted_at']
                        missing_fields = [field for field in required_fields if field not in first_job]
                        if not missing_fields:
                            self.log("✅ Job data structure complete")
                        else:
                            self.log(f"⚠️ Missing job fields: {missing_fields}")
                else:
                    self.log("❌ Main job listing failed")
                
                # 4. Test company filtering
                result = self.make_request("GET", f"/api/v1/jobs?company={sample_company}&limit=3")
                if result["success"]:
                    jobs = result["data"].get("jobs", [])
                    self.log(f"✅ Company filter '{sample_company}': {len(jobs)} results")
                else:
                    self.log(f"❌ Company filter failed for '{sample_company}'")
                
                # 5. Test search functionality
                search_terms = ["developer", "manager", "bank", "sales"]
                for term in search_terms:
                    result = self.make_request("GET", f"/api/v1/jobs?search={term}&limit=3")
                    if result["success"]:
                        jobs = result["data"].get("jobs", [])
                        self.log(f"✅ Search '{term}': {len(jobs)} results")
                        break  # Test one working search term
                    else:
                        continue
                else:
                    self.log("❌ All search terms failed")
                
                # 6. Test source filtering
                if job_sources:
                    sample_source = job_sources[0]['source']
                    result = self.make_request("GET", f"/api/v1/jobs?source={sample_source}&limit=3")
                    if result["success"]:
                        jobs = result["data"].get("jobs", [])
                        self.log(f"✅ Source filter '{sample_source}': {len(jobs)} results")
                    else:
                        self.log(f"❌ Source filter failed for '{sample_source}'")
                
                # 7. Test date filtering (recent jobs)
                result = self.make_request("GET", "/api/v1/jobs?days=7&limit=3")
                if result["success"]:
                    jobs = result["data"].get("jobs", [])
                    self.log(f"✅ Recent jobs (7 days): {len(jobs)} results")
                else:
                    self.log("❌ Date filtering failed")
                
                # 8. Test sorting options
                sort_tests = [
                    ("created_at", "desc", "Latest jobs first"),
                    ("title", "asc", "Alphabetical by title"),
                    ("company", "asc", "Alphabetical by company")
                ]
                
                for sort_by, sort_order, description in sort_tests:
                    result = self.make_request("GET", f"/api/v1/jobs?sort_by={sort_by}&sort_order={sort_order}&limit=2")
                    if result["success"]:
                        jobs = result["data"].get("jobs", [])
                        self.log(f"✅ Sorting ({description}): {len(jobs)} results")
                    else:
                        self.log(f"❌ Sorting failed: {description}")
                
                # 9. Test pagination navigation
                result = self.make_request("GET", "/api/v1/jobs?limit=2&offset=2")
                if result["success"]:
                    pagination = result["data"].get("pagination", {})
                    self.log(f"✅ Pagination navigation: page {pagination.get('current_page', 'N/A')}")
                else:
                    self.log("❌ Pagination navigation failed")
                
                # 10. Test combined filters (realistic mobile app usage)
                result = self.make_request("GET", f"/api/v1/jobs?search=manager&company={sample_company}&limit=5&sort_by=created_at&sort_order=desc")
                if result["success"]:
                    jobs = result["data"].get("jobs", [])
                    filters = result["data"].get("filters", {})
                    self.log(f"✅ Combined filters: {len(jobs)} results")
                    self.log(f"   Applied filters: search={filters.get('search')}, company={filters.get('company')}")
                else:
                    self.log("❌ Combined filters failed")
                
                # 11. Test error handling with invalid job ID
                result = self.make_request("GET", "/api/v1/jobs/999999999")
                if not result["success"] and result["status_code"] == 404:
                    self.log("✅ Error handling: Invalid job ID returns 404")
                else:
                    self.log("❌ Error handling failed for invalid job ID")
                
            else:
                self.log("ℹ️ No jobs in database or no company data - skipping detailed tests")
        else:
            self.log("❌ Failed to get job statistics")

    def test_push_notifications(self):
        """Test push notification endpoints"""
        self.log("\n🔔 Testing Push Notification Endpoints", "INFO")
        self.log("ℹ️ Push notification endpoints not implemented yet")
    
    def test_admin_endpoints(self):
        """Test admin endpoints with API key authentication"""
        self.log("\n👑 Testing Admin Endpoints", "INFO")
        self.log("ℹ️ Admin endpoints not implemented yet")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("\n🧹 Cleaning up test data", "INFO")
        
        if self.test_device_id:
            # Delete test device
            result = self.make_request("DELETE", f"/api/v1/devices/{self.test_device_id}")
            if result["success"]:
                self.log("✅ Test device deleted")
            else:
                self.log("❌ Failed to delete test device")
    
    def run_all_tests(self):
        """Run comprehensive API tests"""
        self.log(f"🚀 Starting comprehensive API tests for: {self.base_url}")
        self.log("=" * 80)
        
        start_time = time.time()
        
        try:
            # Run all test suites
            self.test_health_endpoints()
            self.test_device_management()
            self.test_keyword_management()
            self.test_job_matching()
            self.test_jobs_endpoints()
            self.test_push_notifications()
            self.test_admin_endpoints()
            
        except KeyboardInterrupt:
            self.log("\n⚠️ Tests interrupted by user", "WARNING")
        except Exception as e:
            self.log(f"\n❌ Test suite failed with error: {e}", "ERROR")
        finally:
            # Always try to cleanup
            self.cleanup_test_data()
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.log("=" * 80)
        self.log(f"🏁 Test suite completed in {duration:.2f} seconds")
        self.log("📊 Check the logs above for detailed results")

def main():
    """Main test runner"""
    print("🧪 birjobBackend API Test Suite")
    print("=" * 50)
    print(f"Target URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...")
    print("=" * 50)
    
    # Initialize and run tests
    tester = APITester(BASE_URL, API_KEY)
    tester.run_all_tests()

if __name__ == "__main__":
    main()