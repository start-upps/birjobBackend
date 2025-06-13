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

## Database Structure

### iOS App Schema (`iosapp`)
- `device_tokens` - Registered iOS devices
- `keyword_subscriptions` - User keyword preferences  
- `job_matches` - Jobs that matched user keywords
- `push_notifications` - Notification delivery tracking
- `processed_jobs` - Prevents duplicate notifications

### Existing Job Data (`scraper` schema)
- `jobs_jobpost` - 4,427 jobs from 36+ sources (Glorri, Djinni, etc.)

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
  "sources": ["Glorri", "Djinni", "Vakansiya.biz"],
  "location_filters": {
    "cities": ["Baku", "Ganja"],
    "remote_only": true
  }
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
- `location` (filter by location)
- `days` (jobs from last N days)
- `sort_by` (created_at, title, company)
- `sort_order` (asc/desc)

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
        "apply_link": "https://...",
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
2. **Subscribe to Keywords**: `POST /api/v1/keywords`  
3. **Browse Jobs**: `GET /api/v1/jobs/` (for main job feed)
4. **View Matches**: `GET /api/v1/matches/{device_id}` (personalized matches)
5. **Handle Push Notifications**: Deep link to job details

### Deep Linking:
- `birjob://job/{job_id}` - Open specific job
- `birjob://matches` - Open matches screen

### Key Integrations:
- Handle APNs device token registration
- Process push notification payloads
- Implement deep linking for job views
- Show unread match badges

This backend is production-ready with 4,427 live jobs and full push notification support. All endpoints return JSON with consistent `{"success": true, "data": {...}}` format.