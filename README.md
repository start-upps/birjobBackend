# iOS Backend API for Job Matching App

## Overview for AI Assistant

This is a FastAPI backend for an iOS job matching application. The system has **4,427 jobs** from 36+ job boards and provides real-time push notifications when jobs match user keywords.

**Live API**: `https://birjobbackend-ir3e.onrender.com`

## Core Functionality

1. **Device Management** - Register iOS devices for push notifications
2. **Keyword Subscriptions** - Users subscribe to job keywords (Python, iOS, etc.)
3. **Job Database** - Browse all available jobs with search/filtering
4. **Job Matching** - System finds jobs matching user keywords
5. **Push Notifications** - Apple Push Notifications when matches found
6. **User Profile Management** - Complete user profiles with skills, preferences, and saved jobs
7. **AI-Powered Features** - Job advice, resume review, and personalized recommendations
8. **Analytics & Insights** - Job market analysis, keyword trends, and user analytics

## Database Structure

### iOS App Schema (`iosapp`)
- `device_tokens` - Registered iOS devices
- `keyword_subscriptions` - User keyword preferences  
- `job_matches` - Jobs that matched user keywords
- `push_notifications` - Notification delivery tracking
- `processed_jobs` - Prevents duplicate notifications
- `user_profiles` - Complete user profiles with skills and preferences
- `saved_jobs` - User's favorite/saved jobs
- `job_applications` - Application history tracking
- `user_analytics` - User activity and engagement metrics

### Existing Job Data (`scraper` schema)
- `jobs_jobpost` - 4,427 jobs from 36+ sources (Glorri, Djinni, etc.)
  - Available fields: `id`, `title`, `company`, `apply_link`, `source`, `created_at`

## Complete API Endpoints

### Device Management

#### `POST /api/v1/devices/register`
Register iOS device for notifications.
```json
{
  "device_token": "apple_device_token_here",
  "device_info": {
    "os_version": "17.2",
    "app_version": "1.0.0", 
    "device_model": "iPhone15,2"
  }
}
```
**Response**: `{"data": {"device_id": "uuid", "registered_at": "timestamp"}}`

#### `DELETE /api/v1/devices/{device_id}`
Unregister device.
**Response**: `{"message": "Device unregistered successfully"}`

#### `GET /api/v1/devices/{device_id}/status`
Get device status and info.
**Response**: Device details including registration time, active status.

### Keyword Subscriptions

#### `POST /api/v1/keywords`
Subscribe to job keywords.
```json
{
  "device_id": "uuid-from-registration",
  "keywords": ["Python", "iOS Developer", "Remote"],
  "sources": ["Glorri", "Djinni", "Vakansiya.biz"]
}
```
**Response**: `{"data": {"subscription_id": "uuid", "keywords_count": 3}}`

#### `GET /api/v1/keywords/{device_id}`
Get all subscriptions for device.
**Response**: List of all keyword subscriptions.

#### `PUT /api/v1/keywords/{subscription_id}`
Update subscription (same body as POST).

#### `DELETE /api/v1/keywords/{subscription_id}?device_id={device_id}`
Remove subscription.

### Job Database

#### `GET /api/v1/jobs/`
Browse all jobs with filtering.
**Query Parameters**:
- `limit` (1-100, default 20)
- `offset` (pagination)
- `search` (search title/company)
- `company` (filter by company)
- `source` (filter by job board)
- `days` (jobs from last N days)
- `sort_by` (created_at, title, company)
- `sort_order` (asc/desc)

**Note**: No location column exists in database. Location searches work by searching within title/company fields.

**Example**: `/api/v1/jobs/?search=developer&company=ABB&limit=5`

**Response**: 
```json
{
  "data": {
    "jobs": [
      {
        "id": 369139,
        "title": "Python Developer",
        "company": "TechCorp",
        "apply_link": "https://jobs.glorri.az/vacancies/...",
        "source": "Glorri",
        "posted_at": "2025-06-13T05:26:27.182789"
      }
    ],
    "pagination": {
      "total": 4427,
      "limit": 5,
      "current_page": 1,
      "has_more": true
    }
  }
}
```

#### `GET /api/v1/jobs/{job_id}`
Get specific job details.

#### `GET /api/v1/jobs/stats/summary`
Get job statistics.
**Response**: Total jobs, recent jobs, top companies, job sources.

### Job Matching

#### `GET /api/v1/matches/{device_id}`
Get job matches for device.
**Query Parameters**: `limit`, `offset`, `since` (timestamp)

