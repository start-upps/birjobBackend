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

## Device Registration & Management

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

### GET `/api/v1/device/status/{device_token}`
Get device registration status and configuration.

### DELETE `/api/v1/device/device/{device_token}`
Delete device and all associated data (GDPR compliance).

### POST `/api/v1/device/analytics/track`
Track user actions (respects consent).

### GET `/api/v1/device/analytics/summary`
Get analytics summary (aggregate data).

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

### GET `/api/v1/jobs/{job_id}`
Get specific job by ID.

### GET `/api/v1/jobs/hash/{job_hash}`
Get job by hash (for persistent links).

### GET `/api/v1/jobs/sources/list`
Get list of available job sources.

### GET `/api/v1/jobs/stats/summary`
Get job statistics summary.

---

## Push Notifications & Sessions

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

### GET `/api/v1/job-matches/session/{session_id}`
Get jobs from a specific notification session (used when user taps push notification).

**Path Parameters:**
- `session_id`: Session ID from push notification

**Query Parameters:**
- `page` (int, default=1): Page number (1-based)
- `limit` (int, default=20): Jobs per page (1-100)

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
  }
}
```

---

## Notification Management

### GET `/api/v1/notifications/inbox/{device_token}`
Get notification history/inbox for device.

### GET `/api/v1/notifications/history/{device_token}`
Get detailed notification history.

### POST `/api/v1/notifications/test/{device_token}`
Send test notification to device (for debugging).

### POST `/api/v1/notifications/mark-read/{device_token}`
Mark notifications as read.

### DELETE `/api/v1/notifications/clear/{device_token}`
Clear notification history.

### GET `/api/v1/notifications/job-by-hash/{job_hash}`
Get job details by hash (for notification links).

### POST `/api/v1/notifications/apply/{device_token}`
Track job application attempts.

### GET `/api/v1/notifications/settings/{device_token}`
Get notification settings.

### PUT `/api/v1/notifications/settings/{device_token}`
Update notification settings.

---

## User Profiles & Management

### GET `/api/v1/users/profile/{device_token}`
Get user profile and preferences.

### PUT `/api/v1/users/profile`
Update user profile.

### PUT `/api/v1/users/preferences`
Update user preferences.

### GET `/api/v1/users/activity/{device_token}`
Get user activity statistics.

### DELETE `/api/v1/users/account`
Delete user account (GDPR compliance).

### GET `/api/v1/users/stats/{device_token}`
Get user statistics.

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

### POST `/api/v1/privacy/consent`
Update privacy consent preferences.

### DELETE `/api/v1/privacy/data/{device_token}`
Delete user data (GDPR compliance).

### POST `/api/v1/privacy/export`
Export user data (GDPR compliance).

### GET `/api/v1/privacy/policy`
Get privacy policy.

### GET `/api/v1/privacy/analytics/anonymous`
Get anonymous analytics data.

---

## Market Analytics & Insights

### GET `/api/v1/analytics/market-overview`
Get high-level job market overview.

**Response:**
```json
{
  "success": true,
  "snapshot_time": "2025-01-28T23:15:42.987654Z",
  "market_overview": {
    "total_jobs": 3906,
    "unique_companies": 451,
    "unique_sources": 8,
    "data_freshness": {
      "oldest": "2025-01-28T08:24:12.514262Z",
      "newest": "2025-01-28T23:15:00.000000Z"
    }
  }
}
```

### GET `/api/v1/analytics/keyword-trends`
Analyze trending keywords and skills in job titles.

### GET `/api/v1/analytics/company-analytics`
Analyze company hiring activity and market presence.

### GET `/api/v1/analytics/title-analytics`
Analyze job titles and role demand patterns.

### GET `/api/v1/analytics/source-analytics`
Analyze job volume and distribution by source.

### GET `/api/v1/analytics/remote-work-analysis`
Analyze remote work opportunities.

### GET `/api/v1/analytics/market-competition`
Analyze market competition and job scarcity.

### GET `/api/v1/analytics/snapshot-summary`
Get comprehensive market snapshot summary.

### POST `/api/v1/analytics/event`
Track user analytics events.

---

## AI Chatbot

### POST `/api/v1/chatbot/chat/{device_token}`
Chat with AI career assistant.

### POST `/api/v1/chatbot/analyze-job/{device_token}`
Get AI analysis of specific job.

### GET `/api/v1/chatbot/recommendations/{device_token}`
Get AI career recommendations.

---

## Device Management (Admin)

### GET `/api/v1/devices/status/{device_token}`
Get detailed device status.

### PUT `/api/v1/devices/update/{device_token}`
Update device configuration.

### DELETE `/api/v1/devices/delete/{device_token}`
Delete device (admin).

### GET `/api/v1/devices/analytics/{device_token}`
Get device analytics.

### POST `/api/v1/devices/refresh-token/{old_device_token}`
Refresh device token.

### POST `/api/v1/devices/cleanup/test-data`
Cleanup test data (admin).

### GET `/api/v1/devices/debug/list-all`
List all devices (debug).

---

## Notification Processing (Internal)

### POST `/api/v1/minimal-notifications/process-all`
Process all pending notifications (internal).

### POST `/api/v1/minimal-notifications/process-jobs`
Process specific jobs for notifications.

### POST `/api/v1/minimal-notifications/send-single`
Send single notification.

### GET `/api/v1/minimal-notifications/stats`
Get notification processing statistics.

### GET `/api/v1/minimal-notifications/devices/active`
Get active devices count.

### POST `/api/v1/minimal-notifications/scraper-webhook`
Webhook for scraper integration.

---

## Health & System

### GET `/api/v1/health/`
Basic health check.

### GET `/api/v1/health/status`
Detailed health status.

### GET `/api/v1/health/status/scraper`
Scraper system health.

### POST `/api/v1/health/fix-device-token-length`
Fix device token length issues (admin).

### GET `/api/v1/health/db-debug`
Database debug information.

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