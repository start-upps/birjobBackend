#!/usr/bin/env python3
"""
Check and create database tables for production
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_and_create_tables():
    """Check if tables exist and create them if needed"""
    
    # Get database URL and convert for asyncpg
    database_url = os.getenv("DATABASE_URL")
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    if "?sslmode=require" in database_url:
        database_url = database_url.replace("?sslmode=require", "")
    
    print(f"Connecting to database...")
    
    try:
        conn = await asyncpg.connect(database_url, ssl="require")
        print("✅ Database connection successful")
        
        # Check if iosapp schema exists
        schema_check = await conn.fetchval(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'iosapp'"
        )
        
        if schema_check:
            print("✅ iosapp schema exists")
        else:
            print("❌ iosapp schema does not exist")
            print("Creating iosapp schema...")
            await conn.execute("CREATE SCHEMA IF NOT EXISTS iosapp")
            print("✅ iosapp schema created")
        
        # Check tables
        tables_check = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'iosapp'
        """)
        
        existing_tables = [row['table_name'] for row in tables_check]
        print(f"Existing tables in iosapp schema: {existing_tables}")
        
        required_tables = ['device_tokens', 'keyword_subscriptions', 'job_matches', 'push_notifications', 'processed_jobs']
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            print("Creating missing tables...")
            
            # Create tables
            create_sql = """
            -- Device tokens table
            CREATE TABLE IF NOT EXISTS iosapp.device_tokens (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_token VARCHAR(255) UNIQUE NOT NULL,
                device_info JSONB,
                is_active BOOLEAN DEFAULT true,
                last_seen TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Keyword subscriptions table
            CREATE TABLE IF NOT EXISTS iosapp.keyword_subscriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
                keywords TEXT[] NOT NULL,
                sources TEXT[],
                location_filters JSONB,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Job matches table
            CREATE TABLE IF NOT EXISTS iosapp.job_matches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
                job_id VARCHAR(50) NOT NULL,
                matched_keywords TEXT[] NOT NULL,
                relevance_score DECIMAL(3,2),
                is_read BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Push notifications table
            CREATE TABLE IF NOT EXISTS iosapp.push_notifications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
                title VARCHAR(100) NOT NULL,
                body TEXT NOT NULL,
                data JSONB,
                status VARCHAR(20) DEFAULT 'pending',
                sent_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            -- Processed jobs table  
            CREATE TABLE IF NOT EXISTS iosapp.processed_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                device_id UUID REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
                job_id VARCHAR(50) NOT NULL,
                action VARCHAR(20) NOT NULL,
                processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(device_id, job_id, action)
            );

            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_device_tokens_token ON iosapp.device_tokens(device_token);
            CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON iosapp.device_tokens(is_active);
            CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_device ON iosapp.keyword_subscriptions(device_id);
            CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_active ON iosapp.keyword_subscriptions(is_active);
            CREATE INDEX IF NOT EXISTS idx_job_matches_device ON iosapp.job_matches(device_id);
            CREATE INDEX IF NOT EXISTS idx_job_matches_read ON iosapp.job_matches(is_read);
            CREATE INDEX IF NOT EXISTS idx_push_notifications_device ON iosapp.push_notifications(device_id);
            CREATE INDEX IF NOT EXISTS idx_processed_jobs_device_job ON iosapp.processed_jobs(device_id, job_id);
            """
            
            await conn.execute(create_sql)
            print("✅ All tables created successfully")
        else:
            print("✅ All required tables exist")
        
        # Final verification
        final_check = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'iosapp'
            ORDER BY table_name
        """)
        
        final_tables = [row['table_name'] for row in final_check]
        print(f"Final table list: {final_tables}")
        
        await conn.close()
        print("✅ Database setup complete")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(check_and_create_tables())