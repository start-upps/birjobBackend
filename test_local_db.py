#!/usr/bin/env python3
"""
Test database operations locally to debug issues
"""
import asyncio
import asyncpg
import os
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

async def test_insert():
    """Test direct database insert"""
    
    # Get database URL and convert for asyncpg
    database_url = os.getenv("DATABASE_URL")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if "?sslmode=require" in database_url:
        database_url = database_url.replace("?sslmode=require", "")
    
    try:
        conn = await asyncpg.connect(database_url, ssl="require")
        print("✅ Connected to database")
        
        # Test insert
        device_id = uuid.uuid4()
        device_token = f"test_token_{uuid.uuid4().hex}_{uuid.uuid4().hex}"
        device_info = {
            "os_version": "17.0",
            "app_version": "1.0.0",
            "device_model": "iPhone15,2",
            "timezone": "UTC"
        }
        
        print(f"🧪 Testing insert with device_id: {device_id}")
        print(f"🧪 Device token: {device_token}")
        
        await conn.execute("""
            INSERT INTO iosapp.device_tokens (id, device_token, device_info, is_active)
            VALUES ($1, $2, $3, $4)
        """, device_id, device_token, json.dumps(device_info), True)
        
        print("✅ Insert successful!")
        
        # Verify insert
        result = await conn.fetchrow("""
            SELECT id, device_token, device_info, is_active, created_at
            FROM iosapp.device_tokens 
            WHERE id = $1
        """, device_id)
        
        if result:
            print("✅ Device found in database:")
            print(f"  ID: {result['id']}")
            print(f"  Token: {result['device_token']}")
            print(f"  Info: {result['device_info']}")
            print(f"  Active: {result['is_active']}")
            print(f"  Created: {result['created_at']}")
            
            # Clean up
            await conn.execute("DELETE FROM iosapp.device_tokens WHERE id = $1", device_id)
            print("🧹 Test data cleaned up")
        else:
            print("❌ Device not found after insert")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_insert())