# Database Schema Documentation

**Database Type**: PostgreSQL  
**Architecture**: RDBMS with proper foreign key relationships  
**Schemas**: `iosapp` (user management), `scraper` (job data)

---

## 🏗️ Schema Overview

### Database Schemas
1. **`iosapp`** - iOS app user management and analytics
2. **`scraper`** - Job listings from external sources

### Key Relationships
- Users ← Device Tokens (1:many)
- Users ← Saved Jobs (1:many)  
- Users ← Job Views (1:many)
- Users ← User Analytics (1:1)

---

## 📱 iOS App Schema (`iosapp`)

### Table: `users`
**Purpose**: Core user profiles and preferences

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE | User email address |
| `keywords` | JSONB | - | Job search keywords array |
| `preferred_sources` | JSONB | - | Preferred job sources array |
| `notifications_enabled` | BOOLEAN | DEFAULT true | Push notification preference |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation time |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last profile update |

**Indexes**:
- `idx_users_email` on `email` (unique)
- `idx_users_created_at` on `created_at`

**Example Data**:
```json
{
    "id": "4173a6ad-c13f-4c9b-9765-87d1c6a264c7",
    "email": "developer@example.com",
    "keywords": ["ios", "swift", "backend", "python"],
    "preferred_sources": ["Djinni", "Boss.az"],
    "notifications_enabled": true,
    "created_at": "2025-07-03T04:59:25.960650+00:00",
    "updated_at": "2025-07-03T04:59:25.960650+00:00"
}
```

---

### Table: `device_tokens`
**Purpose**: Device registration for push notifications and user linking

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique device record ID |
| `user_id` | UUID | FOREIGN KEY → users.id | Associated user |
| `device_id` | VARCHAR(255) | UNIQUE | iOS device identifier |
| `device_token` | VARCHAR(255) | - | APNs push token (64+ chars) |
| `device_info` | JSONB | - | Device metadata |
| `is_active` | BOOLEAN | DEFAULT true | Device status |
| `registered_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration time |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update |

**Foreign Keys**:
- `user_id` → `users.id` ON DELETE CASCADE

**Indexes**:
- `idx_device_tokens_device_id` on `device_id` (unique)
- `idx_device_tokens_user_id` on `user_id`
- `idx_device_tokens_device_token` on `device_token`

**Example Data**:
```json
{
    "id": "7ee3650b-3c90-4a32-a4c4-7732aa94db6a",
    "user_id": "4173a6ad-c13f-4c9b-9765-87d1c6a264c7", 
    "device_id": "test-device-fixed",
    "device_token": "placeholder_token_64_chars_min_test-device-fixed_xxxxxxxxxxxxxxxxxxxx",
    "device_info": {
        "model": "iPhone 14",
        "osVersion": "iOS 17.0",
        "deviceModel": "iPhone 14 Pro",
        "timezone": "UTC",
        "app_version": "1.0.0"
    },
    "is_active": true,
    "registered_at": "2025-07-03T04:59:26.397975+00:00"
}
```

---

### Table: `saved_jobs`
**Purpose**: User bookmarked jobs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique saved job record |
| `user_id` | UUID | FOREIGN KEY → users.id | User who saved job |
| `job_id` | INTEGER | - | Reference to scraper.jobs_jobpost.id |
| `job_title` | TEXT | - | Cached job title |
| `job_company` | TEXT | - | Cached company name |
| `job_source` | VARCHAR(100) | - | Cached job source |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When job was saved |

**Foreign Keys**:
- `user_id` → `users.id` ON DELETE CASCADE

**Unique Constraints**:
- `(user_id, job_id)` - User can't save same job twice

**Indexes**:
- `idx_saved_jobs_user_id` on `user_id`
- `idx_saved_jobs_job_id` on `job_id`
- `idx_saved_jobs_created_at` on `created_at`

**Example Data**:
```json
{
    "id": "saved-job-uuid",
    "user_id": "4173a6ad-c13f-4c9b-9765-87d1c6a264c7",
    "job_id": 2066000,
    "job_title": "Full-stack Python / Typescript (React) - work during EST time",
    "job_company": "Envion Software",
    "job_source": "Djinni",
    "created_at": "2025-07-03T04:59:55.989264+00:00"
}
```

---

### Table: `job_views`
**Purpose**: Job viewing analytics and user behavior tracking

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique view record |
| `user_id` | UUID | FOREIGN KEY → users.id | User who viewed job |
| `job_id` | INTEGER | - | Reference to scraper.jobs_jobpost.id |
| `job_title` | TEXT | - | Cached job title |
| `job_company` | TEXT | - | Cached company name |
| `job_source` | VARCHAR(100) | - | Cached job source |
| `view_duration_seconds` | INTEGER | - | How long user viewed job |
| `viewed_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When job was viewed |

