# iOS Job App Backend - Complete API Documentation

**Base URL**: `https://birjobbackend-ir3e.onrender.com`
**API Version**: v1
**Architecture**: FastAPI + PostgreSQL + Redis + Gemini AI

---

## 🏗️ Architecture Overview

### Core Components
- **FastAPI Backend**: High-performance async API server
- **PostgreSQL Database**: RDBMS with proper foreign key relationships
- **Redis Cache**: Session management and caching
- **Gemini 2.5 Flash AI**: Chatbot and job recommendations
- **Push Notifications**: APNs integration for iOS

### Database Schemas
- **iosapp**: User management, analytics, saved jobs
- **scraper**: Job listings from 39+ sources (4,367+ jobs)

---

## 📱 iOS Integration Quick Start

### 1. Base Configuration
```swift
struct APIConfig {
    static let baseURL = "https://birjobbackend-ir3e.onrender.com"
    static let apiVersion = "v1"
    static let timeout: TimeInterval = 30.0
}
```

### 2. Device Registration (Required First)
```swift
// Register device on app launch
POST /api/v1/users/register
{
    "device_id": "unique-ios-device-id",
    "email": "user@example.com", 
    "keywords": ["ios", "swift", "developer"],
    "notifications_enabled": true
}
```

### 3. Authentication Flow
- **No JWT tokens required** - Uses device_id for identification
- **Device-based auth** - Each API call includes device_id
- **Automatic user linking** - Email conflicts handled gracefully

---

## 🔗 API Endpoints Reference

### Health & System Status

#### GET `/`
**Purpose**: Basic service info
**Response**:
```json
{
    "message": "iOS Job App Backend",
    "version": "1.0.0", 
    "status": "running"
}
```

#### GET `/health`
**Purpose**: Simple health check
**Response**:
```json
{
    "status": "healthy",
    "message": "Service is running"
}
```

#### GET `/api/v1/health/status`
**Purpose**: Detailed system health
**Response**:
```json
{
    "status": "healthy",
    "timestamp": "2025-07-03T05:00:42.388403+00:00",
    "services": {
        "database": "healthy",
        "redis": "healthy", 
        "apns": "healthy",
        "scraper": "healthy"
    },
    "metrics": {
        "active_devices": 7,
        "active_subscriptions": 6,
        "matches_last_24h": 2,
        "notifications_sent_last_24h": 4
    }
}
```

---

### 👤 User Management

