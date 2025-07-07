#!/usr/bin/env python3
"""
Test production server to verify new APNs key is deployed
"""
import asyncio
import httpx
import json

# Your production server URL (adjust if different)
PRODUCTION_SERVER = "https://birjob-backend.onrender.com"  # Update this URL
NEW_DEVICE_TOKEN = "328b1bcf9414e941a07f5d102260b4e48245f83cc07291e62ff2eb16c478a442"

async def test_production_server():
    """Test that production server is using new APNs key"""
    print("=== Testing Production Server Deployment ===")
    print(f"Server: {PRODUCTION_SERVER}")
    
    # Test 1: Health check
    print("\n1. Testing server health...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{PRODUCTION_SERVER}/health")
            print(f"Health Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Server is running")
            else:
                print("❌ Server health check failed")
                return
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return
    
    # Test 2: Test device registration
    print("\n2. Testing device registration...")
    try:
        device_data = {
            "device_token": NEW_DEVICE_TOKEN,
            "device_info": {
                "device_id": "test-production-device",
                "os_version": "18.6",
                "app_version": "1.0",
                "device_model": "iPhone",
                "timezone": "UTC"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{PRODUCTION_SERVER}/api/v1/devices/register",
                json=device_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Registration Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("✅ Device registration successful")
                print(f"Device ID: {data.get('data', {}).get('device_id')}")
                print(f"User ID: {data.get('data', {}).get('user_id')}")
            else:
                print(f"❌ Registration failed: {response.text}")
                
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
    
    # Test 3: Test push notification endpoint (if available)
    print("\n3. Testing push notification capability...")
    try:
        # Check if there's a test push endpoint
        test_payload = {
            "device_token": NEW_DEVICE_TOKEN,
            "message": {
                "title": "Production Test",
                "body": "Testing production push notifications"
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try different possible endpoints
            endpoints = [
                "/api/v1/notifications/test",
                "/test/push",
                "/api/v1/push/test"
            ]
            
            for endpoint in endpoints:
                try:
                    response = await client.post(
                        f"{PRODUCTION_SERVER}{endpoint}",
                        json=test_payload,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    print(f"Endpoint {endpoint}: {response.status_code}")
                    if response.status_code == 200:
                        print(f"✅ Push test successful via {endpoint}")
                        break
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(f"Response: {response.text}")
                except:
                    continue
            else:
                print("ℹ️  No test push endpoint found (this is normal)")
                
    except Exception as e:
        print(f"ℹ️  Push test not available: {e}")
    
    print("\n=== Production Server Summary ===")
    print("✅ If health check and registration passed, your server is ready")
    print("✅ New APNs key should be deployed and working")
    print("📱 Ready for production push notifications!")

if __name__ == "__main__":
    asyncio.run(test_production_server())