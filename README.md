# iOS Native App Backend Specification

## 1. Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           iOS Native App Backend                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   iOS Device    │    │   iOS Device    │    │   iOS Device    │            │
│  │  (Device Token) │    │  (Device Token) │    │  (Device Token) │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│           │                       │                       │                   │
│           └───────────────────────┼───────────────────────┘                   │
│                                   │                                           │
│                           ┌───────▼────────┐                                  │
│                           │  Load Balancer │                                  │
│                           │   (Nginx/HAP)  │                                  │
│                           └───────┬────────┘                                  │
│                                   │                                           │
│               ┌───────────────────┼───────────────────┐                       │
│               │                   │                   │                       │
│       ┌───────▼────────┐ ┌────────▼────────┐ ┌───────▼────────┐              │
│       │  iOS API       │ │  iOS API        │ │  iOS API       │              │
│       │  Server 1      │ │  Server 2       │ │  Server 3      │              │
│       │ (Node.js/Fast) │ │ (Node.js/Fast)  │ │ (Node.js/Fast) │              │
│       └───────┬────────┘ └────────┬────────┘ └───────┬────────┘              │
│               │                   │                   │                       │
│               └───────────────────┼───────────────────┘                       │
│                                   │                                           │
│  ┌────────────────────────────────┼────────────────────────────────────────┐  │
│  │              Data Layer        │                                        │  │
│  │                                │                                        │  │
│  │  ┌─────────────────────────────▼─────────────────────────────┐          │  │
│  │  │               PostgreSQL Database                        │          │  │
│  │  │                                                          │          │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │          │  │
│  │  │  │   scraper   │  │   website   │  │   iosapp    │     │          │  │
│  │  │  │   schema    │  │   schema    │  │   schema    │     │          │  │
│  │  │  │ (existing)  │  │ (existing)  │  │    (new)    │     │          │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘     │          │  │
│  │  └──────────────────────────────────────────────────────────          │  │
│  │                                                                        │  │
│  │  ┌─────────────────────┐    ┌─────────────────────┐                   │  │
│  │  │     Redis Cache     │    │   Background Jobs   │                   │  │
│  │  │   (Keywords &       │    │   (Celery/Bull)     │                   │  │
│  │  │  Device Tokens)     │    │                     │                   │  │
│  │  └─────────────────────┘    └─────────────────────┘                   │  │
│  └────────────────────────────────────────────────────────────────────────  │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                     Background Services                                │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │  │
│  │  │  Data Scraper   │    │ Match Engine    │    │ Push Notification│    │  │
│  │  │   (Existing)    │    │   (Keywords)    │    │   Service (APNs) │    │  │
│  │  │                 │    │                 │    │                 │    │  │
│  │  │  Cron: Every    │    │  Cron: Every    │    │  Event: On      │    │  │
│  │  │  15 minutes     │    │  5 minutes      │    │  Match Found    │    │  │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────  │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                       External Services                                │  │
│  │                                                                        │  │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    │  │
│  │  │  Apple Push     │    │   Monitoring    │    │    Logging      │    │  │
│  │  │  Notification   │    │   (DataDog)     │    │  (ELK Stack)    │    │  │
│  │  │  Service (APNs) │    │                 │    │                 │    │  │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **API Framework**: Node.js with Express/Fastify or Python with FastAPI
- **Database**: PostgreSQL (Multi-schema: `scraper`, `website`, `iosapp`)
- **Cache**: Redis for device tokens and keyword matching
- **Queue**: Celery (Python) or Bull (Node.js) for background jobs
- **Push Notifications**: Apple Push Notification Service (APNs)
- **Monitoring**: Health checks, structured logging, metrics collection

## 2. Core Endpoints

### Device Management

#### **POST /api/v1/devices/register**
Registers a new iOS device for push notifications.

**Request:**
```json
{
  "device_token": "a1b2c3d4e5f6...",
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
    "device_id": "uuid-1234-5678-90ab",
    "registered_at": "2024-01-15T10:30:00Z"
  }
}
```