#### POST `/api/v1/users/register`
**Purpose**: Register new user with device
**Request Body**:
```json
{
    "device_id": "string",
    "email": "string", 
    "keywords": ["array", "of", "strings"],
    "preferred_sources": ["array", "of", "sources"],
    "notifications_enabled": boolean
}
```
**Response**:
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "user_id": "uuid",
        "device_id": "string"
    }
}
```

#### GET `/api/v1/users/profile/{device_id}`
**Purpose**: Get user profile by device
**Response**:
```json
{
    "success": true,
    "message": "User profile found",
    "data": {
        "id": "uuid",
        "device_id": "string",
        "email": "string",
        "keywords": ["array"],
        "preferred_sources": ["array"],
        "notifications_enabled": boolean,
        "created_at": "ISO-8601",
        "updated_at": "ISO-8601"
    }
}
```

#### PUT `/api/v1/users/profile`
**Purpose**: Create or update user profile
**Request Body**:
```json
{
    "device_id": "string",
    "email": "string",
    "keywords": ["updated", "keywords"], 
    "notifications_enabled": boolean
}
```

#### GET `/api/v1/users/by-email?email={email}`
**Purpose**: Get/create user by email (web integration)

#### POST `/api/v1/users/keywords/email`
**Purpose**: Add keyword to user by email
**Request Body**:
```json
{
    "email": "string",
    "keyword": "string"
}
```

---

### 💼 Job Management

#### GET `/api/v1/jobs/`
**Purpose**: List jobs with filtering and search
**Query Parameters**:
- `limit`: Number of jobs (1-100, default: 20)
- `offset`: Skip jobs for pagination (default: 0)
- `search`: Search in title/company
- `company`: Filter by company
- `source`: Filter by job source
- `location`: Search by location
- `days`: Jobs from last N days
- `sort_by`: Sort field (created_at, title, company)
- `sort_order`: asc/desc (default: desc)

**Response**:
```json
{
    "success": true,
    "data": {
        "jobs": [
            {
                "id": 2066000,
                "title": "Full-stack Python Developer",
                "company": "Envion Software", 
                "apply_link": "https://...",
                "source": "Djinni",
                "posted_at": "2025-07-03T04:37:01.516357"
            }
        ],
        "pagination": {
            "total": 4367,
            "limit": 20,
            "offset": 0,
            "current_page": 1,
            "total_pages": 219,
            "has_more": true,
            "has_previous": false
        },
        "filters": {
            "search": null,
            "company": null,
            "source": null
        }
    }
}
```

#### GET `/api/v1/jobs/{job_id}`
**Purpose**: Get specific job details
**Response**:
```json
{
    "success": true,
    "data": {
        "job": {
            "id": 2066000,
            "title": "Full-stack Python Developer",
            "company": "Envion Software",
            "apply_link": "https://...",
            "source": "Djinni",
            "posted_at": "2025-07-03T04:37:01.516357"
        }
    }
}
```

#### GET `/api/v1/jobs/stats/summary`
**Purpose**: Job statistics and insights
**Response**:
```json
{
    "success": true,
    "data": {
        "total_jobs": 4367,
        "recent_jobs_24h": 150,
        "top_companies": [
            {"company": "ABB", "job_count": 115},
            {"company": "Kontakt Home", "job_count": 109}
        ],
        "job_sources": [
            {"source": "Glorri", "job_count": 794},
            {"source": "Vakansiya.biz", "job_count": 490}
        ]
    }
}
```

#### POST `/api/v1/jobs/save`
**Purpose**: Save job for user
**Request Body**:
```json
{
    "device_id": "string",
    "job_id": 123456
}
```

#### GET `/api/v1/jobs/saved/{device_id}`
**Purpose**: Get user's saved jobs
**Response**:
```json
{
    "success": true,
    "data": {
        "saved_jobs": [
            {
                "job_id": 2066000,
                "job_title": "Full-stack Python Developer",
                "job_company": "Envion Software",
                "job_source": "Djinni",
                "saved_at": "2025-07-03T04:59:55.989264+00:00"
            }
        ]
    }
}
```

#### DELETE `/api/v1/jobs/unsave`
**Purpose**: Remove saved job
**Request Body**:
```json
{
    "device_id": "string", 
    "job_id": 123456
}
```

#### POST `/api/v1/jobs/view`
**Purpose**: Record job view for analytics
**Request Body**:
```json
{
    "device_id": "string",
    "job_id": 123456,
    "view_duration_seconds": 30
}
```

---

### 📱 Device Management

#### POST `/api/v1/devices/register`
**Purpose**: Register device for push notifications
**Request Body**:
```json
{
    "device_id": "string",
    "device_token": "64+_character_apns_token",
    "device_info": {
        "model": "iPhone 14",
        "osVersion": "iOS 17.0", 
        "deviceModel": "iPhone 14 Pro",
        "timezone": "UTC",
        "app_version": "1.0.0"
    }
}
```

#### GET `/api/v1/devices/{device_id}/status`
**Purpose**: Get device registration status
**Response**:
```json
{
    "success": true,
    "data": {
        "device_id": "string",
        "uuid": "device-uuid",
        "is_active": true,
        "registered_at": "ISO-8601",
        "last_updated": "ISO-8601",
        "device_info": {}
    }
}
```

#### DELETE `/api/v1/devices/{device_id}`
**Purpose**: Unregister device

---

### 📊 Analytics

#### POST `/api/v1/analytics/event`
**Purpose**: Record user analytics event
**Request Body**:
```json
{
    "device_id": "string",
    "action_type": "job_view|job_save|search|app_open|app_close",
    "action_data": {"key": "value"},
    "session_id": "optional-session-id",
    "device_info": {}
}
```

#### GET `/api/v1/analytics/user/{device_id}`
**Purpose**: Get user analytics summary
**Response**:
```json
{
    "user_id": "uuid",
    "total_events": 10,
    "events_by_type": {
        "job_view": 7,
        "job_save": 2,
        "search": 1
    },
    "first_event": "ISO-8601",
    "last_event": "ISO-8601",
    "data": {
        "analysis_period_days": 30,
        "device_id": "string"
    }
}
```

#### GET `/api/v1/analytics/stats`
**Purpose**: Get global analytics statistics
**Response**:
```json
{
    "success": true,
    "data": {
        "last_24_hours": {
            "active_users": 5,
            "total_events": 25,
            "events_by_type": {
                "job_view": 15,
                "search": 8,
                "job_save": 2
            }
        }
    }
}
```

---

### 🤖 AI Chatbot (Gemini 2.5 Flash)

#### POST `/api/v1/chatbot/chat`
**Purpose**: Chat with AI job search assistant
**Request Body**:
```json
{
    "device_id": "string",
    "message": "How can I improve my resume for backend roles?",
    "conversation_history": [
        {
            "role": "user|assistant",
            "content": "message content",
            "timestamp": "optional-ISO-8601"
        }
    ],
    "include_user_context": true
}
```
**Response**:
```json
{
    "success": true,
    "response": "AI response about resume improvement...",
    "timestamp": "ISO-8601",
    "model": "gemini-2.5-flash",
    "error": null
}
```

#### POST `/api/v1/chatbot/recommendations`
**Purpose**: Get personalized job recommendations
**Request Body**:
```json
{
    "device_id": "string",
    "keywords": ["python", "fastapi", "backend"],
    "location": "Baku"
}
```
**Response**:
```json
{
    "success": true,
    "recommendations": "AI-generated job search recommendations...",
    "keywords": ["python", "fastapi", "backend"],
    "location": "Baku",
    "timestamp": "ISO-8601"
}
```

#### POST `/api/v1/chatbot/analyze-job`
**Purpose**: AI analysis of job posting
**Request Body**:
```json
{
    "device_id": "string",
    "job_id": 123456,
    "job_title": "Senior Backend Developer",
    "job_company": "Tech Company",
    "job_description": "We are looking for..."
}
```
**Response**:
```json
{
    "success": true,
    "analysis": "AI analysis with insights, interview questions, resume tips...",
    "job_title": "Senior Backend Developer",
    "company": "Tech Company", 
    "timestamp": "ISO-8601"
}
```

#### GET `/api/v1/chatbot/stats`
**Purpose**: Chatbot usage statistics
**Response**:
```json
{
    "success": true,
    "data": {
        "last_24_hours": {
            "total_interactions": 15,
            "unique_users": 8,
            "interactions_by_type": {
                "chatbot_message": 10,
                "job_recommendations": 3,
                "job_analysis": 2
            }
        },
        "chatbot_status": "operational",
        "timestamp": "ISO-8601"
    }
}
```

---

## 🔧 Error Handling

### Standard Error Response Format
```json
{
    "detail": "Error message",
    "error_code": "optional_error_code",
    "timestamp": "ISO-8601"
}
```

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (user/job/device not found)
- **422**: Unprocessable Entity (validation error)
- **500**: Internal Server Error
- **503**: Service Unavailable (temporary issues)

### Device Not Found Handling
If device_id is not registered:
```json
{
    "detail": "User not found for device"
}
```
**Solution**: Call `/api/v1/users/register` first

---

## 📱 iOS Integration Examples

### 1. App Launch Flow
```swift
// 1. Register device
let deviceData = [
    "device_id": UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString,
    "email": userEmail,
    "keywords": userKeywords,
    "notifications_enabled": true
] 

