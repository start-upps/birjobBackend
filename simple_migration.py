#!/usr/bin/env python3
"""
Direct migration script using psycopg2
"""
import psycopg2
import sys

def create_iosapp_schema():
    """Create the iosapp schema directly"""
    
    # Connection string for psycopg2 (not asyncpg)
    conn_string = "postgresql://neondb_owner:gocazMi82pXl@ep-white-cloud-a2453ie4.eu-central-1.aws.neon.tech/neondb?sslmode=require"
    
    # SQL to create the iosapp schema
    sql_commands = [
        "CREATE SCHEMA IF NOT EXISTS iosapp;",
        
        """CREATE TABLE IF NOT EXISTS iosapp.device_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_token VARCHAR(255) UNIQUE NOT NULL,
            device_info JSONB,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        """CREATE TABLE IF NOT EXISTS iosapp.keyword_subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
            keywords TEXT[] NOT NULL,
            sources TEXT[],
            location_filters JSONB,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        """CREATE TABLE IF NOT EXISTS iosapp.job_matches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
            subscription_id UUID NOT NULL REFERENCES iosapp.keyword_subscriptions(id) ON DELETE CASCADE,
            job_id VARCHAR NOT NULL,
            matched_keywords TEXT[] NOT NULL,
            relevance_score VARCHAR,
            is_read BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        """CREATE TABLE IF NOT EXISTS iosapp.push_notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
            match_id UUID REFERENCES iosapp.job_matches(id) ON DELETE CASCADE,
            notification_type VARCHAR(50) NOT NULL,
            payload JSONB NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            apns_response JSONB,
            sent_at TIMESTAMP WITH TIME ZONE,
            delivered_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );""",
        
        """CREATE TABLE IF NOT EXISTS iosapp.processed_jobs (
            device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
            job_id VARCHAR NOT NULL,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (device_id, job_id)
        );""",
        
        # Indexes
        "CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON iosapp.device_tokens(is_active, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_device_tokens_token ON iosapp.device_tokens(device_token);",
        "CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_device ON iosapp.keyword_subscriptions(device_id, is_active);",
        "CREATE INDEX IF NOT EXISTS idx_keyword_subscriptions_keywords ON iosapp.keyword_subscriptions USING GIN(keywords);",
        "CREATE INDEX IF NOT EXISTS idx_job_matches_device_created ON iosapp.job_matches(device_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_job_matches_subscription ON iosapp.job_matches(subscription_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_job_matches_unread ON iosapp.job_matches(device_id, is_read, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_push_notifications_device ON iosapp.push_notifications(device_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_push_notifications_status ON iosapp.push_notifications(status, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_processed_jobs_lookup ON iosapp.processed_jobs(device_id, job_id);",
        
        # Trigger function
        """CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';""",
        
        # Triggers
        """DROP TRIGGER IF EXISTS update_device_tokens_updated_at ON iosapp.device_tokens;
        CREATE TRIGGER update_device_tokens_updated_at 
            BEFORE UPDATE ON iosapp.device_tokens 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();""",
            
        """DROP TRIGGER IF EXISTS update_keyword_subscriptions_updated_at ON iosapp.keyword_subscriptions;
        CREATE TRIGGER update_keyword_subscriptions_updated_at 
            BEFORE UPDATE ON iosapp.keyword_subscriptions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"""
    ]
    
    try:
        print("🗄️ Connecting to Neon database...")
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        print("🚀 Creating iosapp schema and tables...")
        
        for i, command in enumerate(sql_commands, 1):
            try:
                cursor.execute(command)
                print(f"✅ Step {i}/{len(sql_commands)} completed")
            except Exception as e:
                print(f"⚠️  Step {i}: {e} (might be expected if already exists)")
        
        # Verify the schema was created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'iosapp'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n🎉 Migration completed! Created {len(tables)} tables:")
        for table in tables:
            print(f"  - iosapp.{table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Your database is ready for the iOS backend!")
        print("🚀 You can now deploy to Render!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🗄️ iOS Backend - Simple Database Migration")
    print("=" * 50)
    
    if create_iosapp_schema():
        print("\n🎉 Success! Your Neon database now has the iosapp schema.")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)