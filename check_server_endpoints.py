#!/usr/bin/env python3
"""
Check what endpoints are available on production server
"""
import asyncio
import httpx

PRODUCTION_SERVER = "https://birjobbackend-ir3e.onrender.com"

async def check_server_endpoints():
    """Check available endpoints on production server"""
    print("=== Checking Production Server Endpoints ===")
    print(f"Server: {PRODUCTION_SERVER}")
    
    # Common endpoints to test
    endpoints = [
        "/",
        "/health",
        "/api/health", 
        "/api/v1/health",
        "/docs",
        "/api/v1/devices/register",
        "/api/v1/devices/token",
        "/api/v1/notifications",
        "/api/v1/users",
        "/status"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            try:
                response = await client.get(f"{PRODUCTION_SERVER}{endpoint}")
                status_emoji = "✅" if response.status_code == 200 else "📍" if response.status_code in [404, 405] else "❌"
                print(f"{status_emoji} {endpoint}: {response.status_code}")
                
                if response.status_code == 200 and len(response.text) < 200:
                    print(f"    Response: {response.text[:100]}")
                    
            except Exception as e:
                print(f"❌ {endpoint}: Connection error - {e}")
        
        # Test device registration specifically
        print(f"\n=== Testing Device Registration ===")
        try:
            device_data = {
                "device_token": "328b1bcf9414e941a07f5d102260b4e48245f83cc07291e62ff2eb16c478a442",
                "device_info": {
                    "device_id": "test-device-prod",
                    "os_version": "18.6",
                    "app_version": "1.0",
                    "device_model": "iPhone",
                    "timezone": "UTC"
                }
            }
            
            response = await client.post(
                f"{PRODUCTION_SERVER}/api/v1/devices/register",
                json=device_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Device Registration: {response.status_code}")
            if response.status_code == 200:
                print("✅ Device registration working!")
                data = response.json()
                print(f"Response: {data}")
            else:
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Device registration test failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_server_endpoints())