// 2. Register for push notifications
let deviceToken = // APNs device token
registerDevice(deviceToken: deviceToken)
```

### 2. Job Search Implementation
```swift
// Search jobs
func searchJobs(query: String, page: Int = 1) {
    let params = [
        "search": query,
        "limit": "20",
        "offset": String((page - 1) * 20)
    ]
    // Call GET /api/v1/jobs/
}

// Save job
func saveJob(jobId: Int) {
    let data = [
        "device_id": deviceId,
        "job_id": jobId
    ]
    // Call POST /api/v1/jobs/save
}
```

### 3. AI Chatbot Integration
```swift
func askChatbot(message: String) {
    let data = [
        "device_id": deviceId,
        "message": message,
        "include_user_context": true
    ]
    // Call POST /api/v1/chatbot/chat
}
```

### 4. Analytics Tracking
```swift
func trackJobView(jobId: Int, duration: Int) {
    let data = [
        "device_id": deviceId,
        "action_type": "job_view",
        "action_data": ["job_id": jobId, "duration": duration]
    ]
    // Call POST /api/v1/analytics/event
}
```

---

## 🔒 Security & Privacy

### Data Protection
- **No passwords required** - Device-based authentication
- **GDPR compliant** - Analytics deletion available
- **Secure connections** - HTTPS only
- **Data encryption** - In transit and at rest

### Rate Limiting
- **API calls**: Reasonable rate limits applied
- **Chatbot**: Usage tracked and limited per device
- **Search**: Optimized for mobile usage patterns

---

## 🚀 Performance & Reliability

### System Status
- **Uptime**: 99.9% availability target
- **Response Time**: <500ms average
- **Database**: 4,367+ jobs, real-time updates
- **Caching**: Redis for optimized performance

### Monitoring Endpoints
- `GET /health` - Basic health check
- `GET /api/v1/health/status` - Detailed monitoring
- `GET /api/v1/analytics/stats` - Usage statistics

---

## 📞 Support & Troubleshooting

### Common Issues
1. **"User not found for device"** → Register device first
2. **"Invalid device ID format"** → Use string device IDs
3. **Email conflicts** → Handled automatically with UPSERT
4. **Chatbot errors** → Check Gemini API status

### Debug Endpoints
- `GET /api/v1/health/db-debug` - Database connection debug
- `GET /api/v1/health/check-user-tables` - Table existence check

### Contact
- **API Issues**: Check health endpoints first
- **Documentation**: This file covers all endpoints
- **Performance**: All endpoints tested and optimized

---

## 📋 Quick Reference

### Essential Endpoints for iOS App
1. **User Registration**: `POST /api/v1/users/register`
2. **Job Search**: `GET /api/v1/jobs/`
3. **Save Jobs**: `POST /api/v1/jobs/save`
4. **AI Chat**: `POST /api/v1/chatbot/chat`
5. **Analytics**: `POST /api/v1/analytics/event`

### Required Fields
- **device_id**: Always required for user operations
- **email**: Required for user registration
- **job_id**: Required for job operations
- **keywords**: Optional but recommended for personalization

### Data Sources
- **39+ Job Sources**: Glorri, Vakansiya.biz, Djinni, Boss.az, etc.
- **Real-time Updates**: Jobs scraped continuously
- **AI Powered**: Gemini 2.5 Flash for recommendations

---

**Last Updated**: July 3, 2025
**API Version**: v1.0
**Backend Status**: Production Ready ✅