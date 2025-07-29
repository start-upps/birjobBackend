# 📱 BirJob Backend - Complete API Documentation

## 🎯 Overview

**Production-ready backend for iOS/Android job notification apps**. Complete API documentation for mobile app development with device-based authentication, push notifications, job matching, and analytics.

**🌐 Production API**: `https://birjobbackend-ir3e.onrender.com`  
**📚 Interactive Docs**: `https://birjobbackend-ir3e.onrender.com/docs`  
**🚀 Status**: **LIVE** with complete mobile app support

---

## 🏗️ System Architecture

### Core Features
- **Device-First Authentication**: No email required - device tokens + keywords
- **Push Notifications**: APNs integration with notification_id for iOS compatibility
- **Job Matching**: Real-time job matching with session-based pagination
- **Privacy Compliant**: GDPR/CCPA with user consent controls
- **Hash Deduplication**: SHA-256-based job uniqueness (prevents spam)
- **Analytics**: Privacy-aware user behavior tracking

### Database Schema
```
iosapp.device_users         # Device registration & authentication
iosapp.users                # User profiles & preferences  
iosapp.notification_hashes  # Notification deduplication
iosapp.job_match_sessions   # Session-based job matching
iosapp.job_match_session_jobs # Jobs in sessions
iosapp.user_analytics       # Privacy-aware analytics
iosapp.consent_logs         # GDPR compliance
scraper.jobs_jobpost        # Job data from scrapers
```

---

## 📱 Quick Start for Mobile Apps

### 1. Device Registration
```http
POST /api/v1/device/register
```

### 2. Get Jobs
```http
GET /api/v1/jobs/?limit=20&offset=0
```

### 3. Handle Push Notifications
- iOS: Extract `notification_id` and `session_id` from payload
- Navigate to `/api/v1/job-matches/session/{session_id}`

---

## 🔐 Authentication

All endpoints use **device token validation**. Device tokens must be:
- 64 hexadecimal characters (Apple APNs format)
- Valid hex string
- Not consist of repeating patterns (security)

**Example**: `bff72bd38158b6a430b4c5feff7befd41aadf4634a715c4d7078be51ef77feff`

---

## 🚀 API Endpoints

## Device Registration

### POST `/api/v1/device/register`
Register a new device for job notifications.

**Request Body:**
```json
{
  "device_token": "bff72bd38158b6a430b4c5feff7befd41aadf4634a715c4d7078be51ef77feff",
  "keywords": ["iOS", "Swift", "Mobile Developer"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": "5dde4e2a-4c63-47e1-9126-ffd0869e10fb",
    "device_token_preview": "bff72bd38158b6a4...",
    "keywords_count": 3,
    "notifications_enabled": true,
    "registered_at": "2025-01-28T22:57:37.123456Z",
    "message": "Device registered successfully - ready for job notifications!"
  }
}
```

### PUT `/api/v1/device/keywords`
Update keywords for existing device.

**Request Body:**
```json
{
  "device_token": "bff72bd38158b6a430b4c5feff7befd41aadf4634a715c4d7078be51ef77feff",
  "keywords": ["Product Manager", "PM", "Strategy"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Keywords updated successfully",
  "keywords_count": 3
}
```

### GET `/api/v1/device/status/{device_token}`
Get device registration status and configuration.

**Response:**
```json
{
  "registered": true,
  "device_id": "5dde4e2a-4c63-47e1-9126-ffd0869e10fb",
  "keywords_count": 3,
  "keywords": ["iOS", "Swift", "Mobile Developer"],
  "notifications_enabled": true,
  "has_keywords": true,
  "setup_complete": true,
  "requires_onboarding": false,
  "registered_at": "2025-01-28T22:57:37.123456Z"
}
```

### DELETE `/api/v1/device/{device_token}`
Delete device and all associated data (GDPR compliance).

**Response:**
```json
{
  "success": true,
  "message": "Device and all associated data deleted successfully",
  "deleted_device_id": "5dde4e2a-4c63-47e1-9126-ffd0869e10fb"
}
```

---

## Jobs API

### GET `/api/v1/jobs/`
Get paginated job listings with filtering and search.

**Query Parameters:**
- `limit` (int, default=20): Number of jobs to return (1-100)
- `offset` (int, default=0): Number of jobs to skip
- `search` (string, optional): Search in title, company
- `company` (string, optional): Filter by company name
- `source` (string, optional): Filter by job source
- `location` (string, optional): Filter by location
- `sort_by` (string, default="created_at"): Sort field
- `sort_order` (string, default="desc"): Sort order (asc/desc)

