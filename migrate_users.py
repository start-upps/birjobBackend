#!/usr/bin/env python3
"""
Database migration script for user tables
"""
import asyncio
import sys
from app.core.database import db_manager

async def create_user_tables():
    """Create all user-related tables"""
    
    # Users table
    users_table = """
    CREATE TABLE IF NOT EXISTS iosapp.users (
        id VARCHAR(255) PRIMARY KEY,
        device_id VARCHAR(255) UNIQUE NOT NULL,
        
        -- Personal Information
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        email VARCHAR(255),
        phone VARCHAR(20),
        location VARCHAR(255),
        current_job_title VARCHAR(255),
        years_of_experience VARCHAR(50),
        linkedin_profile VARCHAR(500),
        portfolio_url VARCHAR(500),
        bio TEXT,
        
        -- Job Preferences (stored as JSON)
        desired_job_types JSONB,
        remote_work_preference VARCHAR(50) DEFAULT 'Hybrid',
        skills JSONB,
        preferred_locations JSONB,
        min_salary INTEGER,
        max_salary INTEGER,
        salary_currency VARCHAR(10) DEFAULT 'USD',
        salary_negotiable BOOLEAN DEFAULT TRUE,
        
        -- Notification Settings
        job_matches_enabled BOOLEAN DEFAULT TRUE,
        application_reminders_enabled BOOLEAN DEFAULT TRUE,
        weekly_digest_enabled BOOLEAN DEFAULT FALSE,
        market_insights_enabled BOOLEAN DEFAULT TRUE,
        quiet_hours_enabled BOOLEAN DEFAULT TRUE,
        quiet_hours_start VARCHAR(5) DEFAULT '22:00',
        quiet_hours_end VARCHAR(5) DEFAULT '08:00',
        preferred_notification_time VARCHAR(5) DEFAULT '09:00',
        
        -- Privacy Settings
        profile_visibility VARCHAR(20) DEFAULT 'Public',
        share_analytics BOOLEAN DEFAULT TRUE,
        share_job_view_history BOOLEAN DEFAULT FALSE,
        allow_personalized_recommendations BOOLEAN DEFAULT TRUE,
        
        -- Profile Metadata
        profile_completeness INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Saved jobs table
    saved_jobs_table = """
    CREATE TABLE IF NOT EXISTS iosapp.saved_jobs (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        job_id INTEGER NOT NULL,
        notes TEXT,
        application_status VARCHAR(20) DEFAULT 'not_applied',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
        UNIQUE (user_id, job_id)
    );
    """
    
    # Job views table
    job_views_table = """
    CREATE TABLE IF NOT EXISTS iosapp.job_views (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        job_id INTEGER NOT NULL,
        view_duration INTEGER,
        source VARCHAR(50),
        viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE
    );
    """
    
    # Job applications table
    job_applications_table = """
    CREATE TABLE IF NOT EXISTS iosapp.job_applications (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        job_id INTEGER NOT NULL,
        
        -- Application details
        status VARCHAR(20) DEFAULT 'pending',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        follow_up_date TIMESTAMP,
        
        -- Application source/method
        application_source VARCHAR(100),
        
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE,
        UNIQUE (user_id, job_id)
    );
    """
    
    # User analytics table
    user_analytics_table = """
    CREATE TABLE IF NOT EXISTS iosapp.user_analytics (
        id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        
        -- Profile insights
        profile_strength INTEGER DEFAULT 0,
        market_fit INTEGER DEFAULT 0,
        
        -- Job activity stats
        total_jobs_viewed INTEGER DEFAULT 0,
        total_jobs_saved INTEGER DEFAULT 0,
        total_applications INTEGER DEFAULT 0,
        average_view_time DECIMAL(10,2) DEFAULT 0,
        
        -- Matching insights
        total_matches INTEGER DEFAULT 0,
        average_match_score DECIMAL(5,2) DEFAULT 0,
        
        -- Computed insights (stored as JSON)
        improvement_areas JSONB,
        most_viewed_categories JSONB,
        top_matching_companies JSONB,
        recommended_skills JSONB,
        market_insights JSONB,
        
        -- Timestamps
        computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) ON DELETE CASCADE
    );
    """
    
    # Execute table creation
    tables = [
        ("users", users_table),
        ("saved_jobs", saved_jobs_table),
        ("job_views", job_views_table),
        ("job_applications", job_applications_table),
        ("user_analytics", user_analytics_table)
    ]
    
    for table_name, sql in tables:
        try:
            print(f"Creating table: iosapp.{table_name}")
            await db_manager.execute_query(sql)
            print(f"✓ Table iosapp.{table_name} created successfully")
        except Exception as e:
            print(f"✗ Error creating table iosapp.{table_name}: {e}")
            return False
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_device_id ON iosapp.users(device_id);",
        "CREATE INDEX IF NOT EXISTS idx_saved_jobs_user_id ON iosapp.saved_jobs(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_saved_jobs_job_id ON iosapp.saved_jobs(job_id);",
        "CREATE INDEX IF NOT EXISTS idx_job_views_user_id ON iosapp.job_views(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_job_views_job_id ON iosapp.job_views(job_id);",
        "CREATE INDEX IF NOT EXISTS idx_job_views_viewed_at ON iosapp.job_views(viewed_at);",
        "CREATE INDEX IF NOT EXISTS idx_job_applications_user_id ON iosapp.job_applications(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_job_applications_job_id ON iosapp.job_applications(job_id);",
        "CREATE INDEX IF NOT EXISTS idx_job_applications_status ON iosapp.job_applications(status);",
        "CREATE INDEX IF NOT EXISTS idx_job_applications_applied_at ON iosapp.job_applications(applied_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_analytics_user_id ON iosapp.user_analytics(user_id);"
    ]
    
    print("\nCreating indexes...")
    for index_sql in indexes:
        try:
            await db_manager.execute_query(index_sql)
            print(f"✓ Index created")
        except Exception as e:
            print(f"✗ Error creating index: {e}")
    
    print("\n🎉 All user tables and indexes created successfully!")
    return True

if __name__ == "__main__":
    asyncio.run(create_user_tables())