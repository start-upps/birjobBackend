# iOS Backend API Endpoints Demo

## 🚀 API Endpoints Overview

Based on your README specification, here are all the implemented endpoints with example requests and responses:

### 📱 Device Management

#### 1. Register Device
```bash
POST /api/v1/devices/register
```

**Request:**
```json
{
  "device_token": "a1b2c3d4e5f6789012345678901234567890abcdef",
  "device_info": {
    "os_version": "17.2",
    "app_version": "1.0.0",
    "device_model": "iPhone15,2",
    "timezone": "America/New_York"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "registered_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 2. Unregister Device
```bash
DELETE /api/v1/devices/{device_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Device unregistered successfully"
}
```

#### 3. Get Device Status
```bash
GET /api/v1/devices/{device_id}/status
```

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "registered_at": "2024-01-15T10:30:00Z",
    "last_seen": "2024-01-16T14:22:00Z",
    "device_info": {
      "os_version": "17.2",
      "app_version": "1.0.0",
      "device_model": "iPhone15,2",
      "timezone": "America/New_York"
    }
  }
}
```

### 🔍 Keyword Management

#### 4. Create Keyword Subscription
```bash
POST /api/v1/keywords
```

**Request:**
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keywords": ["Python", "Senior Developer", "Remote"],
  "sources": ["linkedin", "indeed", "glassdoor"],
  "location_filters": {
    "cities": ["New York", "San Francisco"],
    "remote_only": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subscription_id": "660e8400-e29b-41d4-a716-446655440001",
    "keywords_count": 3,
    "sources_count": 3,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 5. Get Device Subscriptions
```bash
GET /api/v1/keywords/{device_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "subscription_id": "660e8400-e29b-41d4-a716-446655440001",
        "keywords": ["Python", "Senior Developer"],
        "sources": ["linkedin", "indeed"],
        "location_filters": {
          "cities": ["New York"],
          "remote_only": true
        },
        "created_at": "2024-01-15T10:30:00Z",
        "last_match": "2024-01-16T08:45:00Z"
      }
    ]
  }
}
```

#### 6. Update Subscription
```bash
PUT /api/v1/keywords/{subscription_id}
```

#### 7. Delete Subscription
```bash
DELETE /api/v1/keywords/{subscription_id}?device_id={device_id}
```

### 💼 Job Matching

#### 8. Get Job Matches
```bash
GET /api/v1/matches/{device_id}?limit=20&offset=0&since=2024-01-16T00:00:00Z
```

**Response:**
```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "770e8400-e29b-41d4-a716-446655440002",
        "job": {
          "id": 12345,
          "title": "Senior Python Developer",
          "company": "TechCorp Inc.",
          "apply_link": "https://example.com/apply/12345",
          "source": "linkedin",
          "posted_at": "2024-01-16T08:00:00Z"
        },
        "matched_keywords": ["Python", "Senior Developer"],
        "relevance_score": 0.85,
        "matched_at": "2024-01-16T08:30:00Z"
      },
      {
        "match_id": "880e8400-e29b-41d4-a716-446655440003",
        "job": {
          "id": 12346,
          "title": "Full Stack Engineer - Remote",
          "company": "StartupXYZ",
          "apply_link": "https://example.com/apply/12346",
          "source": "indeed",
          "posted_at": "2024-01-16T09:00:00Z"
        },
        "matched_keywords": ["Python", "Remote"],
        "relevance_score": 0.78,
        "matched_at": "2024-01-16T09:15:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

#### 9. Mark Match as Read
```bash
POST /api/v1/matches/{match_id}/read?device_id={device_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Match marked as read"
}
```

#### 10. Get Unread Count
```bash
GET /api/v1/matches/{device_id}/unread-count
```

**Response:**
```json
{
  "success": true,
  "data": {
    "unread_count": 3
  }
}
```

### 🔍 Health & Monitoring

#### 11. System Health Check
```bash
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "apns": "healthy",
    "scraper": "healthy"
  },
  "metrics": {
    "active_devices": 1250,
    "active_subscriptions": 3400,
    "matches_last_24h": 890,
    "notifications_sent_last_24h": 245
  }
}
```

#### 12. Scraper Status
```bash
GET /api/v1/health/status/scraper
```

**Response:**
```json
{
  "status": "running",
  "last_run": "2024-01-16T10:15:00Z",
  "next_run": "2024-01-16T10:30:00Z",
  "sources": [
    {
      "name": "linkedin",
      "status": "healthy",
      "last_successful_scrape": "2024-01-16T10:15:00Z",
      "jobs_scraped_last_run": 45,
      "error_count_24h": 0
    },
    {
      "name": "indeed",
      "status": "healthy",
      "last_successful_scrape": "2024-01-16T10:12:00Z",
      "jobs_scraped_last_run": 32,
      "error_count_24h": 1
    }
  ],
  "total_jobs_last_24h": 2340,
  "errors_last_24h": 2
}
```

#### 13. Prometheus Metrics
```bash
GET /metrics
```

**Response:**
```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/api/v1/health",status="200"} 1250.0

# HELP active_devices_total Number of active devices
# TYPE active_devices_total gauge
active_devices_total 1250.0

# HELP job_matches_created_total Total job matches created
# TYPE job_matches_created_total counter
job_matches_created_total 890.0
```

## 🔐 Authentication

### Device Authentication (JWT)
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Admin API Key
```bash
X-API-Key: your-api-key-here
```

## 📱 Push Notification Payload

When a job match is found, the following push notification is sent:

```json
{
  "aps": {
    "alert": {
      "title": "New Job Match! 🎯",
      "subtitle": "Senior Python Developer at TechCorp",
      "body": "Matches your keywords: Python, Senior Developer"
    },
    "badge": 1,
    "sound": "default",
    "category": "JOB_MATCH",
    "thread-id": "job-matches"
  },
  "custom_data": {
    "type": "job_match",
    "match_id": "770e8400-e29b-41d4-a716-446655440002",
    "job_id": 12345,
    "matched_keywords": ["Python", "Senior Developer"],
    "deep_link": "birjob://job/12345"
  }
}
```

## 🚀 Quick Start Commands

To run the actual backend:

```bash
# Using Docker (recommended)
docker-compose up -d

# Direct Python (after setting up database)
uvicorn app:app --host 0.0.0.0 --port 8000

# Run match engine separately
python -c "import asyncio; from app.services.match_engine import job_scheduler; asyncio.run(job_scheduler.start())"
```

## 📊 API Features

✅ **Complete REST API** - All endpoints from README spec  
✅ **PostgreSQL Integration** - Uses iosapp schema  
✅ **Redis Caching** - Device keywords, processed jobs  
✅ **Job Matching Engine** - Automatic background processing  
✅ **Push Notifications** - APNs with smart throttling  
✅ **Security** - JWT auth, rate limiting, input validation  
✅ **Monitoring** - Prometheus metrics, health checks  
✅ **Production Ready** - Docker, load balancing, scaling  

## 🔗 Integration

The backend seamlessly integrates with your existing scraper:
- Reads from `scraper.jobs_jobpost` table
- No changes needed to existing scraper code
- Creates matches in `iosapp.job_matches` table
- Sends push notifications for new matches every 5 minutes