**Response**:
```json
{
  "data": {
    "matches": [
      {
        "match_id": "uuid",
        "job": { "id": 123, "title": "...", "company": "..." },
        "matched_keywords": ["Python", "Senior"],
        "relevance_score": 0.85,
        "matched_at": "timestamp"
      }
    ],
    "pagination": { "total": 45, "has_more": true }
  }
}
```

#### `POST /api/v1/matches/{match_id}/read?device_id={device_id}`
Mark match as read.

#### `GET /api/v1/matches/{device_id}/unread-count`
Get count of unread matches.

### Analytics & Insights

#### `GET /api/v1/analytics/jobs/overview`
Get overall job market statistics.
**Response**: Total jobs, recent additions, growth trends, source distribution.

#### `GET /api/v1/analytics/jobs/by-source`
Get job distribution by source/job board.
**Response**: Job counts per source with percentages.

#### `GET /api/v1/analytics/jobs/by-company`
Get top companies by job count.
**Query Parameters**: `limit` (default 10)
**Response**: List of companies with job counts.

#### `GET /api/v1/analytics/jobs/current-cycle`
Get current scraping cycle analysis.
**Response**: Current cycle status, recent jobs, processing metrics.

#### `GET /api/v1/analytics/jobs/keywords`
Get popular keywords in job titles.
**Query Parameters**: `limit` (default 20)
**Response**: Most frequently used keywords with counts.

#### `GET /api/v1/analytics/jobs/search`
Search analytics for specific keywords.
**Query Parameters**: `keyword` (required)
**Response**: Jobs matching keyword with relevance scores.

### AI-Powered Features

#### `POST /api/v1/ai/analyze`
General AI analysis endpoint.
```json
{
  "message": "Analyze job market trends for Python developers"
}
```
**Response**: AI-generated analysis and insights.

#### `POST /api/v1/ai/job-advice`
Get AI-powered job search advice.
```json
{
  "message": "How can I improve my chances as a junior developer?"
}
```
**Response**: Personalized job search recommendations.

#### `POST /api/v1/ai/resume-review`
AI resume review and improvement suggestions.
```json
{
  "message": "Review my resume: [resume content]"
}
```
**Response**: Resume feedback and improvement suggestions.

#### `POST /api/v1/ai/job-recommendations`
Get AI job recommendations based on profile.
```json
{
  "message": "Recommend jobs for my Python and React skills"
}
```
**Response**: Personalized job recommendations with explanations.

#### `POST /api/v1/ai/job-match-analysis`
Analyze job compatibility with user profile.
```json
{
  "message": "How well do I match this job: [job description]"
}
```
**Response**: Compatibility analysis with improvement suggestions.

### User Profile Management

#### `POST /api/v1/users/profile`
Create or update user profile.
```json
{
  "deviceId": "uuid-from-registration",
  "profile": {
    "name": "John Doe",
    "email": "john@example.com",
    "skills": ["Python", "React", "Node.js"],
    "experience": "3-5 years",
    "location": "Baku, Azerbaijan",
    "resume_url": "https://...",
    "preferences": {
      "remote_work": true,
      "salary_min": 2000,
      "job_types": ["full-time", "contract"]
    }
  }
}
```
**Response**: Created profile with ID and confirmation.

#### `GET /api/v1/users/profile/{device_id}`
Get user profile by device ID.
**Response**: Complete user profile with all saved data.

#### `POST /api/v1/users/{device_id}/saved-jobs`
Save a job to user's favorites.
```json
{
  "job_id": 123456
}
```
**Response**: Confirmation of saved job.

#### `GET /api/v1/users/{device_id}/saved-jobs`
Get user's saved/favorite jobs.
**Query Parameters**: `limit`, `offset`
**Response**: List of saved jobs with details.

#### `DELETE /api/v1/users/{device_id}/saved-jobs/{job_id}`
Remove job from saved list.
**Response**: Confirmation of removal.

#### `GET /api/v1/users/{device_id}/analytics`
Get user analytics and activity insights.
**Response**: User activity stats, application history, match performance.

#### `POST /api/v1/users/{device_id}/job-views`
Track job view for analytics.
```json
{
  "job_id": 123456,
  "view_duration": 30,
  "source": "search"
}
```
**Response**: View recorded confirmation.

#### `GET /api/v1/users/{device_id}/applications`
Get user's job application history.
**Query Parameters**: `limit`, `offset`, `status`
**Response**: List of job applications with status tracking.

#### `POST /api/v1/users/profile/sync`
Sync user profile between devices.
```json
{
  "primary_device_id": "uuid1",
  "secondary_device_id": "uuid2"
}
```
**Response**: Profile synchronization confirmation.

