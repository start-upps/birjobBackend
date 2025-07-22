CREATE TABLE IF NOT EXISTS iosapp.job_match_sessions (
    session_id VARCHAR(50) NOT NULL UNIQUE,
    device_id UUID NOT NULL,
    total_matches INTEGER NOT NULL,
    matched_keywords JSONB NOT NULL,
    notification_sent BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (session_id),
    FOREIGN KEY (device_id) REFERENCES iosapp.device_users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS iosapp.job_match_session_jobs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    job_hash VARCHAR(32) NOT NULL,
    job_title VARCHAR(500) NOT NULL,
    job_company VARCHAR(200) NOT NULL,
    job_source VARCHAR(100) NOT NULL,
    apply_link TEXT,
    job_data JSONB NOT NULL,
    match_score INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES iosapp.job_match_sessions(session_id) ON DELETE CASCADE,
    UNIQUE(session_id, job_hash)
);

CREATE INDEX IF NOT EXISTS idx_job_match_sessions_device_id ON iosapp.job_match_sessions(device_id);

CREATE INDEX IF NOT EXISTS idx_job_match_sessions_created_at ON iosapp.job_match_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_job_match_session_jobs_session_id ON iosapp.job_match_session_jobs(session_id);

CREATE INDEX IF NOT EXISTS idx_job_match_session_jobs_match_score ON iosapp.job_match_session_jobs(match_score DESC);

-- Verify tables were created (commented out for migration)
-- SELECT 'job_match_sessions' as table_name, COUNT(*) as row_count FROM iosapp.job_match_sessions
-- UNION ALL
-- SELECT 'job_match_session_jobs' as table_name, COUNT(*) as row_count FROM iosapp.job_match_session_jobs;