**Example Request:**
```http
GET /api/v1/jobs/?limit=20&offset=0&search=iOS&company=Apple
```

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "12345",
        "title": "Senior iOS Developer",
        "company": "Apple Inc",
        "apply_link": "https://jobs.apple.com/apply/12345",
        "source": "linkedin", 
        "posted_at": "2025-01-28T22:57:37.123456Z"
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 20,
      "offset": 0,
      "current_page": 1,
      "total_pages": 8,
      "has_more": true,
      "has_previous": false
    }
  }
}
```

---

## Push Notifications

### POST `/api/v1/notifications/test/{device_token}`
Send test notification to device (for debugging).

**Response:**
```json
{
  "success": true,
  "message": "Test notification sent!",
  "device_token_preview": "bff72bd38158b6a4...",
  "test_job": {
    "title": "Test Job Notification",
    "company": "Test Company Inc.",
    "source": "test"
  }
}
```

### Push Notification Payload Structure
When your app receives push notifications, expect this payload:

```json
{
  "aps": {
    "alert": {
      "title": "🎯 Senior iOS Developer",
      "subtitle": "🏢 Apple Inc",
      "body": "💼 iOS, Swift, SwiftUI • +24 more jobs"
    },
    "badge": 1,
    "sound": "default",
    "category": "JOB_MATCH"
  },
  "notification_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "match_20250728_225737_a1197970",
  "type": "job_match",
  "jobId": "abc123hash",
  "custom_data": {
    "notification_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "match_20250728_225737_a1197970",
    "type": "job_match",
    "total_matches": 24,
    "deep_link": "birjob://session/match_20250728_225737_a1197970"
  }
}
```

**iOS App Integration:**
1. Extract `notification_id` from `userInfo["notification_id"]` or `userInfo["custom_data"]["notification_id"]`
2. Extract `session_id` for navigation
3. Navigate to job matches using session endpoint

---

## Job Match Sessions (Push Notification Navigation)

### GET `/api/v1/job-matches/session/{session_id}`
Get jobs from a specific notification session (used when user taps push notification).

**Path Parameters:**
- `session_id`: Session ID from push notification (e.g., "match_20250728_225737_a1197970")

**Query Parameters:**
- `page` (int, default=1): Page number (1-based)
- `limit` (int, default=20): Jobs per page (1-100)

**Example Request:**
```http
GET /api/v1/job-matches/session/match_20250728_225737_a1197970?page=1&limit=20
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session": {
      "session_id": "match_20250728_225737_a1197970",
      "total_matches": 24,
      "matched_keywords": ["iOS", "Swift"],
      "created_at": "2025-01-28T22:57:37.123456Z"
    },
    "jobs": [
      {
        "id": "3546335",
        "title": "IT Recruiter-Researcher",
        "company": "Trust-Sourcing", 
        "apply_link": "https://linkedin.com/jobs/3546335",
        "source": "linkedin",
        "posted_at": "2025-01-28T20:30:00.000000Z"
      }
    ],
    "pagination": {
      "total": 24,
      "limit": 20,
      "offset": 0,
      "current_page": 1,
      "total_pages": 2,
      "has_more": true,
      "has_previous": false
    }
  },
  "message": "Found 20 jobs in session"
}
```

---

## Notification Management

### GET `/api/v1/notifications/inbox/{device_token}`
Get notification history/inbox for device.

**Query Parameters:**
- `limit` (int, default=50): Number of notifications
- `offset` (int, default=0): Skip notifications
- `group_by_time` (bool, default=true): Group by date

**Response:**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "notification_date": "2025-01-28",
        "job_count": 5,
        "matched_keywords": ["iOS", "Swift"],
        "latest_sent_at": "2025-01-28T22:57:37.123456Z",
        "unread_count": 2,
        "jobs_preview": [
          {
            "title": "iOS Developer",
            "company": "Apple"
          }
        ]
      }
    ],
    "pagination": {
      "total": 10,
      "limit": 50,
      "offset": 0,
      "has_more": false
    }
  }
}
```

### POST `/api/v1/notifications/mark-read`
Mark notifications as read.

**Request Body:**
```json
{
  "device_token": "bff72bd38158b6a430b4c5feff7befd41aadf4634a715c4d7078be51ef77feff",
  "notification_ids": ["123", "456"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "2 notifications marked as read"
}
```

---

## User Profiles

