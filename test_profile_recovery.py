#!/usr/bin/env python3
"""
Profile Recovery Test Suite
Tests the profile recovery functionality with real API calls
"""

import asyncio
import httpx
import json
import uuid
from typing import Dict, Any
from datetime import datetime

# API Configuration
BASE_URL = "https://birjobbackend-ir3e.onrender.com/api/v1"
TIMEOUT = 30.0

class ProfileRecoveryTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Profile-Recovery-Tester/1.0"
        }
        self.test_users = []
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request to API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
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
    
    async def create_test_user(self, email: str, phone: str = None) -> Dict[str, Any]:
        """Create a test user for recovery testing"""
        device_id = f"test_device_{uuid.uuid4().hex[:8]}"
        
        # First register device
        device_data = {
            "device_token": f"test_token_{uuid.uuid4().hex[:16]}",
            "device_info": {
                "device_id": device_id,
                "os_version": "17.2",
                "app_version": "1.0.0",
                "device_model": "iPhone15,2",
                "timezone": "America/Los_Angeles"
            }
        }
        
        device_response = await self.make_request("POST", "/devices/register", device_data)
        
        if not device_response["success"]:
            print(f"❌ Failed to register device: {device_response}")
            return {}
        
        # Extract user info
        user_data = device_response["data"].get("data", {})
        user_device_id = user_data.get("device_id")
        user_id = user_data.get("user_id")
        
        if not user_device_id:
            print(f"❌ No device_id in response: {device_response}")
            return {}
        
        # Create user profile with recovery information
        profile_data = {
            "deviceId": user_device_id,
            "profile": {
                "name": "Test User",
                "email": email,
                "phone": phone,
                "skills": ["Python", "iOS", "Swift"],
                "experience": "3-5 years",
                "location": "Test City",
                "preferences": {
                    "remote_work": True,
                    "salary_min": 100000,
                    "job_types": ["full-time"]
                }
            }
        }
        
        profile_response = await self.make_request("POST", "/users/profile", profile_data)
        
        test_user = {
            "device_id": user_device_id,
            "user_id": user_id,
            "email": email,
            "phone": phone,
            "original_device_token": device_data["device_token"]
        }
        
        self.test_users.append(test_user)
        print(f"✅ Created test user: {email} (device_id: {user_device_id})")
        return test_user
    
    async def test_recovery_options_check(self, email: str, phone: str = None) -> Dict[str, Any]:
        """Test checking recovery options"""
        print(f"\n🔍 Testing recovery options check for {email}")
        
        recovery_data = {
            "new_device_id": f"new_device_{uuid.uuid4().hex[:8]}",
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
            print(f"✅ Found {len(options)} recovery options")
            
            for option in options:
                method = option.get("method")
                confidence = option.get("confidence")
                print(f"   - {method}: {confidence} confidence")
                
                preview = option.get("profile_preview", {})
                if preview.get("name"):
                    print(f"     Profile: {preview['name']}")
                if preview.get("email"):
                    print(f"     Email: {preview['email']}")
        else:
            print(f"❌ Recovery options check failed: {response}")
        
        return response
    
    async def test_email_recovery(self, email: str) -> Dict[str, Any]:
        """Test email-based profile recovery"""
        print(f"\n📧 Testing email recovery for {email}")
        
        new_device_id = f"recovered_device_{uuid.uuid4().hex[:8]}"
        
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
                print(f"✅ Recovery successful using: {method}")
                
                profile = data.get("user_profile", {})
                print(f"   - User ID: {profile.get('user_id')}")
                print(f"   - Device ID: {profile.get('device_id')}")
                print(f"   - Name: {profile.get('name')}")
                print(f"   - Profile Completeness: {profile.get('profile_completeness')}%")
            else:
                print(f"❌ Recovery failed: {data.get('message')}")
        else:
            print(f"❌ Recovery request failed: {response}")
        
        return response
    
    async def test_phone_recovery(self, phone: str) -> Dict[str, Any]:
        """Test phone-based profile recovery"""
        print(f"\n📱 Testing phone recovery for {phone}")
        
        new_device_id = f"phone_recovered_{uuid.uuid4().hex[:8]}"
        
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
                print(f"✅ Recovery successful using: {method}")
            else:
                print(f"❌ Recovery failed: {data.get('message')}")
        else:
            print(f"❌ Recovery request failed: {response}")
        
        return response
    
    async def test_device_fingerprint_recovery(self, original_device_info: Dict) -> Dict[str, Any]:
        """Test device fingerprint-based recovery"""
        print(f"\n🔒 Testing device fingerprint recovery")
        
        new_device_id = f"fingerprint_device_{uuid.uuid4().hex[:8]}"
        
        # Use similar device characteristics
        recovery_data = {
            "new_device_id": new_device_id,
            "device_info": {
                "device_model": original_device_info.get("device_model"),
                "os_version": original_device_info.get("os_version", "").split(".")[0],  # Major version
                "timezone": original_device_info.get("timezone"),
                "screen_resolution": "1179x2556"  # iPhone 15 Pro resolution
            }
        }
        
        response = await self.make_request("POST", "/profile/recover", recovery_data)
        
        if response["success"]:
            data = response["data"]
            if data.get("success"):
                method = data.get("recovery_method")
                print(f"✅ Recovery successful using: {method}")
            else:
                print(f"❌ Recovery failed: {data.get('message')}")
        else:
            print(f"❌ Recovery request failed: {response}")
        
        return response
    
    async def test_no_match_scenario(self) -> Dict[str, Any]:
        """Test recovery when no matching profile exists"""
        print(f"\n❓ Testing no-match scenario")
        
        recovery_data = {
            "new_device_id": f"nomatch_device_{uuid.uuid4().hex[:8]}",
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
                print(f"✅ Correctly handled no-match case: {data.get('message')}")
            else:
                print(f"❌ Unexpected match found: {data}")
        else:
            print(f"❌ Request failed: {response}")
        
        return response
    
    async def run_comprehensive_test(self):
        """Run comprehensive profile recovery tests"""
        print("🧪 Profile Recovery Comprehensive Test Suite")
        print("=" * 60)
        
        # Test 1: Create test users
        print("\n📝 Step 1: Creating test users...")
        user1 = await self.create_test_user("recovery_test_1@example.com", "+1234567890")
        user2 = await self.create_test_user("recovery_test_2@example.com")
        
        if not user1 or not user2:
            print("❌ Failed to create test users, aborting tests")
            return
        
        # Test 2: Check recovery options
        print("\n📝 Step 2: Testing recovery options check...")
        await self.test_recovery_options_check(user1["email"], user1["phone"])
        await self.test_recovery_options_check(user2["email"])
        
        # Test 3: Email recovery
        print("\n📝 Step 3: Testing email recovery...")
        await self.test_email_recovery(user1["email"])
        await self.test_email_recovery(user2["email"])
        
        # Test 4: Phone recovery
        if user1["phone"]:
            print("\n📝 Step 4: Testing phone recovery...")
            await self.test_phone_recovery(user1["phone"])
        
        # Test 5: Device fingerprint recovery (commented out - requires implementation)
        # print("\n📝 Step 5: Testing device fingerprint recovery...")
        # await self.test_device_fingerprint_recovery({"device_model": "iPhone15,2", "os_version": "17.2", "timezone": "America/Los_Angeles"})
        
        # Test 6: No match scenario
        print("\n📝 Step 6: Testing no-match scenario...")
        await self.test_no_match_scenario()
        
        print("\n" + "=" * 60)
        print("🎉 Profile Recovery Test Suite Completed!")
        print("\nTest Summary:")
        print(f"   - Created {len(self.test_users)} test users")
        print("   - Tested recovery options checking")
        print("   - Tested email-based recovery")
        print("   - Tested phone-based recovery (where applicable)")
        print("   - Tested no-match scenario handling")
        
        print("\n📋 Test Users Created:")
        for user in self.test_users:
            print(f"   - {user['email']} (device_id: {user['device_id']})")

async def main():
    """Main function to run profile recovery tests"""
    tester = ProfileRecoveryTester()
    
    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Fatal error during testing: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Profile Recovery Test Suite...")
    
    # Run the async tests
    asyncio.run(main())