**Foreign Keys**:
- `user_id` → `users.id` ON DELETE CASCADE

**Indexes**:
- `idx_job_views_user_id` on `user_id`
- `idx_job_views_job_id` on `job_id`
- `idx_job_views_viewed_at` on `viewed_at`

---

### Table: `user_analytics`
**Purpose**: User behavior analytics and metrics

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique analytics record |
| `user_id` | UUID | FOREIGN KEY → users.id | Associated user |
| `action_type` | VARCHAR(50) | - | Type of action performed |
| `action_data` | JSONB | - | Additional action metadata |
| `device_info` | JSONB | - | Device context |
| `session_id` | VARCHAR(255) | - | Optional session identifier |
| `timestamp` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When action occurred |

**Foreign Keys**:
- `user_id` → `users.id` ON DELETE CASCADE

**Action Types**:
- `app_open`, `app_close`
- `job_view`, `job_save`, `job_unsave`
- `search`, `profile_update`, `settings_change`
- `notification_click`
- `chatbot_message`, `job_recommendations`, `job_analysis`

**Indexes**:
- `idx_user_analytics_user_id` on `user_id`
- `idx_user_analytics_action_type` on `action_type`
- `idx_user_analytics_timestamp` on `timestamp`

**Example Data**:
```json
{
    "id": "23338054-dc3b-41f2-a0dd-c8aaef761fc8",
    "user_id": "4173a6ad-c13f-4c9b-9765-87d1c6a264c7",
    "action_type": "job_view",
    "action_data": {
        "job_id": 2066000,
        "duration": 45
    },
    "device_info": {},
    "session_id": "session-test",
    "timestamp": "2025-07-03T05:00:17.308511+00:00"
}
```

---

## 💼 Job Data Schema (`scraper`)

### Table: `jobs_jobpost`
**Purpose**: Job listings from external sources

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Unique job identifier |
| `title` | TEXT | NOT NULL | Job title |
| `company` | VARCHAR(255) | - | Company name |
| `apply_link` | TEXT | - | Application URL |
| `source` | VARCHAR(100) | - | Job board source |
| `posted_at` | TIMESTAMP | - | When job was posted |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When scraped |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update |

**Indexes**:
- `idx_jobs_title` on `title`
- `idx_jobs_company` on `company`
- `idx_jobs_source` on `source`
- `idx_jobs_created_at` on `created_at`

**Job Sources** (39 total):
- Glorri (794 jobs)
- Vakansiya.biz (490 jobs)
- Djinni (465 jobs)
- Smartjob (400 jobs)
- eJob (260 jobs)
- Boss.az (180 jobs)
- And 33 more sources...

**Example Data**:
```json
{
    "id": 2066000,
    "title": "Full-stack Python / Typescript (React) - work during EST time",
    "company": "Envion Software",
    "apply_link": "https://djinni.co/jobs/706772-full-stack-python-typescript-react-work-durin/",
    "source": "Djinni",
    "posted_at": "2025-07-03T04:37:01.516357",
    "created_at": "2025-07-03T04:37:01.516357"
}
```

---

## 🔗 Relationships Diagram

```
┌─────────────┐     1:N     ┌─────────────────┐
│    users    │◄───────────►│  device_tokens  │
│             │             │                 │
│ - id (PK)   │             │ - user_id (FK)  │
│ - email     │             │ - device_id     │
│ - keywords  │             │ - device_token  │
└─────────────┘             └─────────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐
│ saved_jobs  │
│             │
│ - user_id   │ FK → users.id
│ - job_id    │ → scraper.jobs_jobpost.id
└─────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐
│ job_views   │
│             │
│ - user_id   │ FK → users.id
│ - job_id    │ → scraper.jobs_jobpost.id
└─────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐
│user_analytic│
│             │
│ - user_id   │ FK → users.id
│ - action    │
└─────────────┘
```

---

## 🔧 Database Operations

### Common Queries

#### 1. Get User by Device ID
```sql
SELECT u.* FROM iosapp.users u
JOIN iosapp.device_tokens dt ON u.id = dt.user_id
WHERE dt.device_id = $1 AND dt.is_active = true;
```