### GET `/api/v1/users/profile/{device_token}`
Get user profile and preferences.

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user_123",
    "device_id": "5dde4e2a-4c63-47e1-9126-ffd0869e10fb",
    "profile": {
      "job_matches_enabled": true,
      "application_reminders_enabled": true,
      "weekly_digest_enabled": true,
      "market_insights_enabled": true
    },
    "keywords": ["iOS", "Swift", "Mobile Developer"],
    "notification_preferences": {
      "push_enabled": true,
      "quiet_hours": {
        "enabled": false,
        "start_time": "22:00",
        "end_time": "08:00"
      }
    },
    "created_at": "2025-01-28T22:57:37.123456Z",
    "last_active": "2025-01-28T23:15:42.987654Z"
  }
}
```

### PUT `/api/v1/users/profile/{device_token}`
Update user profile and preferences.

**Request Body:**
```json
{
  "job_matches_enabled": true,
  "application_reminders_enabled": false,
  "weekly_digest_enabled": true,
  "market_insights_enabled": true,
  "quiet_hours": {
    "enabled": true,
    "start_time": "22:00", 
    "end_time": "08:00"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "updated_fields": ["application_reminders_enabled", "quiet_hours"]
}
```

---

## Privacy & Analytics

### GET `/api/v1/privacy/status/{device_token}`
Get privacy consent status.

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": "5dde4e2a-4c63-47e1-9126-ffd0869e10fb",
    "analytics_consent": true,
    "marketing_consent": false,
    "data_sharing_consent": true,
    "last_updated": "2025-01-28T22:57:37.123456Z",
    "gdpr_compliant": true
  }
}
```

### POST `/api/v1/privacy/consent/{device_token}`
Update privacy consent preferences.

**Request Body:**
```json
{
  "analytics_consent": true,
  "marketing_consent": false,
  "data_sharing_consent": true
}
```

### POST `/api/v1/device/analytics/track`
Track user actions (respects consent).

**Request Body:**
```json
{
  "device_token": "bff72bd38158b6a430b4c5feff7befd41aadf4634a715c4d7078be51ef77feff",
  "action": "job_viewed",
  "metadata": {
    "job_id": "12345",
    "source": "notification"
  }
}
```

---

## Analytics Dashboard

### GET `/api/v1/device/analytics/summary`
Get analytics summary (aggregate data).

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_users": 1250,
      "total_notifications_sent": 45000,
      "avg_keywords_per_user": 3.2,
      "top_job_sources": ["linkedin", "indeed", "glassdoor"]
    },
    "top_keywords": [
      {
        "keyword": "iOS",
        "usage_count": 450,
        "percentage": 15.2
      }
    ]
  }
}
```

### GET `/api/v1/analytics/job-trends`
Get job market trends and insights.

**Query Parameters:**
- `days` (int, default=30): Trend period
- `limit` (int, default=10): Number of trends

**Response:**
```json
{
  "success": true,
  "data": {
    "trending_keywords": [
      {
        "keyword": "AI Engineer",
        "growth_rate": 45.2,
        "job_count": 1200
      }
    ],
    "top_companies": [
      {
        "company": "Google",
        "job_count": 89,
        "growth_rate": 12.5
      }
    ],
    "market_insights": {
      "total_jobs_added": 15000,
      "most_active_source": "linkedin",
      "peak_posting_hour": "10:00"
    }
  }
}
```

---

## Device Management

### GET `/api/v1/devices/active`
Get active devices summary (admin endpoint).

**Response:**
```json
{
  "success": true,
  "data": {
    "total_devices": 1250,
    "notifications_enabled": 1100,
    "avg_keywords": 3.2,
    "last_24h_registrations": 25
  }
}
```

### POST `/api/v1/devices/cleanup`
Clean up inactive devices (admin endpoint).

**Request Body:**
```json
{
  "days_inactive": 90
}
```

---

## Health & Status

### GET `/api/v1/health/`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-28T23:15:42.987654Z"
}
```

