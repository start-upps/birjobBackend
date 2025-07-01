#!/usr/bin/env python3
"""
Production Profile Recovery Test Suite
Tests profile recovery functionality against actual deployed endpoints
"""

import asyncio
import httpx
import json
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# API Configuration
BASE_URL = "https://birjobbackend-ir3e.onrender.com/api/v1"
TIMEOUT = 30.0

class ProductionRecoveryTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Production-Recovery-Tester/1.0"
        }
        self.test_users = []
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "recovery_success_rate": 0.0
        }

    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                return {
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {},
                    "success": 200 <= response.status_code < 300
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "data": {"error": str(e)},
                    "success": False
                }

    def log_test(self, test_name: str, success: bool, details: str):
        """Log test result"""
        self.results["total_tests"] += 1
        if success:
            self.results["passed"] += 1
            status = "✅"
        else:
            self.results["failed"] += 1
            status = "❌"
            self.results["errors"].append(f"{test_name}: {details}")
        
        print(f"{status} {test_name}: {details}")

    async def create_test_user_with_profile(self, email: str, phone: str = None) -> Optional[Dict[str, Any]]:
        """Create a test user with a complete profile for recovery testing"""
        # Generate proper device token (64+ chars)
        device_token = f"test_token_{uuid.uuid4().hex}_{uuid.uuid4().hex[:32]}"
        device_id = f"test_device_{uuid.uuid4().hex[:12]}"
        
        # Step 1: Register device
        device_data = {
            "device_token": device_token,
            "device_info": {
                "device_id": device_id,
                "os_version": "17.2",
                "app_version": "1.0.0",
                "device_model": "iPhone15,2",
                "timezone": "America/Los_Angeles",
                "locale": "en_US"
            }
        }
        
        device_response = await self.make_request("POST", "/devices/register", device_data)
        
        if not device_response["success"]:
            print(f"❌ Failed to register device for {email}: {device_response}")
            return None
        
        registered_device_id = device_response["data"]["data"]["device_id"]
        user_id = device_response["data"]["data"]["user_id"]
        
        # Step 2: Create user profile (attempt with current endpoint)
        # Note: This may fail if profile endpoint isn't working, but device is still created
        profile_data = {
            "device_id": registered_device_id,
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "phone": phone,
            "skills": ["Python", "iOS", "Swift"],
            "current_job_title": "Senior Developer",
            "location": "Test City, CA",
            "bio": "Test user for profile recovery"
        }
        
        profile_response = await self.make_request("POST", "/users/profile", profile_data)
        
        test_user = {
            "device_id": registered_device_id,
            "user_id": user_id,
            "email": email,
            "phone": phone,
            "device_token": device_token,
            "device_info": device_data["device_info"],
            "profile_created": profile_response["success"]
        }
        
        self.test_users.append(test_user)
        
        profile_status = "✅" if profile_response["success"] else "⚠️ (device only)"
        print(f"📝 Created test user: {email} {profile_status}")
        print(f"   Device ID: {registered_device_id}")
        print(f"   User ID: {user_id}")
        
        return test_user

    async def test_endpoint_availability(self) -> bool:
        """Test if profile recovery endpoints are deployed"""
        print("\n🔍 Checking Profile Recovery Endpoint Availability...")
        
        # Test endpoints that should exist after deployment
        endpoints_to_check = [
            "/profile/check-recovery-options",
            "/profile/recover", 
            "/profile/link-device"
        ]
        
        available_endpoints = 0
        
        for endpoint in endpoints_to_check:
            # Try a basic request to see if endpoint exists
            test_data = {
                "new_device_id": "test_availability_check",
                "email": "test@example.com"
            }
            
            response = await self.make_request("POST", endpoint, test_data)
            
            if response["status_code"] != 404:
                available_endpoints += 1
                print(f"✅ {endpoint} - Available")
            else:
                print(f"❌ {endpoint} - Not deployed")
        
        if available_endpoints == len(endpoints_to_check):
            print("🎉 All profile recovery endpoints are deployed!")
            return True
        elif available_endpoints > 0:
            print(f"⚠️ Partial deployment: {available_endpoints}/{len(endpoints_to_check)} endpoints available")
            return True
        else:
            print("❌ Profile recovery endpoints not yet deployed")
            return False

    async def test_recovery_options_check(self, email: str, phone: str = None) -> Dict[str, Any]:
        """Test checking available recovery options"""
        print(f"\n🔍 Testing Recovery Options Check for {email}")
        
        recovery_data = {
            "new_device_id": f"check_device_{uuid.uuid4().hex[:8]}",
            "email": email,
            "phone": phone,
            "device_info": {
                "device_model": "iPhone15,2",
                "os_version": "17.2",
                "timezone": "America/Los_Angeles"
            }
        }
        
        response = await self.make_request("POST", "/profile/check-recovery-options", recovery_data)
        
        if response["success"]:
            data = response["data"]
            options = data.get("recovery_options", [])
            recommendation = data.get("recommendation", "none")
            
            self.log_test(
                f"Recovery Options Check ({email})",
                True,
                f"Found {len(options)} options, recommended: {recommendation}"
            )
            
            # Log details of available options
            for option in options:
                method = option.get("method")
                confidence = option.get("confidence")
                print(f"   📋 {method}: {confidence} confidence")
        else:
            self.log_test(
                f"Recovery Options Check ({email})",
                False,
                f"Request failed: {response['data']}"
            )
        
        return response

    async def test_email_recovery(self, email: str) -> Dict[str, Any]:
        """Test email-based profile recovery"""
        print(f"\n📧 Testing Email Recovery for {email}")
        
        new_device_id = f"email_recovery_{uuid.uuid4().hex[:8]}"
        
        recovery_data = {
            "new_device_id": new_device_id,
            "email": email,
            "device_info": {
                "device_model": "iPhone15,2",
                "os_version": "17.2",
                "timezone": "America/Los_Angeles"
            }
        }
        
        response = await self.make_request("POST", "/profile/recover", recovery_data)
        
        if response["success"]:
            data = response["data"]
            if data.get("success"):
                method = data.get("recovery_method")
                user_profile = data.get("user_profile", {})
                
                self.log_test(
                    f"Email Recovery ({email})",
                    True,
                    f"Recovery successful using {method}, profile completeness: {user_profile.get('profile_completeness', 0)}%"
                )
            else:
                self.log_test(
                    f"Email Recovery ({email})",
                    False,
                    f"Recovery failed: {data.get('message')}"
                )
        else:
            self.log_test(
                f"Email Recovery ({email})",
                False,
                f"Request failed: {response['data']}"
            )
        
        return response

    async def test_phone_recovery(self, phone: str) -> Dict[str, Any]:
        """Test phone-based profile recovery"""
        print(f"\n📱 Testing Phone Recovery for {phone}")
        
        new_device_id = f"phone_recovery_{uuid.uuid4().hex[:8]}"
        
        recovery_data = {
            "new_device_id": new_device_id,
            "phone": phone,
            "device_info": {
                "device_model": "iPhone15,2",
                "os_version": "17.2"
            }
        }
        
        response = await self.make_request("POST", "/profile/recover", recovery_data)
        
        if response["success"]:
            data = response["data"]
            if data.get("success"):
                method = data.get("recovery_method")
                self.log_test(
                    f"Phone Recovery ({phone})",
                    True,
                    f"Recovery successful using {method}"
                )
            else:
                self.log_test(
                    f"Phone Recovery ({phone})",
                    False,
                    f"Recovery failed: {data.get('message')}"
                )
        else:
            self.log_test(
                f"Phone Recovery ({phone})",
                False,
                f"Request failed: {response['data']}"
            )
        
        return response

    async def test_device_fingerprint_recovery(self, original_device_info: Dict) -> Dict[str, Any]:
        """Test device fingerprint-based recovery"""
        print(f"\n🔒 Testing Device Fingerprint Recovery")
        
        new_device_id = f"fingerprint_{uuid.uuid4().hex[:8]}"
        
        # Use similar device characteristics for fingerprint matching
        recovery_data = {
            "new_device_id": new_device_id,
            "device_info": {
                "device_model": original_device_info.get("device_model"),
                "os_version": original_device_info.get("os_version", "").split(".")[0],
                "timezone": original_device_info.get("timezone"),
                "locale": original_device_info.get("locale")
            }
        }
        
        response = await self.make_request("POST", "/profile/recover", recovery_data)
        
        if response["success"]:
            data = response["data"]
            if data.get("success"):
                method = data.get("recovery_method")
                self.log_test(
                    "Device Fingerprint Recovery",
                    True,
                    f"Recovery successful using {method}"
                )
            else:
                self.log_test(
                    "Device Fingerprint Recovery",
                    False,
                    f"No match found (expected for strict fingerprinting)"
                )
        else:
            self.log_test(
                "Device Fingerprint Recovery",
                False,
                f"Request failed: {response['data']}"
            )
        
        return response

    async def test_manual_device_linking(self, user_id: str) -> Dict[str, Any]:
        """Test manual device linking"""
        print(f"\n🔗 Testing Manual Device Linking for User {user_id}")
        
        new_device_id = f"manual_link_{uuid.uuid4().hex[:8]}"
        
        link_data = {
            "user_id": user_id,
            "new_device_id": new_device_id,
            "device_info": {
                "device_model": "iPhone15,2",
                "os_version": "17.2"
            }
        }
        
        response = await self.make_request("POST", "/profile/link-device", link_data)
        
        if response["success"]:
            data = response["data"]
            if data.get("success"):
                self.log_test(
                    "Manual Device Linking",
                    True,
                    "Device successfully linked to profile"
                )
            else:
                self.log_test(
                    "Manual Device Linking",
                    False,
                    f"Linking failed: {data.get('message')}"
                )
        else:
            self.log_test(
                "Manual Device Linking",
                False,
                f"Request failed: {response['data']}"
            )
        
        return response

    async def test_no_match_scenario(self) -> Dict[str, Any]:
        """Test recovery when no matching profile exists"""
        print(f"\n❓ Testing No-Match Scenario")
        
        recovery_data = {
            "new_device_id": f"nomatch_{uuid.uuid4().hex[:8]}",
            "email": "nonexistent@example.com",
            "phone": "+9999999999",
            "device_info": {
                "device_model": "Unknown",
                "os_version": "99.0"
            }
        }
        
        response = await self.make_request("POST", "/profile/recover", recovery_data)
        
        if response["success"]:
            data = response["data"]
            if not data.get("success"):
                self.log_test(
                    "No-Match Scenario",
                    True,
                    "Correctly handled non-existent profile"
                )
            else:
                self.log_test(
                    "No-Match Scenario",
                    False,
                    "Unexpected match found for non-existent user"
                )
        else:
            self.log_test(
                "No-Match Scenario",
                False,
                f"Request failed: {response['data']}"
            )
        
        return response

    async def run_comprehensive_production_tests(self):
        """Run comprehensive profile recovery tests against production"""
        print("🏭 Production Profile Recovery Test Suite")
        print("=" * 60)
        
        # Step 1: Check system health
        print("\n🏥 Step 1: System Health Check")
        health_response = await self.make_request("GET", "/health")
        if health_response["success"]:
            health_data = health_response["data"]
            print(f"✅ System Status: {health_data.get('status', 'unknown')}")
            
            services = health_data.get('services', {})
            for service, status in services.items():
                print(f"   {service}: {status}")
        else:
            print("❌ System health check failed - aborting tests")
            return
        
        # Step 2: Check endpoint availability
        print("\n🔍 Step 2: Endpoint Availability Check")
        endpoints_available = await self.test_endpoint_availability()
        
        if not endpoints_available:
            print("\n⚠️ Profile recovery endpoints not deployed yet.")
            print("   Testing current system behavior instead...")
            
            # Test current system to demonstrate profile loss
            await self.test_current_system_profile_loss()
            return
        
        # Step 3: Create test users
        print("\n📝 Step 3: Creating Test Users")
        user1 = await self.create_test_user_with_profile("prod.test.1@example.com", "+15551234567")
        user2 = await self.create_test_user_with_profile("prod.test.2@example.com")
        user3 = await self.create_test_user_with_profile("prod.test.3@example.com", "+15559876543")
        
        valid_users = [u for u in [user1, user2, user3] if u is not None]
        
        if not valid_users:
            print("❌ Failed to create test users - aborting recovery tests")
            return
        
        # Step 4: Test recovery options checking
        print("\n📋 Step 4: Testing Recovery Options")
        for user in valid_users:
            await self.test_recovery_options_check(user["email"], user.get("phone"))
            await asyncio.sleep(1)  # Rate limiting
        
        # Step 5: Test email recovery
        print("\n📧 Step 5: Testing Email Recovery")
        for user in valid_users:
            await self.test_email_recovery(user["email"])
            await asyncio.sleep(1)
        
        # Step 6: Test phone recovery
        print("\n📱 Step 6: Testing Phone Recovery")
        for user in valid_users:
            if user.get("phone"):
                await self.test_phone_recovery(user["phone"])
                await asyncio.sleep(1)
        
        # Step 7: Test device fingerprint recovery
        print("\n🔒 Step 7: Testing Device Fingerprint Recovery")
        if valid_users:
            await self.test_device_fingerprint_recovery(valid_users[0]["device_info"])
            await asyncio.sleep(1)
        
        # Step 8: Test manual device linking
        print("\n🔗 Step 8: Testing Manual Device Linking")
        if valid_users:
            await self.test_manual_device_linking(valid_users[0]["user_id"])
            await asyncio.sleep(1)
        
        # Step 9: Test no-match scenario
        print("\n❓ Step 9: Testing No-Match Scenario")
        await self.test_no_match_scenario()
        
        # Step 10: Generate results
        self.generate_test_report()

    async def test_current_system_profile_loss(self):
        """Test current system to demonstrate profile loss issue"""
        print("\n📱 Testing Current System - Profile Loss Demonstration")
        print("-" * 50)
        
        # Create original user
        print("1. Creating original user...")
        original_user = await self.create_test_user_with_profile("demo.loss@example.com", "+15551111111")
        
        if not original_user:
            print("❌ Failed to create original user")
            return
        
        # Simulate app reinstall
        print("\n2. Simulating app reinstall (new device registration)...")
        new_device_token = f"reinstall_{uuid.uuid4().hex}_{uuid.uuid4().hex[:32]}"
        new_device_id = f"reinstalled_{uuid.uuid4().hex[:12]}"
        
        reinstall_data = {
            "device_token": new_device_token,
            "device_info": {
                "device_id": new_device_id,
                "os_version": "17.2",
                "app_version": "1.0.0",
                "device_model": "iPhone15,2",
                "timezone": "America/Los_Angeles"
            }
        }
        
        reinstall_response = await self.make_request("POST", "/devices/register", reinstall_data)
        
        if reinstall_response["success"]:
            reinstall_data = reinstall_response["data"]["data"]
            new_user_id = reinstall_data["user_id"]
            
            print(f"\n📊 Profile Loss Analysis:")
            print(f"   Original User ID: {original_user['user_id']}")
            print(f"   New User ID:      {new_user_id}")
            
            if new_user_id != original_user["user_id"]:
                print("❌ PROFILE LOSS CONFIRMED!")
                print("   Different User IDs = Separate Profiles")
                print("   User cannot access original saved jobs, preferences, etc.")
                print("\n💡 This is exactly what profile recovery solves!")
            else:
                print("✅ Profile preserved (unexpected)")
        else:
            print("❌ Reinstall simulation failed")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 PRODUCTION TEST REPORT")
        print("=" * 60)
        
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📈 Test Summary:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        
        if self.results["errors"]:
            print(f"\n🚨 Failed Tests:")
            for error in self.results["errors"]:
                print(f"   • {error}")
        
        print(f"\n👥 Test Users Created: {len(self.test_users)}")
        for user in self.test_users:
            print(f"   • {user['email']} (ID: {user['user_id'][:8]}...)")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"production_test_results_{timestamp}.json"
        
        full_results = {
            "test_summary": self.results,
            "test_users": self.test_users,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "api_base_url": self.base_url
        }
        
        with open(results_file, 'w') as f:
            json.dump(full_results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Profile recovery system is working correctly.")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Review errors and retry.")

async def main():
    """Main function to run production tests"""
    tester = ProductionRecoveryTester()
    
    try:
        await tester.run_comprehensive_production_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Fatal error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🏭 Production Profile Recovery Test Suite")
    print("⚡ Testing against live production API...")
    print(f"🔗 API Base: {BASE_URL}")
    print()
    
    # Run the async tests
    asyncio.run(main())