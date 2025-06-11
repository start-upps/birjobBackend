#!/usr/bin/env python3
"""
Fix database schema to match models
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def fix_schema():
    """Fix database schema mismatches"""
    
    # Get database URL and convert for asyncpg
    database_url = os.getenv("DATABASE_URL")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if "?sslmode=require" in database_url:
        database_url = database_url.replace("?sslmode=require", "")
    
    try:
        conn = await asyncpg.connect(database_url, ssl="require")
        print("✅ Connected to database")
        
        # Check if subscription_id column exists in job_matches
        column_check = await conn.fetchval("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'iosapp' 
            AND table_name = 'job_matches' 
            AND column_name = 'subscription_id'
        """)
        
        if column_check:
            print("📋 Found subscription_id column in job_matches")
            print("🔧 Dropping subscription_id column...")
            await conn.execute("ALTER TABLE iosapp.job_matches DROP COLUMN IF EXISTS subscription_id")
            print("✅ subscription_id column dropped")
        else:
            print("ℹ️ subscription_id column not found - no action needed")
        
        # Verify final schema
        print("\n📋 Final job_matches schema:")
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'iosapp' AND table_name = 'job_matches'
            ORDER BY ordinal_position
        """)
        
        for col in columns:
            print(f"  {col['column_name']}: {col['data_type']}")
        
        await conn.close()
        print("✅ Schema fix complete")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_schema())