### GET `/api/v1/health/detailed`
Detailed system health with database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected", 
  "apns": "configured",
  "uptime": "2 days, 5 hours",
  "version": "4.0.0",
  "environment": "production"
}
```

---

## 🔧 Error Handling

All endpoints return consistent error format:

### 400 Bad Request
```json
{
  "detail": "Invalid device_token format"
}
```

### 404 Not Found
```json
{
  "detail": "Device not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Registration failed: Database connection error"
}
```

### Security Probe Detection
```json
{
  "detail": "Invalid device_token format"
}
```
*Note: Security probes (repeating character patterns) are automatically detected and blocked.*

---

## 📱 Mobile App Integration Guide

### iOS Integration

1. **Push Notification Setup:**
```swift
// Handle notification tap
func handleNotificationLaunch(userInfo: [String: Any]) {
    // Check for notification_id (required)
    if let notificationId = userInfo["notification_id"] as? String {
        // Extract session_id for navigation
        if let sessionId = userInfo["session_id"] as? String {
            navigateToJobMatches(sessionId: sessionId)
        }
    } else {
        // Show error page - notification_id missing
        showErrorView()
    }
}
```

2. **API Client Setup:**
```swift
struct APIClient {
    static let baseURL = "https://birjobbackend-ir3e.onrender.com/api/v1"
    
    func registerDevice(deviceToken: String, keywords: [String]) async throws {
        // POST /device/register
    }
    
    func getJobMatches(sessionId: String, page: Int = 1) async throws -> JobMatchResponse {
        // GET /job-matches/session/{sessionId}
    }
}
```

### Android Integration

1. **FCM Setup:**
```kotlin
// Handle notification data
class MyFirebaseMessagingService : FirebaseMessagingService() {
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        val notificationId = remoteMessage.data["notification_id"]
        val sessionId = remoteMessage.data["session_id"]
        
        if (notificationId != null && sessionId != null) {
            navigateToJobMatches(sessionId)
        }
    }
}
```

2. **API Client:**
```kotlin
class ApiClient {
    companion object {
        const val BASE_URL = "https://birjobbackend-ir3e.onrender.com/api/v1"
    }
    
    suspend fun registerDevice(deviceToken: String, keywords: List<String>): RegisterResponse
    suspend fun getJobMatches(sessionId: String, page: Int = 1): JobMatchResponse
}
```

---

## 🔐 Security Features

### Device Token Validation
- Hexadecimal format (64 chars)
- Security probe detection
- Rate limiting protection

### Privacy Compliance
- GDPR/CCPA consent management
- Data deletion capabilities
- Consent-based analytics

### API Security
- Input validation
- SQL injection prevention
- XSS protection
- Request rate limiting

---

## 🚀 Performance Optimization

### Caching Strategy
- Redis caching for frequent queries
- Database query optimization
- Pagination for large datasets

### Push Notification Efficiency
- Hash-based deduplication
- Notification throttling
- Bulk processing

### Database Optimization
- Indexed columns for fast queries
- Connection pooling
- Query result caching

---

## 📊 Monitoring & Analytics

### Key Metrics Tracked
- Device registrations
- Notification delivery rates
- User engagement
- API response times
- Error rates

### Analytics Events
- `registration` - Device registered
- `notification_received` - Push notification sent
- `job_viewed` - User viewed job
- `application_clicked` - User clicked apply
- `keywords_update` - Keywords modified

---

## 🛠️ Development Environment

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export APNS_KEY_ID="ABC123"
export APNS_TEAM_ID="DEF456"

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
- **Platform**: Render.com
- **Database**: PostgreSQL
- **Caching**: Redis
- **Push Notifications**: Apple APNs
- **Monitoring**: Built-in health checks

---

## 📞 Support & Troubleshooting

### Common Issues

1. **Push notifications not received:**
   - Verify device token format (64 hex chars)
   - Check APNs configuration
   - Ensure keywords are set

2. **"Cannot load matched jobs" error:**
   - Backend provides exact job structure as main jobs endpoint
   - Check session_id format in push payload
   - Verify API response format matches expectations

3. **Device registration fails:**
   - Validate device token format
   - Check for security probe patterns
   - Ensure keywords array is provided

### API Testing
Use the interactive docs at `/docs` for testing endpoints:
- Swagger UI with try-it-out functionality
- Request/response examples
- Schema validation

### Logs & Debugging
Production logs include:
- `📱 iOS DEBUG` - iOS-specific debugging info
- `🔔 Push notification sent` - Notification delivery
- `Security probe detected` - Blocked malicious requests

---

## 📋 Changelog

### v4.0.0 (Current)
- ✅ Session-based job matching system
- ✅ iOS notification_id compatibility 
- ✅ Enhanced push notification payload
- ✅ Simplified job data structure
- ✅ Complete mobile app integration support

### v3.0.0
- ✅ Push notification system overhaul
- ✅ Hash-based deduplication
- ✅ Privacy compliance features
- ✅ User profile management

---

**🎯 Ready for mobile app integration!** This backend provides everything needed for iOS and Android job notification apps with comprehensive push notification support, session-based job matching, and privacy-compliant analytics.