### Health & Monitoring

#### `GET /api/v1/health`
System health check.
**Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "apns": "healthy",
    "scraper": "healthy"
  },
  "metrics": {
    "active_devices": 8,
    "active_subscriptions": 6,
    "matches_last_24h": 0,
    "notifications_sent_last_24h": 0
  }
}
```

#### `GET /api/v1/health/status/scraper`
Detailed scraper statistics.
**Response**: Scraper performance metrics, recent activity, source status.

#### `POST /api/v1/health/trigger-matching`
Manually trigger the job matching engine.
**Response**: Matching process initiated confirmation.

#### `GET /api/v1/health/scheduler-status`
Get background scheduler status.
**Response**: Scheduler health, next runs, recent activity.

#### `POST /api/v1/health/create-user-tables`
Create user management database tables (production setup).
**Response**: Table creation status and results.

#### `GET /api/v1/health/check-user-tables`
Check if user management tables exist.
**Response**: Table existence status for each required table.

### Root Endpoint

#### `GET /`
API info.
**Response**: `{"message": "iOS Native App Backend API", "version": "1.0.0"}`

## Available Job Sources (36+ boards)

Top sources by job count:
- **Glorri**: 810 jobs
- **Vakansiya.biz**: 689 jobs  
- **Djinni**: 465 jobs
- **Smartjob**: 401 jobs
- **eJob**: 261 jobs
- **Position.az**: 209 jobs
- **Boss.az**: 180 jobs
- **ABB**: 131 jobs
- And 28+ more sources

## Push Notifications

The system uses Apple Push Notification Service (APNs) with:
- Environment variable configuration (private key, team ID, etc.)
- Smart throttling (max 5/hour, 20/day per device)
- Quiet hours (10 PM - 8 AM)
- Job match notifications with deep links

**Notification payload**:
```json
{
  "aps": {
    "alert": {
      "title": "New Job Match! 🎯",
      "subtitle": "Python Developer at TechCorp", 
      "body": "Matches: Python, Senior Developer"
    },
    "badge": 1,
    "sound": "default"
  },
  "custom_data": {
    "type": "job_match",
    "job_id": 12345,
    "matched_keywords": ["Python"],
    "deep_link": "birjob://job/12345"
  }
}
```

## How Matching Works

1. User subscribes to keywords (e.g., "Python", "iOS Developer")
2. Background service runs every 5 minutes
3. Checks new jobs from `scraper.jobs_jobpost` table
4. Matches job titles/companies against user keywords
5. Creates match in `job_matches` table
6. Sends push notification if not in quiet hours
7. Tracks notification delivery

## Technology Stack

- **FastAPI** (Python 3.11)
- **PostgreSQL** (multi-schema: `iosapp` + `scraper`)
- **Redis** (caching, throttling)
- **Apple APNs** (push notifications)
- **Render.com** (deployment)

## Environment Configuration

Required variables:
```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
APNS_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
APNS_KEY_ID=TYV6K8TS9X
APNS_TEAM_ID=KK5HUUQ3HR  
APNS_BUNDLE_ID=com.ismats.birjob
APNS_SANDBOX=true
```

## For iOS App Development

### Typical User Flow:
1. **Register Device**: `POST /api/v1/devices/register`
2. **Create Profile**: `POST /api/v1/users/profile` (skills, preferences, experience)
3. **Subscribe to Keywords**: `POST /api/v1/keywords`  
4. **Browse Jobs**: `GET /api/v1/jobs/` (for main job feed)
5. **View Matches**: `GET /api/v1/matches/{device_id}` (personalized matches)
6. **Save Jobs**: `POST /api/v1/users/{device_id}/saved-jobs`
7. **Get AI Advice**: `POST /api/v1/ai/job-advice` or `POST /api/v1/ai/resume-review`
8. **Track Applications**: `GET /api/v1/users/{device_id}/applications`
9. **Handle Push Notifications**: Deep link to job details

### Deep Linking:
- `birjob://job/{job_id}` - Open specific job
- `birjob://matches` - Open matches screen

### Key Integrations:
- Handle APNs device token registration
- Process push notification payloads
- Implement deep linking for job views
- Show unread match badges

This backend is production-ready with 4,427 live jobs and full push notification support. All endpoints return JSON with consistent `{"success": true, "data": {...}}` format.

## 📁 Project Structure

