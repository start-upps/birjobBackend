# Database Documentation
**Complete Schema Reference for BirJob Backend**

**Database**: PostgreSQL (Neon)  
**Schema**: `iosapp`  
**Last Updated**: June 30, 2025  
**Version**: Optimized RDBMS v2.0

---

## 📋 Table of Contents

1. [Database Overview](#database-overview)
2. [Schema Design Principles](#schema-design-principles)
3. [Table Relationships](#table-relationships)
4. [Complete Table Documentation](#complete-table-documentation)
5. [Foreign Key Relationships](#foreign-key-relationships)
6. [Indexes and Performance](#indexes-and-performance)
7. [Functions and Triggers](#functions-and-triggers)
8. [Common Query Patterns](#common-query-patterns)
9. [Data Migration Guide](#data-migration-guide)
10. [Backup and Maintenance](#backup-and-maintenance)

---

## 🗄️ Database Overview

### Connection Details
```
Host: ep-white-cloud-a2453ie4.eu-central-1.aws.neon.tech
Database: neondb
Schema: iosapp
SSL Mode: require
Port: 5432
```

### Schema Statistics
- **Total Tables**: 9
- **Total Columns**: 132
- **Foreign Key Constraints**: 10
- **Indexes**: 62
- **Functions**: 2
- **Triggers**: 8
- **Views**: 1 (backward compatibility)

---

## 🎯 Schema Design Principles

### 1. **User-Centric Design**
- All data revolves around the central `users` table
- Every table has proper foreign key relationships
- Cascading deletes maintain data integrity

### 2. **JSONB Flexibility**
- Flexible data storage for evolving requirements
- GIN indexes for fast JSON queries
- Backward compatibility for schema changes

### 3. **Performance Optimization**
- Comprehensive indexing strategy
- Partitioning-ready structure
- Query optimization through proper relationships

### 4. **Data Integrity**
- Foreign key constraints enforce relationships
- Check constraints validate data ranges
- Triggers maintain calculated fields automatically

---

## 🔗 Table Relationships

### Entity Relationship Diagram (Text Format)

```
┌─────────────────┐
│     users       │ (CENTRAL TABLE)
│  Primary Key    │
│  - id (UUID)    │
│  - device_id    │
└─────────┬───────┘
          │
          │ (1:N relationships)
          │
    ┌─────┴──────┬──────────┬─────────────┬──────────────┬───────────────┬────────────┬─────────────┐
    │            │          │             │              │               │            │             │
    ▼            ▼          ▼             ▼              ▼               ▼            ▼             ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
│device_  │ │keyword_  │ │job_      │ │saved_jobs   │ │job_          │ │job_     │ │push_    │ │user_     │
│tokens   │ │subscript-│ │matches   │ │             │ │applications  │ │views    │ │notific- │ │analytics │
│         │ │ions      │ │          │ │             │ │              │ │         │ │ations   │ │          │
└─────────┘ └──────────┘ └────┬─────┘ └─────────────┘ └──────────────┘ └─────────┘ └────┬────┘ └──────────┘
                              │                                                         │
                              └─────────────────────────────────────────────────────────┘
                                        (job_matches.id → push_notifications.job_match_id)
```

---

## 📊 Complete Table Documentation

### 1. **users** (Primary Table)
**Purpose**: Central user management and profile storage  
**Row Count**: Variable (clean slate after optimization)  
**Primary Key**: `id` (UUID)  
**Unique Keys**: `device_id`

#### Schema Definition
```sql
CREATE TABLE iosapp.users (
    -- Primary Identification
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Personal Information (40 points toward profile completeness)
    first_name VARCHAR(100),                    -- 5 points if filled
    last_name VARCHAR(100),                     -- 5 points if filled  
    email VARCHAR(255),                         -- 10 points if filled
    phone VARCHAR(20),                          -- 5 points if filled
    location VARCHAR(255),                      -- 5 points if filled
    current_job_title VARCHAR(255),             -- 10 points if filled
    years_of_experience INTEGER,                -- 5 points if filled
    linkedin_profile VARCHAR(500),              -- 5 points if filled
    portfolio_url VARCHAR(500),                 -- 5 points if filled
    bio TEXT,                                   -- 5 points if filled
    
    -- Job Preferences (40 points toward profile completeness)
    desired_job_types JSONB DEFAULT '[]'::jsonb,        -- 5 points if filled
    remote_work_preference VARCHAR(50) DEFAULT 'hybrid',
    skills JSONB DEFAULT '[]'::jsonb,                    -- 15 points if filled
    preferred_locations JSONB DEFAULT '[]'::jsonb,
    match_keywords JSONB DEFAULT '[]'::jsonb,           -- 15 points if filled
    
    -- Salary Preferences
    min_salary INTEGER,                         -- 5 points if both min/max filled
    max_salary INTEGER,
    salary_currency VARCHAR(10) DEFAULT 'USD',
    salary_negotiable BOOLEAN DEFAULT TRUE,
    
    -- Notification Settings
    job_matches_enabled BOOLEAN DEFAULT TRUE,
    application_reminders_enabled BOOLEAN DEFAULT TRUE,
    weekly_digest_enabled BOOLEAN DEFAULT FALSE,
    market_insights_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_start TIME DEFAULT '22:00',
    quiet_hours_end TIME DEFAULT '08:00',
    preferred_notification_time TIME DEFAULT '09:00',
    
    -- Privacy Settings
    profile_visibility VARCHAR(20) DEFAULT 'private' 
        CHECK (profile_visibility IN ('public', 'private')),
    share_analytics BOOLEAN DEFAULT FALSE,
    share_job_view_history BOOLEAN DEFAULT FALSE,
    allow_personalized_recommendations BOOLEAN DEFAULT TRUE,
    
    -- Profile Metadata
    profile_completeness INTEGER DEFAULT 0 
        CHECK (profile_completeness >= 0 AND profile_completeness <= 100),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Flexible Storage for Future Features
    additional_personal_info JSONB DEFAULT '{}'::jsonb,
    additional_job_preferences JSONB DEFAULT '{}'::jsonb,
    additional_notification_settings JSONB DEFAULT '{}'::jsonb,
    additional_privacy_settings JSONB DEFAULT '{}'::jsonb,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### Key Business Rules
- `device_id` must be unique across all users
- `profile_completeness` is automatically calculated via trigger
- JSONB fields allow for flexible schema evolution
- `updated_at` is automatically updated via trigger

#### Common Queries
```sql
-- Get user by device ID
SELECT * FROM iosapp.users WHERE device_id = 'device_123';

-- Get active users with high profile completeness
SELECT device_id, first_name, last_name, profile_completeness 
FROM iosapp.users 
WHERE is_active = TRUE AND profile_completeness >= 80;

-- Search users by skills
SELECT device_id, skills 
FROM iosapp.users 
WHERE skills @> '["Swift"]'::jsonb;
```

---

### 2. **device_tokens** (Device Management)
**Purpose**: Manage device registration and push notifications  
**Relationship**: Many-to-One with `users`  
**Primary Key**: `id` (UUID)  
**Unique Keys**: `device_token`

#### Schema Definition
```sql
CREATE TABLE iosapp.device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    device_token VARCHAR(255) UNIQUE NOT NULL,          -- APNS token
    device_type VARCHAR(20) DEFAULT 'iOS' 
        CHECK (device_type IN ('iOS', 'Android')),
    device_info JSONB DEFAULT '{}'::jsonb,              -- Device metadata
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT fk_device_tokens_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);
```

#### Device Info JSON Structure
```json
{
  "model": "iPhone 15 Pro",
  "os_version": "17.0",
  "app_version": "1.2.0",
  "timezone": "America/Los_Angeles",
  "screen_size": "6.1 inch",
  "locale": "en_US"
}
```

#### Common Queries
```sql
-- Get active devices for a user
SELECT device_token, device_info, last_seen 
FROM iosapp.device_tokens 
WHERE user_id = 'user_uuid' AND is_active = TRUE;

-- Update device last seen
UPDATE iosapp.device_tokens 
SET last_seen = CURRENT_TIMESTAMP 
WHERE device_token = 'apns_token_here';
```

---

### 3. **keyword_subscriptions** (Search Preferences)
**Purpose**: Store user job search keywords and filters  
**Relationship**: Many-to-One with `users`  
**Primary Key**: `id` (UUID)

#### Schema Definition
```sql
CREATE TABLE iosapp.keyword_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    keywords JSONB NOT NULL DEFAULT '[]'::jsonb,        -- Search keywords array
    location_filters JSONB DEFAULT '{}'::jsonb,         -- Location preferences
    source_filters JSONB DEFAULT '[]'::jsonb,           -- Job board preferences
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT fk_keyword_subscriptions_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);
```

#### Keywords JSON Structure
```json
{
  "keywords": ["ios developer", "swift engineer", "mobile architect"],
  "location_filters": {
    "cities": ["San Francisco", "New York", "Remote"],
    "remote_ok": true,
    "countries": ["US", "CA"],
    "radius_miles": 50
  },
  "source_filters": ["linkedin", "indeed", "glassdoor", "stackoverflow"]
}
```

#### Common Queries
```sql
-- Get user keywords
SELECT keywords, location_filters 
FROM iosapp.keyword_subscriptions 
WHERE user_id = 'user_uuid' AND is_active = TRUE;

-- Find users interested in specific keyword
SELECT u.device_id, ks.keywords 
FROM iosapp.users u
JOIN iosapp.keyword_subscriptions ks ON u.id = ks.user_id
WHERE ks.keywords @> '["ios developer"]'::jsonb;
```

---

### 4. **job_matches** (AI Job Matching)
**Purpose**: Store AI-generated job matches with scoring  
**Relationship**: Many-to-One with `users`  
**Primary Key**: `id` (UUID)  
**Unique Keys**: `(user_id, job_id)`

#### Schema Definition
```sql
CREATE TABLE iosapp.job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    job_id INTEGER NOT NULL,                            -- Reference to external job
    
    -- AI Matching Results
    match_score DECIMAL(5,2) NOT NULL 
        CHECK (match_score >= 0 AND match_score <= 100),
    matched_keywords JSONB DEFAULT '[]'::jsonb,         -- Keywords that matched
    match_reasons JSONB DEFAULT '[]'::jsonb,            -- Why it matched
    keyword_relevance JSONB DEFAULT '{}'::jsonb,        -- Keyword scores
    
    -- User Interaction
    is_read BOOLEAN DEFAULT FALSE,
    is_saved BOOLEAN DEFAULT FALSE,
    is_applied BOOLEAN DEFAULT FALSE,
    user_feedback VARCHAR(20) 
        CHECK (user_feedback IN ('like', 'dislike', 'not_interested')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key and Unique Constraints
    CONSTRAINT fk_job_matches_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_user_job_match UNIQUE (user_id, job_id)
);
```

#### Match Data JSON Structure
```json
{
  "matched_keywords": ["ios developer", "swift", "remote"],
  "match_reasons": [
    "Skills perfectly align with requirements",
    "Salary matches expectations", 
    "Remote work preference satisfied"
  ],
  "keyword_relevance": {
    "ios developer": 0.95,
    "swift": 0.87,
    "remote": 0.73
  }
}
```

#### Common Queries
```sql
-- Get top matches for user
SELECT job_id, match_score, matched_keywords, created_at
FROM iosapp.job_matches 
WHERE user_id = 'user_uuid' 
ORDER BY match_score DESC, created_at DESC 
LIMIT 20;

-- Get unread matches
SELECT COUNT(*) as unread_count
FROM iosapp.job_matches 
WHERE user_id = 'user_uuid' AND is_read = FALSE;

-- Update match as read
UPDATE iosapp.job_matches 
SET is_read = TRUE, updated_at = CURRENT_TIMESTAMP
WHERE user_id = 'user_uuid' AND job_id = 12345;
```

---

### 5. **saved_jobs** (User Bookmarks)
**Purpose**: Store user-saved job postings  
**Relationship**: Many-to-One with `users`  
**Primary Key**: `id` (UUID)  
**Unique Keys**: `(user_id, job_id)`

#### Schema Definition
```sql
CREATE TABLE iosapp.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    job_id INTEGER NOT NULL,                            -- Reference to external job
    notes TEXT,                                         -- User notes about job
    application_status VARCHAR(20) DEFAULT 'not_applied' 
        CHECK (application_status IN (
            'not_applied', 'applied', 'interviewing', 
            'offered', 'rejected', 'withdrawn'
        )),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key and Unique Constraints
    CONSTRAINT fk_saved_jobs_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_user_saved_job UNIQUE (user_id, job_id)
);
```

#### Common Queries
```sql
-- Get user's saved jobs
SELECT job_id, notes, application_status, created_at
FROM iosapp.saved_jobs 
WHERE user_id = 'user_uuid' 
ORDER BY created_at DESC;

-- Save a job
INSERT INTO iosapp.saved_jobs (user_id, job_id, notes)
VALUES ('user_uuid', 12345, 'Interesting position at startup')
ON CONFLICT (user_id, job_id) DO NOTHING;

-- Update application status
UPDATE iosapp.saved_jobs 
SET application_status = 'applied', updated_at = CURRENT_TIMESTAMP
WHERE user_id = 'user_uuid' AND job_id = 12345;
```

---

### 6. **job_applications** (Application Tracking)
**Purpose**: Track user job applications and follow-ups  
**Relationship**: Many-to-One with `users`  
**Primary Key**: `id` (UUID)  
**Unique Keys**: `(user_id, job_id)`

#### Schema Definition
```sql
CREATE TABLE iosapp.job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    job_id INTEGER NOT NULL,                            -- Reference to external job
    
    -- Application Details
    application_method VARCHAR(50),                     -- How they applied
    application_status VARCHAR(20) DEFAULT 'submitted'
        CHECK (application_status IN (
            'submitted', 'reviewing', 'interviewing', 
            'offered', 'rejected', 'withdrawn'
        )),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Follow-up Tracking
    follow_up_date DATE,
    interview_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    
    -- External References
    external_application_id VARCHAR(255),               -- Company's tracking ID
    application_url VARCHAR(500),                       -- Link to application
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key and Unique Constraints
    CONSTRAINT fk_job_applications_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_user_job_application UNIQUE (user_id, job_id)
);
```

#### Common Queries
```sql
-- Get user's applications
SELECT job_id, application_status, applied_at, interview_date
FROM iosapp.job_applications 
WHERE user_id = 'user_uuid' 
ORDER BY applied_at DESC;

-- Track applications by status
SELECT application_status, COUNT(*) as count
FROM iosapp.job_applications 
WHERE user_id = 'user_uuid'
GROUP BY application_status;

-- Applications needing follow-up
SELECT job_id, follow_up_date, notes
FROM iosapp.job_applications 
WHERE user_id = 'user_uuid' 
  AND follow_up_date <= CURRENT_DATE 
  AND application_status IN ('submitted', 'reviewing');
```

---

### 7. **job_views** (Analytics Tracking)
**Purpose**: Track user job viewing behavior for analytics  
**Relationship**: Many-to-One with `users`  
**Primary Key**: `id` (UUID)

#### Schema Definition
```sql
CREATE TABLE iosapp.job_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    job_id INTEGER NOT NULL,                            -- Reference to external job
    
    -- View Analytics
    view_duration INTEGER,                              -- Seconds spent viewing
    view_source VARCHAR(50),                            -- Where they found job
    device_type VARCHAR(20),                            -- Device used
    view_location VARCHAR(255),                         -- User location
    
    -- Timestamp
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraint
    CONSTRAINT fk_job_views_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);
```

#### View Source Values
- `search` - Found through search
- `match` - From job matching algorithm
- `saved` - Viewed saved job
- `recommendation` - AI recommendation
- `notification` - Push notification click

#### Common Queries
```sql
-- User viewing patterns
SELECT view_source, COUNT(*) as views, AVG(view_duration) as avg_duration
FROM iosapp.job_views 
WHERE user_id = 'user_uuid' 
GROUP BY view_source;

-- Recently viewed jobs
SELECT job_id, view_duration, viewed_at
FROM iosapp.job_views 
WHERE user_id = 'user_uuid' 
ORDER BY viewed_at DESC 
LIMIT 10;

-- Track job engagement
INSERT INTO iosapp.job_views (user_id, job_id, view_duration, view_source)
VALUES ('user_uuid', 12345, 45, 'match');
```

---

### 8. **push_notifications** (Notification History)
**Purpose**: Track push notification delivery and engagement  
**Relationship**: Many-to-One with `users`, `device_tokens`, `job_matches`  
**Primary Key**: `id` (UUID)

#### Schema Definition
```sql
CREATE TABLE iosapp.push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    device_token_id UUID,                               -- FK to device_tokens.id
    
    -- Notification Content
    notification_type VARCHAR(50) NOT NULL,             -- Type of notification
    title VARCHAR(255) NOT NULL,                        -- Notification title
    body TEXT NOT NULL,                                 -- Notification body
    payload JSONB DEFAULT '{}'::jsonb,                  -- Additional data
    
    -- Related Entities
    job_match_id UUID,                                  -- FK to job_matches.id
    job_id INTEGER,                                     -- Direct job reference
    
    -- Delivery Tracking
    status VARCHAR(20) DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'clicked')),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    CONSTRAINT fk_push_notifications_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_push_notifications_device_token 
        FOREIGN KEY (device_token_id) REFERENCES iosapp.device_tokens(id) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_push_notifications_job_match 
        FOREIGN KEY (job_match_id) REFERENCES iosapp.job_matches(id) 
        ON DELETE SET NULL ON UPDATE CASCADE
);
```

#### Notification Types
- `job_match` - New job match found
- `application_reminder` - Remind to apply
- `weekly_digest` - Weekly summary
- `market_insights` - Market updates
- `system` - App updates/announcements

#### Payload JSON Structure
```json
{
  "job_id": 12345,
  "match_score": 89.5,
  "company": "TechCorp",
  "deep_link": "birjob://job/12345",
  "badge_count": 3
}
```

#### Common Queries
```sql
-- Get notification history
SELECT notification_type, title, status, sent_at, clicked_at
FROM iosapp.push_notifications 
WHERE user_id = 'user_uuid' 
ORDER BY created_at DESC 
LIMIT 50;

-- Track notification engagement
SELECT notification_type, 
       COUNT(*) as sent,
       COUNT(clicked_at) as clicked,
       ROUND(COUNT(clicked_at)::DECIMAL / COUNT(*) * 100, 2) as click_rate
FROM iosapp.push_notifications 
WHERE status = 'sent' 
GROUP BY notification_type;

-- Failed notifications
SELECT device_token_id, error_message, COUNT(*)
FROM iosapp.push_notifications 
WHERE status = 'failed' 
GROUP BY device_token_id, error_message;
```

---

### 9. **user_analytics** (User Insights)
**Purpose**: Store computed user insights and recommendations  
**Relationship**: One-to-One with `users`  
**Primary Key**: `id` (UUID)  
**Unique Keys**: `user_id`

#### Schema Definition
```sql
CREATE TABLE iosapp.user_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                              -- FK to users.id
    
    -- Profile Insights (0-100 scores)
    profile_strength INTEGER DEFAULT 0 
        CHECK (profile_strength >= 0 AND profile_strength <= 100),
    market_fit_score INTEGER DEFAULT 0 
        CHECK (market_fit_score >= 0 AND market_fit_score <= 100),
    
    -- Activity Metrics
    total_jobs_viewed INTEGER DEFAULT 0,
    total_jobs_saved INTEGER DEFAULT 0,
    total_applications INTEGER DEFAULT 0,
    total_matches_received INTEGER DEFAULT 0,
    average_view_time_seconds INTEGER DEFAULT 0,
    
    -- Matching Insights
    average_match_score DECIMAL(5,2) DEFAULT 0,
    top_match_score DECIMAL(5,2) DEFAULT 0,
    total_keywords INTEGER DEFAULT 0,
    
    -- AI-Generated Recommendations (JSONB for flexibility)
    skill_recommendations JSONB DEFAULT '[]'::jsonb,
    top_matching_companies JSONB DEFAULT '[]'::jsonb,
    recommended_job_types JSONB DEFAULT '[]'::jsonb,
    market_insights JSONB DEFAULT '{}'::jsonb,
    improvement_suggestions JSONB DEFAULT '[]'::jsonb,
    
    -- Computation Metadata
    last_computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    computation_version VARCHAR(10) DEFAULT '1.0',
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key and Unique Constraints
    CONSTRAINT fk_user_analytics_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT unique_user_analytics UNIQUE (user_id)
);
```

#### Analytics JSON Structure
```json
{
  "skill_recommendations": [
    {"skill": "SwiftUI", "priority": "high", "market_demand": 89},
    {"skill": "Combine", "priority": "medium", "market_demand": 76}
  ],
  "top_matching_companies": [
    {"company": "Apple", "match_score": 92, "avg_salary": 165000},
    {"company": "Uber", "match_score": 87, "avg_salary": 155000}
  ],
  "market_insights": {
    "salary_percentile": 75,
    "skill_demand_trend": "increasing",
    "recommended_locations": ["San Francisco", "Seattle"]
  },
  "improvement_suggestions": [
    "Add portfolio projects to increase profile strength",
    "Consider learning SwiftUI for better job matches"
  ]
}
```

#### Common Queries
```sql
-- Get user analytics
SELECT profile_strength, market_fit_score, 
       total_jobs_viewed, average_match_score,
       skill_recommendations
FROM iosapp.user_analytics 
WHERE user_id = 'user_uuid';

-- Users needing analytics update
SELECT user_id, last_computed_at
FROM iosapp.user_analytics 
WHERE last_computed_at < CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Top performing users
SELECT u.device_id, ua.profile_strength, ua.market_fit_score
FROM iosapp.user_analytics ua
JOIN iosapp.users u ON ua.user_id = u.id
WHERE ua.profile_strength >= 80
ORDER BY ua.market_fit_score DESC;
```

---

## 🔗 Foreign Key Relationships

### Complete Relationship Map

```sql
-- Users is the central table (no foreign keys)
users (id) <- [PARENT TABLE]

-- All other tables reference users
device_tokens (user_id) -> users (id)
keyword_subscriptions (user_id) -> users (id) 
job_matches (user_id) -> users (id)
saved_jobs (user_id) -> users (id)
job_applications (user_id) -> users (id)
job_views (user_id) -> users (id)
push_notifications (user_id) -> users (id)
user_analytics (user_id) -> users (id)

-- Additional cross-table relationships
push_notifications (device_token_id) -> device_tokens (id)
push_notifications (job_match_id) -> job_matches (id)
```

### Cascade Behavior

**ON DELETE CASCADE**: When a user is deleted, all related data is automatically removed
**ON UPDATE CASCADE**: When a user ID changes, all references are updated automatically
**ON DELETE SET NULL**: Optional references are set to NULL when target is deleted

### Adding New Tables

When adding new tables, follow this pattern:
```sql
CREATE TABLE iosapp.new_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    -- other columns...
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_new_table_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);
```

---

## 📈 Indexes and Performance

### Index Categories

#### 1. **Primary Key Indexes** (Automatic)
Every table has a primary key index on the `id` column.

#### 2. **Foreign Key Indexes** (Manual)
```sql
-- Device tokens
CREATE INDEX idx_device_tokens_user_id ON iosapp.device_tokens(user_id);

