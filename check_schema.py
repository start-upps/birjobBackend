#!/usr/bin/env python3
"""
Check actual database schema
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_schema():
    """Check actual database schema"""
    
    # Get database URL and convert for asyncpg
    database_url = os.getenv("DATABASE_URL")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if "?sslmode=require" in database_url:
        database_url = database_url.replace("?sslmode=require", "")
    
    try:
        conn = await asyncpg.connect(database_url, ssl="require")
        
        # Check each table schema
        tables = ['device_tokens', 'keyword_subscriptions', 'job_matches', 'push_notifications', 'processed_jobs']
        
        for table in tables:
            print(f"\n📋 {table} schema:")
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'iosapp' AND table_name = $1
                ORDER BY ordinal_position
            """, table)
            
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  {col['column_name']}: {col['data_type']} {nullable}{default}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())