#### **DELETE /api/v1/devices/{device_id}**
Unregisters a device from push notifications.

**Response:**
```json
{
  "success": true,
  "message": "Device unregistered successfully"
}
```

### Keyword Management

#### **POST /api/v1/keywords**
Subscribes a device to keyword-based job notifications.

**Request:**
```json
{
  "device_id": "uuid-1234-5678-90ab",
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
    "subscription_id": "sub-uuid-1234",
    "keywords_count": 3,
    "sources_count": 3,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### **GET /api/v1/keywords/{device_id}**
Retrieves current keyword subscriptions for a device.

**Response:**
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "subscription_id": "sub-uuid-1234",
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

#### **PUT /api/v1/keywords/{subscription_id}**
Updates keyword subscription settings.

#### **DELETE /api/v1/keywords/{subscription_id}**
Removes a keyword subscription.

### Job Matching

#### **GET /api/v1/matches/{device_id}**
Retrieves recent job matches for a device.

**Query Parameters:**
- `limit`: Number of matches to return (default: 20, max: 100)
- `offset`: Pagination offset
- `since`: ISO timestamp for filtering recent matches

**Response:**
```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "match-uuid-1234",
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

#### **POST /api/v1/matches/{match_id}/read**
Marks a job match as read/viewed.

### Health & Status

#### **GET /api/v1/health**
System health check endpoint.

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

#### **GET /api/v1/status/scraper**
Detailed scraper status and statistics.

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
    }
  ],
  "total_jobs_last_24h": 2340,
  "errors_last_24h": 2
}
```

## 3. Database Schema (`iosapp`)

### Tables Overview

```sql
-- iOS App Schema Tables
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
```

### Indexes for Performance

```sql
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
```

## 4. Scraper Integration

### Data Flow Integration

The iOS backend leverages the existing scraper infrastructure with minimal modifications:

1. **Existing Scraper**: Continues to populate `scraper.jobs_jobpost` table
2. **Match Engine**: New service monitors `scraper.jobs_jobpost` for new entries
3. **Keyword Matching**: Matches new jobs against active iOS subscriptions
4. **Notification Delivery**: Sends push notifications via APNs

### Match Engine Implementation

```python
# match_engine.py
import asyncio
import logging
from typing import List, Dict
from datetime import datetime, timedelta

class JobMatchEngine:
    def __init__(self, db_connection, redis_client, apns_client):
        self.db = db_connection
        self.redis = redis_client
        self.apns = apns_client
        self.logger = logging.getLogger(__name__)
    
    async def process_new_jobs(self):
        """Main matching engine - runs every 5 minutes"""
        try:
            # Get jobs from last 10 minutes (with overlap buffer)
            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
            
            new_jobs = await self.get_new_jobs_since(cutoff_time)
            if not new_jobs:
                self.logger.info("No new jobs to process")
                return
            
            self.logger.info(f"Processing {len(new_jobs)} new jobs")
            
            # Get all active subscriptions with caching
            active_subscriptions = await self.get_active_subscriptions()
            
            for job in new_jobs:
                await self.match_job_to_subscriptions(job, active_subscriptions)
                
        except Exception as e:
            self.logger.error(f"Error in match engine: {e}", exc_info=True)
    
    async def match_job_to_subscriptions(self, job: Dict, subscriptions: List[Dict]):
        """Match a single job against all active subscriptions"""
        job_text = f"{job['title']} {job['company']}".lower()
        
        for subscription in subscriptions:
            # Check if this job was already processed for this device
            processed_key = f"processed:{subscription['device_id']}:{job['id']}"
            if await self.redis.exists(processed_key):
                continue
            
            # Apply source filter
            if (subscription['sources'] and 
                job['source'] not in subscription['sources']):
                continue
            
            # Check keyword matches
            matched_keywords = []
            for keyword in subscription['keywords']:
                if keyword.lower() in job_text:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                # Calculate relevance score
                relevance_score = self.calculate_relevance(
                    job, matched_keywords, subscription['keywords']
                )
                
                # Store match in database
                match_id = await self.store_job_match(
                    subscription['device_id'],
                    subscription['id'],
                    job['id'],
                    matched_keywords,
                    relevance_score
                )
                
                # Send push notification
                await self.send_push_notification(
                    subscription['device_token'],
                    job,
                    matched_keywords,
                    match_id
                )
                
                # Mark as processed
                await self.redis.setex(processed_key, 86400, "1")  # 24hr TTL
    
    def calculate_relevance(self, job: Dict, matched_keywords: List[str], 
                          all_keywords: List[str]) -> float:
        """Calculate relevance score (0.0 to 1.0)"""
        # Simple scoring: percentage of keywords matched + title match bonus
        base_score = len(matched_keywords) / len(all_keywords)
        
        # Bonus for title matches
        title_matches = sum(1 for kw in matched_keywords 
                          if kw.lower() in job['title'].lower())
        title_bonus = (title_matches / len(matched_keywords)) * 0.2
        
        return min(1.0, base_score + title_bonus)
