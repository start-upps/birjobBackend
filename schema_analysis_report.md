# iOS App Database Schema Analysis Report

**Production Database:** https://birjobbackend-ir3e.onrender.com  
**Schema:** iosapp  
**Analysis Date:** June 30, 2025

## Executive Summary

The `iosapp` schema contains 14 tables with a total of 64 rows across all tables. The schema shows signs of evolution and potential redundancy, with several empty tables and duplicate user management structures.

## 1. Complete Table Inventory

### Active Tables (with data):
- **device_tokens**: 36 rows - Core device registration table
- **keyword_subscriptions**: 1 row - User job search preferences
- **saved_jobs**: 1 row - User saved job postings
- **user_profiles**: 1 row - New unified user profile structure
- **users**: 1 row - Legacy user management table
- **users_legacy_view**: 12 rows - View combining legacy data
- **users_unified**: 12 rows - New unified user management

### Empty Tables (0 rows):
- **job_applications**: Job application tracking
- **job_matches**: AI-powered job matching results
- **job_views**: User job viewing analytics
- **migration_log**: Database migration tracking
- **processed_jobs**: Job processing status tracking
- **push_notifications**: Push notification delivery logs
- **user_analytics**: User behavior analytics

## 2. Detailed Table Structure Analysis

### Core Device Management
```sql
-- device_tokens (36 rows)
CREATE TABLE device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_token VARCHAR(255) NOT NULL UNIQUE,
    device_info JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT now()
);
-- Indexes: device_token (unique), is_active, device_token
```

### User Management (Multiple Tables - Redundancy Issue)

#### Legacy Users Table
```sql
-- users (1 row)
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL UNIQUE,
    -- 33 columns total with full user profile data
    -- Includes: personal info, job preferences, notification settings
);
```

#### New Profiles Table
```sql
-- user_profiles (1 row)
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL UNIQUE,
    personal_info JSONB DEFAULT '{}',
    job_preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    privacy_settings JSONB DEFAULT '{}',
    match_keywords JSONB DEFAULT '[]',
    profile_completeness INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Unified Users Table
```sql
-- users_unified (12 rows)
CREATE TABLE users_unified (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) NOT NULL UNIQUE,
    -- 36 columns with comprehensive user data
    -- Includes additional JSONB fields for extensibility
);
```

### Job Management
```sql
-- keyword_subscriptions (1 row)
CREATE TABLE keyword_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_tokens(id),
    keywords TEXT[] NOT NULL,
    sources TEXT[],
    location_filters JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

### Matching and Notifications System (All Empty)
```sql
-- job_matches (0 rows)
CREATE TABLE job_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_tokens(id),
    job_id VARCHAR NOT NULL,
    matched_keywords TEXT[] NOT NULL,
    relevance_score VARCHAR,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- push_notifications (0 rows)
CREATE TABLE push_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_tokens(id),
    match_id UUID REFERENCES job_matches(id),
    notification_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    apns_response JSONB,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
```

## 3. Foreign Key Relationships

### Relationship Map:
```
device_tokens (36 rows)
├── keyword_subscriptions.device_id (1 row)
├── job_matches.device_id (0 rows)
├── processed_jobs.device_id (0 rows)
└── push_notifications.device_id (0 rows)

users (1 row)
├── job_applications.user_id (0 rows)
├── job_views.user_id (0 rows)
├── saved_jobs.user_id (1 row)
└── user_analytics.user_id (0 rows)

job_matches (0 rows)
└── push_notifications.match_id (0 rows)
```

### Isolated Tables (No Relationships):
- **migration_log**: Database migration tracking
- **users_legacy_view**: View combining legacy data
- **user_profiles**: New profile structure (not connected to main flow)
- **users_unified**: New unified user structure (not connected to main flow)

## 4. Critical Issues Identified

### 🔴 Major Issues:

1. **User Management Redundancy**:
   - Three separate user management systems: `users`, `user_profiles`, `users_unified`
   - No clear primary system being used in production
   - Data inconsistency risk and maintenance overhead

2. **Broken Job Matching Pipeline**:
   - Core matching tables (`job_matches`, `push_notifications`) are empty
   - No actual job matching happening despite having keyword subscriptions
   - Notification system not functioning

3. **Unused Analytics Infrastructure**:
   - `user_analytics`, `job_views`, `job_applications` tables empty
   - No user behavior tracking or insights generation

### 🟡 Moderate Issues:

4. **Schema Evolution Artifacts**:
   - `users_legacy_view` suggests ongoing migration process
   - `migration_log` table empty (no migration tracking)
   - Multiple user table versions suggest incomplete migration

5. **Disconnect Between Device and User Management**:
   - `device_tokens` table (36 rows) vs `users` table (1 row)
   - Most devices not associated with user profiles
   - Job matching uses device-based approach while user features use user-based approach

## 5. Recommendations

### Immediate Actions Required:

1. **Consolidate User Management**:
   ```sql
   -- Recommended approach:
   -- 1. Migrate data from users/user_profiles to users_unified
   -- 2. Update application to use users_unified exclusively
   -- 3. Drop redundant tables after migration
   ```

2. **Fix Job Matching Pipeline**:
   - Investigate why job matching is not producing results
   - Check job scraping and matching engine functionality
   - Verify external job data source connectivity

3. **Establish Primary User System**:
   - Choose `users_unified` as primary user table
   - Create proper foreign key relationships
   - Ensure device-to-user mapping consistency

### Database Optimization:

4. **Remove Redundant Tables**:
   ```sql
   -- After migration, consider dropping:
   -- DROP TABLE users;
   -- DROP TABLE user_profiles;
   -- DROP VIEW users_legacy_view;
   ```

5. **Add Missing Relationships**:
   ```sql
   -- Connect user_profiles/users_unified to device_tokens
   ALTER TABLE device_tokens ADD COLUMN user_id UUID;
   ALTER TABLE device_tokens ADD FOREIGN KEY (user_id) REFERENCES users_unified(id);
   ```

6. **Implement Proper Indexing**:
   - Add composite indexes for frequently queried columns
   - Optimize JSONB field queries with GIN indexes

### Monitoring and Maintenance:

7. **Add Data Validation**:
   - Implement constraints to prevent data inconsistency
   - Add triggers for automatic profile completeness calculation

8. **Enable Migration Tracking**:
   - Start using `migration_log` table for schema changes
   - Implement proper database versioning

## 6. Schema Health Score: 4/10

### Scoring Breakdown:
- **Data Integrity**: 3/10 (Multiple user systems, broken relationships)
- **Functionality**: 2/10 (Core features not working - empty matching tables)
- **Maintenance**: 5/10 (Some good practices but redundant structures)
- **Performance**: 6/10 (Proper indexing but could be optimized)

### Priority Actions:
1. Fix user management redundancy (High Priority)
2. Restore job matching functionality (High Priority)
3. Implement proper foreign key relationships (Medium Priority)
4. Clean up unused/redundant tables (Low Priority)

## 7. Migration Strategy

### Phase 1: Data Consolidation
1. Backup current data
2. Migrate all user data to `users_unified`
3. Update application to use single user table

### Phase 2: Relationship Restoration
1. Connect `device_tokens` to `users_unified`
2. Ensure proper foreign key constraints
3. Test data integrity

### Phase 3: Cleanup
1. Remove redundant tables
2. Optimize indexes
3. Implement monitoring

The schema requires significant cleanup and consolidation to function properly as a production system.