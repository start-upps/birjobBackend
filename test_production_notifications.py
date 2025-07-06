#!/usr/bin/env python3
"""
Test production notification system when service is running
"""

import requests
import json
import time

def test_production_notifications():
    """Test production notification endpoints"""
    
    base_url = "https://birjobbackend.onrender.com"
    device_id = "45b750ec8ffa3c41b9adf6625a9177a6fb2e5670f84fac7cd72b682f86ce8f49"
    
    print("🚀 Testing Production Notification System")
    print("="*60)
    print(f"Base URL: {base_url}")
    print(f"Device ID: {device_id}")
    print("")
    
    # 1. Test if service is running
    print("🔍 Checking if service is running...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 404:
            print("❌ Service not responding (404)")
            print("   Check Render dashboard for deployment status")
            return False
        else:
            print(f"✅ Service responding (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Service not reachable: {e}")
        print("   Service may still be starting up...")
        return False
    
    # 2. Test health endpoint
    print("\n🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/health/check", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"⚠️  Health check returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
    
    # 3. Test notification stats
    print("\n📊 Testing notification stats...")
    try:
        response = requests.get(f"{base_url}/api/v1/notifications/stats", timeout=10)
        if response.status_code == 200:
            print("✅ Notification stats endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"⚠️  Stats endpoint returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Stats endpoint failed: {e}")
    
    # 4. Test notification trigger
    print("\n🔔 Testing notification trigger...")
    try:
        payload = {
            "dry_run": False,
            "limit": 10
        }
        
        response = requests.post(
            f"{base_url}/api/v1/notifications/trigger",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Notification trigger successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            notifications_sent = result.get('notifications_sent', 0)
            if notifications_sent > 0:
                print(f"\n🎉 SUCCESS! {notifications_sent} notifications sent!")
                print("📱 Check your iPhone for push notifications!")
                return True
            else:
                print(f"\n📋 No notifications sent:")
                print(f"   Processed jobs: {result.get('processed_jobs', 0)}")
                print(f"   Matched users: {result.get('matched_users', 0)}")
                
        else:
            print(f"❌ Trigger failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Trigger request failed: {e}")
    
    # 5. Test notification history
    print(f"\n📱 Testing notification history for your device...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/notifications/history/{device_id}?limit=5",
            timeout=10
        )
        
        if response.status_code == 200:
            history = response.json()
            print("✅ History endpoint working")
            print(f"   Total notifications: {history.get('total_notifications', 0)}")
            
            recent = history.get('recent_notifications', [])
            if recent:
                print(f"   Recent notifications:")
                for notif in recent[:3]:
                    print(f"     - {notif.get('job_title', 'Unknown')} at {notif.get('job_company', 'Unknown')}")
            else:
                print("   No recent notifications found")
                
        else:
            print(f"⚠️  History endpoint returned {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ History request failed: {e}")
    
    return False

def wait_for_service(max_wait=300):
    """Wait for service to come online"""
    
    print("⏳ Waiting for service to start...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get("https://birjobbackend.onrender.com/", timeout=5)
            if response.status_code != 404 or "no-server" not in response.headers.get("x-render-routing", ""):
                print("✅ Service is starting up!")
                time.sleep(10)  # Give it a bit more time
                return True
        except:
            pass
        
        elapsed = int(time.time() - start_time)
        print(f"   Waiting... ({elapsed}s elapsed)")
        time.sleep(10)
    
    print("❌ Service didn't start within the timeout period")
    return False

if __name__ == "__main__":
    print("🔔 Production Push Notification Test")
    print("🇦🇿 Testing notifications to iPhone in Baku")
    print("📱 Device: Real iOS device with ML/AI keywords")
    print("")
    
    # Wait for service if needed
    try:
        response = requests.get("https://birjobbackend.onrender.com/", timeout=5)
        if "no-server" in response.headers.get("x-render-routing", ""):
            if not wait_for_service():
                print("Cannot test - service not running")
                exit(1)
    except:
        if not wait_for_service():
            print("Cannot test - service not running")
            exit(1)
    
    # Run tests
    success = test_production_notifications()
    
    print("\n" + "="*60)
    if success:
        print("🎉 PRODUCTION NOTIFICATION TEST SUCCESSFUL!")
        print("📱 You should receive push notifications on your iPhone!")
    else:
        print("📋 Tests completed - check results above")
        print("💡 If no new notifications, try adding fresh job data with ML/AI keywords")
    
    print("\n📝 Next steps if needed:")
    print("   1. Check Render dashboard for any deployment errors")
    print("   2. Verify environment variables (APNS_KEY_ID=S64YC3U4ZX)")
    print("   3. Ensure /etc/secrets/AuthKey_S64YC3U4ZX.p8 is uploaded")
    print("   4. Monitor logs for APNs delivery status")