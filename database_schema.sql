-- iOS App Schema Creation Script
-- This script creates the iosapp schema with all required tables and indexes

-- Create the iosapp schema
CREATE SCHEMA IF NOT EXISTS iosapp;

-- Device registration and management
CREATE TABLE iosapp.device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_token VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Keyword subscriptions per device
CREATE TABLE iosapp.keyword_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    keywords TEXT[] NOT NULL,
    sources TEXT[],
    location_filters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job matches found for devices
CREATE TABLE iosapp.job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES iosapp.keyword_subscriptions(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL, -- References scraper.jobs_jobpost.id
    matched_keywords TEXT[] NOT NULL,
    relevance_score DECIMAL(3,2),
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Push notification delivery tracking
CREATE TABLE iosapp.push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    match_id UUID REFERENCES iosapp.job_matches(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'job_match', 'daily_digest', 'system'
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    apns_response JSONB,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processed jobs tracking (prevent duplicate notifications)
CREATE TABLE iosapp.processed_jobs (
    device_id UUID NOT NULL REFERENCES iosapp.device_tokens(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (device_id, job_id)
);

-- Performance indexes
CREATE INDEX idx_device_tokens_active ON iosapp.device_tokens(is_active, created_at);
CREATE INDEX idx_device_tokens_token ON iosapp.device_tokens(device_token);

CREATE INDEX idx_keyword_subscriptions_device ON iosapp.keyword_subscriptions(device_id, is_active);
CREATE INDEX idx_keyword_subscriptions_keywords ON iosapp.keyword_subscriptions USING GIN(keywords);

CREATE INDEX idx_job_matches_device_created ON iosapp.job_matches(device_id, created_at DESC);
CREATE INDEX idx_job_matches_subscription ON iosapp.job_matches(subscription_id, created_at DESC);
CREATE INDEX idx_job_matches_unread ON iosapp.job_matches(device_id, is_read, created_at DESC);

CREATE INDEX idx_push_notifications_device ON iosapp.push_notifications(device_id, created_at DESC);
CREATE INDEX idx_push_notifications_status ON iosapp.push_notifications(status, created_at);

CREATE INDEX idx_processed_jobs_lookup ON iosapp.processed_jobs(device_id, job_id);

-- Create updated_at trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_device_tokens_updated_at 
    BEFORE UPDATE ON iosapp.device_tokens 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_keyword_subscriptions_updated_at 
    BEFORE UPDATE ON iosapp.keyword_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();