-- Job matches  
CREATE INDEX idx_job_matches_user_id ON iosapp.job_matches(user_id);
CREATE INDEX idx_job_matches_job_id ON iosapp.job_matches(job_id);

-- All other foreign key columns have similar indexes
```

#### 3. **JSONB GIN Indexes** (High Performance)
```sql
-- User skills and keywords
CREATE INDEX idx_users_skills_gin ON iosapp.users USING GIN (skills);
CREATE INDEX idx_users_match_keywords_gin ON iosapp.users USING GIN (match_keywords);

-- Keyword subscriptions
CREATE INDEX idx_keyword_subscriptions_keywords_gin ON iosapp.keyword_subscriptions USING GIN (keywords);
```

#### 4. **Composite Indexes** (Query Optimization)
```sql
-- Common user queries
CREATE INDEX idx_users_job_search ON iosapp.users(current_job_title, location, years_of_experience);
CREATE INDEX idx_users_notifications ON iosapp.users(job_matches_enabled, application_reminders_enabled) WHERE is_active = TRUE;

-- Job matching queries
CREATE INDEX idx_job_matches_unread ON iosapp.job_matches(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_job_matches_score ON iosapp.job_matches(match_score DESC);
```

#### 5. **Partial Indexes** (Space Efficient)
```sql
-- Only index active records
CREATE INDEX idx_users_active ON iosapp.users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_device_tokens_active ON iosapp.device_tokens(is_active) WHERE is_active = TRUE;
```

### Performance Tips

1. **Use JSONB with GIN indexes** for flexible queries
2. **Limit SELECT columns** - don't use SELECT * in production
3. **Use LIMIT** for paginated results
4. **Filter by indexed columns** first in WHERE clauses
5. **Use EXPLAIN ANALYZE** to optimize slow queries

---

## ⚙️ Functions and Triggers

### 1. **Automatic Timestamp Updates**

#### Function
```sql
CREATE OR REPLACE FUNCTION iosapp.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

#### Triggers (Applied to all tables with updated_at)
```sql
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON iosapp.users 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();

-- Similar triggers exist for all tables with updated_at column
```

### 2. **Profile Completeness Calculation**

#### Function
```sql
CREATE OR REPLACE FUNCTION iosapp.calculate_profile_completeness()
RETURNS TRIGGER AS $$
DECLARE
    completeness_score INTEGER := 0;
BEGIN
    -- Basic info (40 points max)
    IF NEW.first_name IS NOT NULL AND NEW.first_name != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.last_name IS NOT NULL AND NEW.last_name != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.email IS NOT NULL AND NEW.email != '' THEN 
        completeness_score := completeness_score + 10; 
    END IF;
    IF NEW.location IS NOT NULL AND NEW.location != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.current_job_title IS NOT NULL AND NEW.current_job_title != '' THEN 
        completeness_score := completeness_score + 10; 
    END IF;
    IF NEW.bio IS NOT NULL AND NEW.bio != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    
    -- Job preferences (40 points max)
    IF NEW.skills IS NOT NULL AND jsonb_array_length(NEW.skills) > 0 THEN 
        completeness_score := completeness_score + 15; 
    END IF;
    IF NEW.match_keywords IS NOT NULL AND jsonb_array_length(NEW.match_keywords) > 0 THEN 
        completeness_score := completeness_score + 15; 
    END IF;
    IF NEW.desired_job_types IS NOT NULL AND jsonb_array_length(NEW.desired_job_types) > 0 THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.min_salary IS NOT NULL AND NEW.max_salary IS NOT NULL THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    
    -- Additional info (20 points max)  
    IF NEW.linkedin_profile IS NOT NULL AND NEW.linkedin_profile != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.portfolio_url IS NOT NULL AND NEW.portfolio_url != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.years_of_experience IS NOT NULL THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    IF NEW.phone IS NOT NULL AND NEW.phone != '' THEN 
        completeness_score := completeness_score + 5; 
    END IF;
    
    NEW.profile_completeness := completeness_score;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

#### Trigger
```sql
CREATE TRIGGER calculate_profile_completeness_trigger 
    BEFORE INSERT OR UPDATE ON iosapp.users 
    FOR EACH ROW EXECUTE FUNCTION iosapp.calculate_profile_completeness();
```

---

## 🔍 Common Query Patterns

### User Management Queries

```sql
-- Create/Update User Profile (UPSERT)
INSERT INTO iosapp.users (device_id, first_name, last_name, email, skills)
VALUES ('device_123', 'John', 'Doe', 'john@email.com', '["Swift", "iOS"]'::jsonb)
ON CONFLICT (device_id) 
DO UPDATE SET 
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    email = EXCLUDED.email,
    skills = EXCLUDED.skills,
    updated_at = CURRENT_TIMESTAMP;

-- Get Complete User Profile
SELECT u.*, 
       COALESCE(ua.profile_strength, 0) as profile_strength,
       COALESCE(ua.market_fit_score, 0) as market_fit_score
FROM iosapp.users u
LEFT JOIN iosapp.user_analytics ua ON u.id = ua.user_id
WHERE u.device_id = 'device_123';

-- Search Users by Skills
SELECT device_id, first_name, last_name, skills
FROM iosapp.users 
WHERE skills @> '["Swift"]'::jsonb 
  AND is_active = TRUE;
```

### Job Matching Queries

```sql
-- Get User's Top Job Matches
SELECT jm.job_id, jm.match_score, jm.matched_keywords, 
       jm.is_read, jm.is_saved, jm.created_at
FROM iosapp.job_matches jm
JOIN iosapp.users u ON jm.user_id = u.id
WHERE u.device_id = 'device_123'
  AND jm.match_score >= 70
ORDER BY jm.match_score DESC, jm.created_at DESC
LIMIT 20;

-- Mark Matches as Read
UPDATE iosapp.job_matches 
SET is_read = TRUE, updated_at = CURRENT_TIMESTAMP
WHERE user_id = (SELECT id FROM iosapp.users WHERE device_id = 'device_123')
  AND job_id IN (12345, 12346, 12347);

-- Get Match Statistics
SELECT COUNT(*) as total_matches,
       COUNT(*) FILTER (WHERE is_read = FALSE) as unread_matches,
       COUNT(*) FILTER (WHERE is_saved = TRUE) as saved_matches,
       AVG(match_score) as average_score,
       MAX(match_score) as best_score
FROM iosapp.job_matches jm
JOIN iosapp.users u ON jm.user_id = u.id
WHERE u.device_id = 'device_123';
```

### Analytics Queries

```sql
-- User Activity Summary
SELECT u.device_id,
       COUNT(jv.id) as jobs_viewed,
       COUNT(sj.id) as jobs_saved,
       COUNT(ja.id) as applications_sent,
       AVG(jv.view_duration) as avg_view_time
FROM iosapp.users u
LEFT JOIN iosapp.job_views jv ON u.id = jv.user_id
LEFT JOIN iosapp.saved_jobs sj ON u.id = sj.user_id  
LEFT JOIN iosapp.job_applications ja ON u.id = ja.user_id
WHERE u.device_id = 'device_123'
GROUP BY u.device_id;

-- Top Keywords Across All Users
SELECT keyword, COUNT(*) as user_count
FROM iosapp.users u,
     jsonb_array_elements_text(u.match_keywords) as keyword
WHERE u.is_active = TRUE
GROUP BY keyword
ORDER BY user_count DESC
LIMIT 20;

-- Push Notification Performance
SELECT pn.notification_type,
       COUNT(*) as sent_count,
       COUNT(pn.clicked_at) as clicked_count,
       ROUND(
           COUNT(pn.clicked_at)::DECIMAL / COUNT(*) * 100, 2
       ) as click_rate_percent
FROM iosapp.push_notifications pn
WHERE pn.status = 'sent'
  AND pn.sent_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY pn.notification_type
ORDER BY click_rate_percent DESC;
```

### Device Management Queries

```sql
-- Register/Update Device
INSERT INTO iosapp.device_tokens (user_id, device_token, device_info)
VALUES (
    (SELECT id FROM iosapp.users WHERE device_id = 'device_123'),
    'apns_token_here',
    '{"model": "iPhone 15", "os_version": "17.0"}'::jsonb
)
ON CONFLICT (device_token)
DO UPDATE SET 
    device_info = EXCLUDED.device_info,
    last_seen = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP;

-- Get Active Devices for User
SELECT device_token, device_info, last_seen
FROM iosapp.device_tokens dt
JOIN iosapp.users u ON dt.user_id = u.id
WHERE u.device_id = 'device_123'
  AND dt.is_active = TRUE;
```

---

## 🔄 Data Migration Guide

### Adding New Columns

```sql
-- Always add new columns as nullable first
ALTER TABLE iosapp.users ADD COLUMN new_field VARCHAR(255);

-- Add default value if needed
ALTER TABLE iosapp.users ALTER COLUMN new_field SET DEFAULT 'default_value';

-- Populate existing data if needed
UPDATE iosapp.users SET new_field = 'some_value' WHERE new_field IS NULL;

-- Make NOT NULL if required (after populating)
ALTER TABLE iosapp.users ALTER COLUMN new_field SET NOT NULL;
```

### Adding New JSONB Fields

```sql
-- Add new JSONB field
ALTER TABLE iosapp.users ADD COLUMN new_json_field JSONB DEFAULT '{}'::jsonb;

-- Create GIN index for performance
CREATE INDEX idx_users_new_json_field_gin ON iosapp.users USING GIN (new_json_field);

-- Update existing records to include new structure
UPDATE iosapp.users 
SET new_json_field = '{
    "new_property": "default_value",
    "another_property": []
}'::jsonb
WHERE new_json_field = '{}'::jsonb;
```

### Adding New Tables

```sql
-- Follow the established pattern
CREATE TABLE iosapp.new_feature_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    feature_data JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_new_feature_table_user 
        FOREIGN KEY (user_id) REFERENCES iosapp.users(id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Add indexes
CREATE INDEX idx_new_feature_table_user_id ON iosapp.new_feature_table(user_id);
CREATE INDEX idx_new_feature_table_active ON iosapp.new_feature_table(is_active) WHERE is_active = TRUE;

-- Add trigger for updated_at
CREATE TRIGGER update_new_feature_table_updated_at 
    BEFORE UPDATE ON iosapp.new_feature_table 
    FOR EACH ROW EXECUTE FUNCTION iosapp.update_updated_at_column();
```

---

## 🔧 Backup and Maintenance

### Regular Maintenance Tasks

#### 1. **Analyze Table Statistics** (Weekly)
```sql
ANALYZE iosapp.users;
ANALYZE iosapp.job_matches; 
ANALYZE iosapp.job_views;
-- Analyze all tables to update query planner statistics
```

#### 2. **Vacuum Tables** (Monthly)
```sql
VACUUM ANALYZE iosapp.users;
VACUUM ANALYZE iosapp.job_matches;
-- Reclaim space and update statistics
```

#### 3. **Monitor Index Usage**
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'iosapp'
ORDER BY idx_scan DESC;
```

#### 4. **Check Foreign Key Constraints**
```sql
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint 
WHERE contype = 'f' 
  AND connamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'iosapp');
```

### Backup Procedures

#### 1. **Schema-Only Backup**
```bash
pg_dump -h hostname -U username -d database -n iosapp --schema-only > iosapp_schema.sql
```

#### 2. **Data-Only Backup**
```bash
pg_dump -h hostname -U username -d database -n iosapp --data-only > iosapp_data.sql
```

#### 3. **Complete Backup**
```bash
pg_dump -h hostname -U username -d database -n iosapp > iosapp_complete.sql
```

### Monitoring Queries

#### 1. **Table Sizes**
```sql
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'iosapp'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### 2. **Row Counts**
```sql
SELECT schemaname, tablename,
       n_tup_ins as inserts,
       n_tup_upd as updates, 
       n_tup_del as deletes,
       n_live_tup as live_rows
FROM pg_stat_user_tables 
WHERE schemaname = 'iosapp'
ORDER BY n_live_tup DESC;
```

#### 3. **Long Running Queries**
```sql
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND query LIKE '%iosapp%';
```

---

## 📞 Contact and Support

### Database Team Contacts
- **Database Administrator**: [Your DBA contact]
- **Backend Team Lead**: [Your team lead contact]  
- **DevOps Engineer**: [Your DevOps contact]

### Documentation Updates
This documentation should be updated whenever:
- New tables are added
- Schema changes are made
- New indexes are created
- Business rules change
- Performance optimizations are implemented

### Version History
- **v2.0** (June 30, 2025): Complete RDBMS optimization with foreign keys
- **v1.x** (Previous): Legacy fragmented structure

---

**Last Updated**: June 30, 2025  
**Next Review**: August 1, 2025  
**Document Owner**: Backend Development Team