```

### Scheduled Jobs Configuration

```yaml
# docker-compose.yml background services
version: '3.8'
services:
  match-engine:
    build: .
    command: python -m celery worker -A match_engine.celery_app
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - APNS_KEY_PATH=${APNS_KEY_PATH}
    depends_on:
      - postgres
      - redis
  
  scheduler:
    build: .
    command: python -m celery beat -A match_engine.celery_app
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
```

```python
# celery_config.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery('ios_backend')

celery_app.conf.beat_schedule = {
    'process-new-jobs': {
        'task': 'match_engine.process_new_jobs',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'cleanup-old-matches': {
        'task': 'cleanup.remove_old_matches',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    'update-device-health': {
        'task': 'devices.check_device_health',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

## 5. Matching & Notification Workflow

### Sequence Diagram

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scraper   │    │Match Engine │    │  Database   │    │    APNs     │    │ iOS Device  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │                   │
       │ 1. Insert new     │                   │                   │                   │
       │    jobs           │                   │                   │                   │
       ├──────────────────►│                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 2. Query new jobs │                   │                   │
       │                   │   (last 10 min)   │                   │                   │
       │                   ├──────────────────►│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 3. Return jobs    │                   │                   │
       │                   │◄──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 4. Get active     │                   │                   │
       │                   │    subscriptions  │                   │                   │
       │                   ├──────────────────►│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 5. Return         │                   │                   │
       │                   │    subscriptions  │                   │                   │
       │                   │◄──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │                   │ 6. For each job:  │                   │                   │
       │                   │    Match keywords │                   │                   │
       │                   │    Calculate score│                   │                   │
       │                   │    Check filters  │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 7. Store matches  │                   │                   │
       │                   ├──────────────────►│                   │                   │
       │                   │                   │                   │                   │
       │                   │ 8. For each match:│                   │                   │
       │                   │    Send push      │                   │                   │
       │                   │    notification   │                   │                   │
       │                   ├───────────────────┼──────────────────►│                   │
       │                   │                   │                   │                   │
       │                   │                   │                   │ 9. Deliver to    │
       │                   │                   │                   │    device         │
       │                   │                   │                   ├──────────────────►│
       │                   │                   │                   │                   │
       │                   │                   │                   │ 10. Delivery     │
       │                   │                   │                   │     confirmation │
       │                   │                   │                   │◄──────────────────┤
       │                   │                   │                   │                   │
       │                   │ 11. Update        │                   │                   │
       │                   │     notification  │                   │                   │
       │                   │     status        │                   │                   │
       │                   ├──────────────────►│                   │                   │
       │                   │                   │                   │                   │
```

### Push Notification Payload Structure

```json
{
  "aps": {
    "alert": {
      "title": "New Job Match!",
      "subtitle": "Senior Python Developer at TechCorp",
      "body": "A new job matching your keywords: Python, Senior Developer"
    },
    "badge": 1,
    "sound": "default",
    "category": "JOB_MATCH",
    "thread-id": "job-matches"
  },
  "custom_data": {
    "type": "job_match",
    "match_id": "match-uuid-1234",
    "job_id": 12345,
    "matched_keywords": ["Python", "Senior Developer"],
    "relevance_score": 0.85,
    "deep_link": "birjob://job/12345"
  }
}
```

### Notification Types

1. **Immediate Job Match**: Sent when a new job matches keywords (within 5 minutes)
2. **Daily Digest**: Sent once per day with summary of matches (optional)
3. **System Notifications**: App updates, maintenance notices

## 6. Security Considerations

### API Authentication

```python
# auth_middleware.py
import jwt
from datetime import datetime, timedelta
from functools import wraps

class APIKeyAuth:
    """Simple API key authentication for admin endpoints"""
    
    def __init__(self, valid_api_keys: set):
        self.valid_api_keys = valid_api_keys
    
    def require_api_key(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            api_key = request.headers.get('X-API-Key')
            if not api_key or api_key not in self.valid_api_keys:
                return jsonify({'error': 'Invalid API key'}), 401
            return f(*args, **kwargs)
        return decorated_function

class DeviceAuth:
    """Device-based authentication using signed tokens"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_device_token(self, device_id: str) -> str:
        payload = {
            'device_id': device_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=365)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_device_token(self, token: str) -> str:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['device_id']
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid device token")
```

### Security Headers

```python
# security_middleware.py
from flask import Flask

def configure_security_headers(app: Flask):
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HSTS for HTTPS
        response.headers['Strict-Transport-Security'] = \
            'max-age=31536000; includeSubDomains'
        
        # CSP for API responses
        response.headers['Content-Security-Policy'] = "default-src 'none'"
        
        return response
```

### Rate Limiting

```python
# rate_limiting.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis:6379",
    default_limits=["1000 per hour"]
)

# Apply to specific endpoints
@app.route('/api/v1/keywords', methods=['POST'])
@limiter.limit("10 per minute")
def create_keywords():
    pass

@app.route('/api/v1/devices/register', methods=['POST'])
@limiter.limit("5 per minute")
def register_device():
    pass
```

### Data Privacy & GDPR Compliance

```python
# privacy_manager.py
class PrivacyManager:
    """Handle data privacy and GDPR compliance"""
    
    async def export_user_data(self, device_id: str) -> Dict:
        """Export all data for a device (GDPR Article 20)"""
        data = {
            'device_info': await self.get_device_info(device_id),
            'subscriptions': await self.get_subscriptions(device_id),
            'matches': await self.get_matches(device_id),
            'notifications': await self.get_notifications(device_id)
        }
        return data
    
    async def delete_user_data(self, device_id: str) -> bool:
        """Delete all data for a device (GDPR Article 17)"""
        async with self.db.transaction():
            await self.db.execute(
                "DELETE FROM iosapp.push_notifications WHERE device_id = $1",
                device_id
            )
            await self.db.execute(
                "DELETE FROM iosapp.job_matches WHERE device_id = $1",
                device_id
            )
            await self.db.execute(
                "DELETE FROM iosapp.keyword_subscriptions WHERE device_id = $1",
                device_id
            )
            await self.db.execute(
                "DELETE FROM iosapp.device_tokens WHERE id = $1",
                device_id
            )
        return True
```

## 7. Optional Extensions

### Analytics Dashboard

```python
# analytics.py
class AnalyticsDashboard:
    """Analytics for iOS app performance"""
    
    async def get_dashboard_metrics(self) -> Dict:
        return {
            'device_metrics': {
                'total_active_devices': await self.count_active_devices(),
                'new_devices_24h': await self.count_new_devices_24h(),
                'device_retention_7d': await self.calculate_retention_7d()
            },
            'subscription_metrics': {
                'total_subscriptions': await self.count_subscriptions(),
                'avg_keywords_per_device': await self.avg_keywords_per_device(),
                'top_keywords': await self.get_top_keywords()
            },
            'notification_metrics': {
                'notifications_sent_24h': await self.count_notifications_24h(),
                'delivery_success_rate': await self.calculate_delivery_rate(),
                'avg_response_time': await self.calculate_avg_response_time()
            },
            'matching_metrics': {
                'matches_found_24h': await self.count_matches_24h(),
                'avg_relevance_score': await self.avg_relevance_score(),
                'top_job_sources': await self.get_top_sources()
            }
        }
```

### A/B Testing Framework

```python
# ab_testing.py
class ABTestManager:
    """A/B testing for notification strategies"""
    
    def __init__(self):
        self.experiments = {
            'notification_timing': {
                'variants': ['immediate', 'batched_5min', 'batched_15min'],
                'allocation': [0.4, 0.3, 0.3]
            },
            'relevance_threshold': {
                'variants': [0.6, 0.7, 0.8],
                'allocation': [0.33, 0.34, 0.33]
            }
        }
    
    def get_variant(self, experiment: str, device_id: str) -> str:
        """Consistent variant assignment based on device_id"""
        import hashlib
        hash_input = f"{experiment}:{device_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        experiment_config = self.experiments[experiment]
        variants = experiment_config['variants']
        allocation = experiment_config['allocation']
        
        # Deterministic assignment
        cumulative = 0
        normalized_hash = (hash_value % 1000) / 1000
        
        for i, alloc in enumerate(allocation):
            cumulative += alloc
            if normalized_hash < cumulative:
                return variants[i]
        
        return variants[-1]
```

### Smart Throttling

```python
# throttling.py
class SmartThrottling:
    """Intelligent notification throttling to prevent spam"""
    
    def __init__(self):
        self.max_notifications_per_hour = 5
        self.max_notifications_per_day = 20
        self.quiet_hours = (22, 8)  # 10 PM to 8 AM local time
    
    async def should_send_notification(self, device_id: str, 
                                     local_time: datetime) -> bool:
        # Check quiet hours
        if self.is_quiet_hours(local_time):
            return False
        
        # Check hourly limit
        hour_count = await self.get_notification_count_last_hour(device_id)
        if hour_count >= self.max_notifications_per_hour:
            return False
        
        # Check daily limit
        day_count = await self.get_notification_count_today(device_id)
        if day_count >= self.max_notifications_per_day:
            return False
        
        return True
    
    def is_quiet_hours(self, local_time: datetime) -> bool:
        hour = local_time.hour
        return hour >= self.quiet_hours[0] or hour < self.quiet_hours[1]
```

## 8. Deployment & Scaling

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

```yaml
# docker-compose.production.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - APNS_KEY_PATH=/secrets/apns.p8
    volumes:
      - ./secrets:/secrets:ro
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=birjob_ios
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Configuration

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ios-backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ios-backend-api
  template:
    metadata:
      labels:
        app: ios-backend-api
    spec:
      containers:
      - name: api
        image: birjob/ios-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Monitoring & Observability

```python
# monitoring.py
import structlog
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
ACTIVE_DEVICES = Gauge('active_devices_total', 'Number of active devices')
NOTIFICATION_QUEUE_SIZE = Gauge('notification_queue_size', 'Pending notifications')

logger = structlog.get_logger()

class MonitoringMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        start_time = time.time()
        
        def new_start_response(status, response_headers, exc_info=None):
            # Log request
            duration = time.time() - start_time
            method = environ.get('REQUEST_METHOD')
            path = environ.get('PATH_INFO')
            status_code = status.split()[0]
            
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
            REQUEST_DURATION.observe(duration)
            
            logger.info("api_request",
                       method=method,
                       path=path,
                       status=status_code,
                       duration=duration,
                       user_agent=environ.get('HTTP_USER_AGENT'))
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, new_start_response)
```

This specification provides a complete foundation for building a production-ready iOS backend that integrates seamlessly with your existing scraper infrastructure while maintaining its own dedicated schema and push notification system. The architecture is designed for horizontal scaling and includes comprehensive monitoring, security, and privacy considerations.