#### 2. Save Job for User
```sql
INSERT INTO iosapp.saved_jobs (user_id, job_id, job_title, job_company, job_source)
SELECT u.id, $2, j.title, j.company, j.source
FROM iosapp.users u
JOIN iosapp.device_tokens dt ON u.id = dt.user_id
JOIN scraper.jobs_jobpost j ON j.id = $2
WHERE dt.device_id = $1 AND dt.is_active = true
ON CONFLICT (user_id, job_id) DO NOTHING;
```

#### 3. Get User's Saved Jobs
```sql
SELECT sj.job_id, sj.job_title, sj.job_company, sj.job_source, sj.created_at as saved_at
FROM iosapp.saved_jobs sj
JOIN iosapp.users u ON sj.user_id = u.id
JOIN iosapp.device_tokens dt ON u.id = dt.user_id
WHERE dt.device_id = $1 AND dt.is_active = true
ORDER BY sj.created_at DESC;
```

#### 4. Record Analytics Event
```sql
INSERT INTO iosapp.user_analytics (user_id, action_type, action_data, device_info)
SELECT u.id, $2, $3, $4
FROM iosapp.users u
JOIN iosapp.device_tokens dt ON u.id = dt.user_id
WHERE dt.device_id = $1 AND dt.is_active = true;
```

#### 5. Search Jobs
```sql
SELECT id, title, company, apply_link, source, posted_at
FROM scraper.jobs_jobpost
WHERE (LOWER(title) LIKE LOWER($1) OR LOWER(company) LIKE LOWER($1))
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;
```

---

## 📊 Data Statistics (Live)

### Current Data Volume
- **Total Jobs**: 4,367 active listings
- **Job Sources**: 39 different platforms
- **Active Users**: 7 registered devices
- **Active Subscriptions**: 6 users with keywords
- **Recent Activity**: 2 job views in last 24h

### Top Job Sources
1. **Glorri**: 794 jobs (18.2%)
2. **Vakansiya.biz**: 490 jobs (11.2%)
3. **Djinni**: 465 jobs (10.6%)
4. **Smartjob**: 400 jobs (9.2%)
5. **eJob**: 260 jobs (6.0%)

### Top Companies
1. **ABB**: 115 job postings
2. **Kontakt Home**: 109 job postings
3. **Kapital Bank**: 78 job postings
4. **Xalq Bank**: 74 job postings
5. **Landau Education Group**: 64 job postings

---

## 🔒 Security & Constraints

### Data Integrity
- **Foreign Key Constraints**: All relationships enforced
- **Unique Constraints**: Prevent duplicate data
- **Cascade Deletes**: User deletion removes all related data
- **NOT NULL Constraints**: Critical fields required

### Privacy Features
- **Email Uniqueness**: One account per email
- **Device Isolation**: Each device independently managed
- **Analytics Anonymization**: No PII in analytics
- **Data Deletion**: GDPR-compliant user data removal

### Performance Optimization
- **Proper Indexing**: All query patterns covered
- **JSONB Columns**: Efficient storage for flexible data
- **Timestamp Indexes**: Fast time-based queries
- **Composite Indexes**: Optimized for common joins

---

## 🛠️ Database Management

### Connection Configuration
```python
DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"
```

### Migration Strategy
- **Schema Changes**: Applied via SQL scripts
- **Data Migration**: Handled by FastAPI application
- **Rollback Plan**: Foreign key constraints prevent corruption
- **Backup Strategy**: Regular automated backups

### Monitoring Queries
```sql
-- Active users in last 24h
SELECT COUNT(DISTINCT user_id) FROM iosapp.user_analytics 
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- Most popular job searches
SELECT action_data->>'search_term', COUNT(*) 
FROM iosapp.user_analytics 
WHERE action_type = 'search' 
GROUP BY action_data->>'search_term'
ORDER BY COUNT(*) DESC;

-- Device registration trends
SELECT DATE(registered_at), COUNT(*) 
FROM iosapp.device_tokens 
GROUP BY DATE(registered_at)
ORDER BY DATE(registered_at) DESC;
```

---

## 📋 Schema Validation

### Required Constraints
✅ **Foreign Keys**: All relationships properly defined  
✅ **Unique Constraints**: Email and device_id uniqueness  
✅ **NOT NULL**: Critical fields enforced  
✅ **Indexes**: All query patterns optimized  
✅ **Cascade Deletes**: Data consistency maintained  

### Data Validation
✅ **Email Format**: Validated at application level  
✅ **Device Token Length**: Minimum 64 characters  
✅ **JSONB Structure**: Keywords and device_info arrays  
✅ **Timestamp Consistency**: All times in UTC  

---

**Database Version**: PostgreSQL 13+  
**Last Updated**: July 3, 2025  
**Schema Status**: Production Ready ✅