```
birjobBackend/
├── 📄 application.py          # Main FastAPI app configuration
├── 📄 run.py                  # Production server entry point
├── 📄 requirements.txt        # Python dependencies
├── 📄 render.yaml            # Render.com deployment config
├── 📄 .env                   # Environment variables (not in git)
├── 📄 LICENSE                # MIT License
├── 📄 README.md             # This documentation
├── 📄 quick_test.py         # API testing script
├── 📄 apn.p8                # APNs private key file (fallback)
│
└── 📁 app/                   # Main application package
    ├── 📄 __init__.py
    │
    ├── 📁 api/               # API layer
    │   ├── 📄 __init__.py
    │   └── 📁 v1/            # API version 1
    │       ├── 📄 __init__.py
    │       ├── 📄 router.py   # Main API router setup
    │       └── 📁 endpoints/  # API endpoint implementations
    │           ├── 📄 __init__.py
    │           ├── 📄 devices.py    # Device registration/management
    │           ├── 📄 keywords.py   # Keyword subscriptions
    │           ├── 📄 jobs.py       # Job database queries
    │           ├── 📄 matches.py    # Job matching results
    │           └── 📄 health.py     # System health monitoring
    │
    ├── 📁 core/              # Core system components
    │   ├── 📄 __init__.py
    │   ├── 📄 config.py       # App settings & environment config
    │   ├── 📄 database.py     # PostgreSQL connection & management
    │   ├── 📄 redis_client.py # Redis caching & session management
    │   ├── 📄 security.py     # Security headers & validation
    │   └── 📄 monitoring.py   # Performance metrics & logging
    │
    ├── 📁 models/            # Database models (SQLAlchemy)
    │   ├── 📄 __init__.py
    │   └── 📄 device.py       # iOS app database tables
    │
    ├── 📁 schemas/           # Data validation (Pydantic)
    │   ├── 📄 __init__.py
    │   └── 📄 device.py       # Request/response data models
    │
    └── 📁 services/          # Business logic services
        ├── 📄 __init__.py
        ├── 📄 push_notifications.py  # APNs integration
        └── 📄 match_engine.py        # Job matching algorithms
```

## 📋 File Functions

### **Root Files**
- **`application.py`** - Main FastAPI app setup, CORS, middleware, lifespan events
- **`run.py`** - Production entry point for Render.com deployment
- **`requirements.txt`** - All Python package dependencies
- **`render.yaml`** - Render.com deployment configuration (web service + worker)
- **`quick_test.py`** - Simple API testing script for verification

### **Core System (`app/core/`)**
- **`config.py`** - Environment variables, settings, APNs credentials
- **`database.py`** - PostgreSQL connection, async session management
- **`redis_client.py`** - Redis connection, caching, rate limiting
- **`security.py`** - CORS headers, API key validation, security middleware
- **`monitoring.py`** - Health checks, metrics collection, performance tracking

### **API Layer (`app/api/v1/`)**
- **`router.py`** - Combines all endpoint routers into main API router
- **`endpoints/devices.py`** - iOS device registration, status, deletion
- **`endpoints/keywords.py`** - Keyword subscriptions CRUD operations
- **`endpoints/jobs.py`** - Job database queries, search, filtering, stats
- **`endpoints/matches.py`** - Job matching results, mark as read, unread counts
- **`endpoints/health.py`** - System health, scraper status, metrics

### **Data Layer (`app/models/` & `app/schemas/`)**
- **`models/device.py`** - SQLAlchemy models for `iosapp` schema tables
- **`schemas/device.py`** - Pydantic models for request/response validation

### **Business Logic (`app/services/`)**
- **`push_notifications.py`** - Apple Push Notifications Service integration
- **`match_engine.py`** - Job matching algorithms, background processing

## 🔧 Key Design Patterns

### **Clean Architecture**
- **Separation of concerns** - API, business logic, data access layers
- **Dependency injection** - Database sessions, Redis clients injected
- **Environment-based config** - All settings via environment variables

### **Async/Await Throughout**
- **FastAPI async handlers** - Non-blocking request processing
- **Async database operations** - PostgreSQL with asyncpg
- **Background job processing** - Match engine runs independently

### **Error Handling**
- **Consistent response format** - All endpoints return `{"success": bool, "data": {}}`
- **HTTP status codes** - Proper 200, 400, 404, 500 responses
- **Detailed logging** - All errors logged with context

### **Security**
- **API key authentication** - For admin endpoints
- **Device ID validation** - UUID format checking
- **Rate limiting** - Via Redis counters
- **CORS configuration** - Controlled cross-origin access

This structure makes the codebase maintainable, testable, and scalable for building iOS apps.