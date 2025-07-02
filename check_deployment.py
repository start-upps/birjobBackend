#!/usr/bin/env python3
"""
Simple deployment status checker
"""

import asyncio
import httpx
import time

async def check_deployment():
    url = "https://birjob-ios-api.onrender.com"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            print(f"🔍 Checking deployment at {url}")
            response = await client.get(f"{url}/")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Deployment is live! {data['message']}")
                return True
            else:
                print(f"❌ Status code: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

async def monitor_deployment(max_attempts=20, delay=15):
    """Monitor deployment status with retries"""
    print("🚀 Monitoring deployment status...")
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n📡 Attempt {attempt}/{max_attempts}")
        
        if await check_deployment():
            print("🎉 Deployment is successful!")
            return True
        
        if attempt < max_attempts:
            print(f"⏳ Waiting {delay} seconds before next check...")
            time.sleep(delay)
    
    print("⚠️ Deployment check timed out")
    return False

if __name__ == "__main__":
    asyncio.run(monitor_deployment())