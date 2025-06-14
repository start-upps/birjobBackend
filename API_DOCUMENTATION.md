# iOS Job Matching Backend - Complete API Documentation

## Base Information
- **Base URL**: `https://birjobbackend-ir3e.onrender.com`
- **API Version**: v1
- **API Prefix**: `/api/v1`
- **Content Type**: `application/json`

## Authentication
The API uses optional JWT-based device authentication for some endpoints:
- **Header**: `Authorization: Bearer <jwt_token>`
- **Device Token Generation**: Handled internally after device registration
- **API Key** (for admin endpoints): `X-API-Key: <api_key>`

## API Endpoints

### 1. Health Check Endpoints

#### GET `/api/v1/health`
**Description**: System health check endpoint
**Authentication**: None required
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-14T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "apns": "healthy",
    "scraper": "healthy"
  },
  "metrics": {
    "active_devices": 150,
    "active_subscriptions": 200,
    "matches_last_24h": 450,
    "notifications_sent_last_24h": 320
  }
}
```

#### GET `/api/v1/health/status/scraper`
**Description**: Detailed scraper status and statistics
**Authentication**: None required
**Response**:
```json
{
  "status": "running",
  "last_run": null,
  "next_run": null,
  "sources": [
    {
      "name": "linkedin",
      "status": "healthy",
      "last_successful_scrape": "2025-06-14T09:00:00Z",
      "jobs_scraped_last_run": 145,
      "error_count_24h": 0
    }
  ],
  "total_jobs_last_24h": 850,
  "errors_last_24h": 0
}
```

### 2. Device Management Endpoints

#### POST `/api/v1/devices/register`
**Description**: Register a new iOS device for push notifications
**Authentication**: None required
**Request Body**:
```json
{
  "device_token": "64-character-apns-device-token-here",
  "device_info": {
    "osVersion": "17.5.1",
    "appVersion": "1.0.0",
    "deviceModel": "iPhone15,2",
    "timezone": "America/New_York"
  }
}
```

**Validation Rules**:
- `device_token`: Required, 64-255 characters
- `device_info.osVersion`: Required string
- `device_info.appVersion`: Required string
- `device_info.deviceModel`: Required string
- `device_info.timezone`: Required string

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "registered_at": "2025-06-14T10:30:00Z"
  }
}
```

**Error Responses**:
- `400`: Invalid request data
- `500`: Internal server error

#### DELETE `/api/v1/devices/{device_id}`
**Description**: Unregister a device from push notifications
**Authentication**: None required
**Path Parameters**:
- `device_id`: UUID format string

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Device unregistered successfully"
}
```

**Error Responses**:
- `400`: Invalid device ID format
- `404`: Device not found
- `500`: Internal server error

#### GET `/api/v1/devices/{device_id}/status`
**Description**: Get device registration status and basic info
**Authentication**: None required
**Path Parameters**:
- `device_id`: UUID format string

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_active": true,
    "registered_at": "2025-06-14T08:00:00Z",
    "last_seen": "2025-06-14T10:30:00Z",
    "device_info": {
      "osVersion": "17.5.1",
      "appVersion": "1.0.0",
      "deviceModel": "iPhone15,2",
      "timezone": "America/New_York"
    }
  }
}
```

### 3. Keyword Subscription Endpoints

#### POST `/api/v1/keywords`
**Description**: Subscribe a device to keyword-based job notifications
**Authentication**: None required
**Request Body**:
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keywords": ["iOS Developer", "Swift", "React Native"],
  "sources": ["linkedin", "indeed", "glassdoor"],
  "location_filters": {
    "cities": ["New York", "San Francisco"],
    "remote_only": false
  }
}
```

**Validation Rules**:
- `device_id`: Required UUID string
- `keywords`: Required array, 1-20 items
- `sources`: Optional array of strings
- `location_filters`: Optional object
- `location_filters.cities`: Optional array of strings
- `location_filters.remote_only`: Optional boolean, default false

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "subscription_id": "660e8400-e29b-41d4-a716-446655440001",
    "keywords_count": 3,
    "sources_count": 3,
    "created_at": "2025-06-14T10:30:00Z"
  }
}
```

#### GET `/api/v1/keywords/{device_id}`
**Description**: Retrieve current keyword subscriptions for a device
**Authentication**: None required
**Path Parameters**:
- `device_id`: UUID format string

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "subscription_id": "660e8400-e29b-41d4-a716-446655440001",
        "keywords": ["iOS Developer", "Swift", "React Native"],
        "sources": ["linkedin", "indeed"],
        "location_filters": {
          "cities": ["New York"],
          "remote_only": false
        },
        "created_at": "2025-06-14T08:00:00Z",
        "last_match": "2025-06-14T09:15:00Z"
      }
    ]
  }
}
```

#### PUT `/api/v1/keywords/{subscription_id}`
**Description**: Update keyword subscription settings
**Authentication**: None required
**Path Parameters**:
- `subscription_id`: UUID format string

**Request Body**: Same as POST `/api/v1/keywords`

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "subscription_id": "660e8400-e29b-41d4-a716-446655440001",
    "keywords_count": 3,
    "sources_count": 2,
    "updated_at": "2025-06-14T10:30:00Z"
  }
}
```

#### DELETE `/api/v1/keywords/{subscription_id}`
**Description**: Remove a keyword subscription
**Authentication**: None required
**Path Parameters**:
- `subscription_id`: UUID format string

**Query Parameters**:
- `device_id`: Required UUID string for ownership verification

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Keyword subscription removed successfully"
}
```

### 4. Job Endpoints

#### GET `/api/v1/jobs/`
**Description**: Get jobs with filtering, search, and pagination
**Authentication**: None required
**Query Parameters**:
- `limit`: Integer (1-100), default 20
- `offset`: Integer (≥0), default 0
- `search`: String (search in title, company)
- `company`: String (filter by company name)
- `source`: String (filter by source)
- `location`: String (filter by location)
- `days`: Integer (1-365) (jobs posted within last N days)
- `sort_by`: String (created_at|title|company), default "created_at"
- `sort_order`: String (asc|desc), default "desc"

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": 12345,
        "title": "Senior iOS Developer",
        "company": "Tech Corp",
        "apply_link": "https://techcorp.com/jobs/12345",
        "source": "linkedin",
        "posted_at": "2025-06-14T08:00:00Z"
      }
    ],
    "pagination": {
      "total": 1500,
      "limit": 20,
      "offset": 0,
      "current_page": 1,
      "total_pages": 75,
      "has_more": true,
      "has_previous": false
    },
    "filters": {
      "search": "iOS",
      "company": null,
      "source": null,
      "location": null,
      "days": 7,
      "sort_by": "created_at",
      "sort_order": "desc"
    }
  }
}
```

#### GET `/api/v1/jobs/{job_id}`
**Description**: Get detailed information for a specific job
**Authentication**: None required
**Path Parameters**:
- `job_id`: Integer

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "job": {
      "id": 12345,
      "title": "Senior iOS Developer",
      "company": "Tech Corp",
      "apply_link": "https://techcorp.com/jobs/12345",
      "source": "linkedin",
      "posted_at": "2025-06-14T08:00:00Z"
    }
  }
}
```

**Error Response (404)**:
```json
{
  "detail": "Job not found"
}
```

#### GET `/api/v1/jobs/stats/summary`
**Description**: Get job statistics and summary information
**Authentication**: None required

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "total_jobs": 15420,
    "recent_jobs_24h": 287,
    "top_companies": [
      {
        "company": "Google",
        "job_count": 45
      },
      {
        "company": "Apple",
        "job_count": 38
      }
    ],
    "job_sources": [
      {
        "source": "linkedin",
        "job_count": 8500
      },
      {
        "source": "indeed",
        "job_count": 4200
      }
    ],
    "last_updated": "2025-06-14T10:30:00Z"
  }
}
```

### 5. Job Matches Endpoints

#### GET `/api/v1/matches/{device_id}`
**Description**: Retrieve recent job matches for a device
**Authentication**: None required
**Path Parameters**:
- `device_id`: UUID format string

**Query Parameters**:
- `limit`: Integer (1-100), default 20
- `offset`: Integer (≥0), default 0
- `since`: String (ISO timestamp, optional)

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "770e8400-e29b-41d4-a716-446655440002",
        "job": {
          "id": 12345,
          "title": "Senior iOS Developer",
          "company": "Tech Corp",
          "apply_link": "https://techcorp.com/jobs/12345",
          "source": "linkedin",
          "posted_at": "2025-06-14T08:00:00Z"
        },
        "matched_keywords": ["iOS", "Swift"],
        "relevance_score": 0.85,
        "matched_at": "2025-06-14T09:15:00Z"
      }
    ],
    "pagination": {
      "total": 25,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

#### POST `/api/v1/matches/{match_id}/read`
**Description**: Mark a job match as read/viewed
**Authentication**: None required
**Path Parameters**:
- `match_id`: UUID format string

**Query Parameters**:
- `device_id`: Required UUID string for ownership verification

**Success Response (200)**:
```json
{
  "success": true,
  "message": "Match marked as read"
}
```

#### GET `/api/v1/matches/{device_id}/unread-count`
**Description**: Get count of unread matches for a device
**Authentication**: None required
**Path Parameters**:
- `device_id`: UUID format string

**Success Response (200)**:
```json
{
  "success": true,
  "data": {
    "unread_count": 5
  }
}
```

## Push Notification System

### Push Notification Types
1. **Job Match**: Sent when a new job matches user keywords
2. **Daily Digest**: Summary of matches sent daily
3. **System**: Administrative notifications

### Push Notification Payload Example
```json
{
  "aps": {
    "alert": {
      "title": "New Job Match! 🎯",
      "subtitle": "Senior iOS Developer at Tech Corp",
      "body": "Matches your keywords: iOS, Swift"
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
    "matched_keywords": ["iOS", "Swift"],
    "deep_link": "birjob://job/12345"
  }
}
```

### Push Notification Settings
- **Rate Limiting**: 5 notifications per hour, 20 per day per device
- **Quiet Hours**: 10 PM - 8 AM (configurable)
- **Delivery**: Apple Push Notification Service (APNs)

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes
- `200`: Success
- `400`: Bad Request (validation errors, invalid parameters)
- `401`: Unauthorized (invalid API key or token)
- `404`: Not Found (resource doesn't exist)
- `422`: Unprocessable Entity (validation errors)
- `500`: Internal Server Error

## Data Models

### Device Registration Schema
```typescript
interface DeviceInfo {
  osVersion: string;      // iOS version
  appVersion: string;     // App version
  deviceModel: string;    // Device model identifier
  timezone: string;       // Device timezone
}

interface DeviceRegisterRequest {
  device_token: string;   // 64-255 characters APNs token
  device_info: DeviceInfo;
}
```

### Keyword Subscription Schema
```typescript
interface LocationFilters {
  cities?: string[];      // Optional city filters
  remote_only?: boolean;  // Filter for remote jobs only
}

interface KeywordSubscriptionRequest {
  device_id: string;                    // UUID
  keywords: string[];                   // 1-20 keywords
  sources?: string[];                   // Optional job sources
  location_filters?: LocationFilters;   // Optional location filters
}
```

### Job Schema
```typescript
interface Job {
  id: number;
  title: string;
  company: string;
  apply_link: string;
  source: string;
  posted_at: string;      // ISO timestamp
}
```

### Job Match Schema
```typescript
interface JobMatch {
  match_id: string;       // UUID
  job: Job;
  matched_keywords: string[];
  relevance_score: number; // 0.0 to 1.0
  matched_at: string;     // ISO timestamp
}
```

## Swift Data Models

```swift
// Device Registration
struct DeviceInfo: Codable {
    let osVersion: String
    let appVersion: String
    let deviceModel: String
    let timezone: String
}

struct DeviceRegisterRequest: Codable {
    let deviceToken: String
    let deviceInfo: DeviceInfo
    
    enum CodingKeys: String, CodingKey {
        case deviceToken = "device_token"
        case deviceInfo = "device_info"
    }
}

struct DeviceRegisterResponse: Codable {
    let success: Bool
    let data: DeviceData
    
    struct DeviceData: Codable {
        let deviceId: String
        let registeredAt: String
        
        enum CodingKeys: String, CodingKey {
            case deviceId = "device_id"
            case registeredAt = "registered_at"
        }
    }
}

// Keyword Subscription
struct LocationFilters: Codable {
    let cities: [String]?
    let remoteOnly: Bool?
    
    enum CodingKeys: String, CodingKey {
        case cities
        case remoteOnly = "remote_only"
    }
}

struct KeywordSubscriptionRequest: Codable {
    let deviceId: String
    let keywords: [String]
    let sources: [String]?
    let locationFilters: LocationFilters?
    
    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case keywords
        case sources
        case locationFilters = "location_filters"
    }
}

// Job
struct Job: Codable, Identifiable {
    let id: Int
    let title: String
    let company: String
    let applyLink: String
    let source: String
    let postedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, title, company, source
        case applyLink = "apply_link"
        case postedAt = "posted_at"
    }
}

// Job Match
struct JobMatch: Codable, Identifiable {
    let matchId: String
    let job: Job
    let matchedKeywords: [String]
    let relevanceScore: Double
    let matchedAt: String
    
    var id: String { matchId }
    
    enum CodingKeys: String, CodingKey {
        case matchId = "match_id"
        case job
        case matchedKeywords = "matched_keywords"
        case relevanceScore = "relevance_score"
        case matchedAt = "matched_at"
    }
}

// API Response Wrappers
struct JobsResponse: Codable {
    let success: Bool
    let data: JobsData
    
    struct JobsData: Codable {
        let jobs: [Job]
        let pagination: Pagination
        let filters: Filters
    }
}

struct Pagination: Codable {
    let total: Int
    let limit: Int
    let offset: Int
    let currentPage: Int
    let totalPages: Int
    let hasMore: Bool
    let hasPrevious: Bool
    
    enum CodingKeys: String, CodingKey {
        case total, limit, offset
        case currentPage = "current_page"
        case totalPages = "total_pages"
        case hasMore = "has_more"
        case hasPrevious = "has_previous"
    }
}

struct Filters: Codable {
    let search: String?
    let company: String?
    let source: String?
    let location: String?
    let days: Int?
    let sortBy: String
    let sortOrder: String
    
    enum CodingKeys: String, CodingKey {
        case search, company, source, location, days
        case sortBy = "sort_by"
        case sortOrder = "sort_order"
    }
}

struct MatchesResponse: Codable {
    let success: Bool
    let data: MatchesData
    
    struct MatchesData: Codable {
        let matches: [JobMatch]
        let pagination: Pagination
    }
}
```

## Rate Limiting and Throttling

### Push Notification Limits
- **Hourly**: 5 notifications per device
- **Daily**: 20 notifications per device
- **Quiet Hours**: 10 PM - 8 AM (notifications delayed)

### API Rate Limits
- **General**: 1000 requests per hour per IP
- **Health Checks**: No rate limiting
- **Job Queries**: Standard rate limiting applies

## Deep Link Schema
The app supports deep linking with the following URL scheme:
- **App Scheme**: `birjob://`
- **Job Details**: `birjob://job/{job_id}`
- **Matches**: `birjob://matches`
- **Settings**: `birjob://settings`

## Development Notes

### Environment Configuration
- **Base URL**: Production endpoint provided
- **APNs**: Configured for sandbox and production
- **Database**: PostgreSQL with separate schemas for app data and scraped jobs
- **Caching**: Redis for performance optimization
- **Monitoring**: Built-in health checks and metrics

### Testing Endpoints
You can test the API using the provided `/health` and `/api/v1/jobs/stats/summary` endpoints to verify connectivity and data availability before implementing full device registration and subscription flows.

### Example API Usage Flow

1. **Device Registration**:
   ```
   POST /api/v1/devices/register
   ```

2. **Create Keyword Subscription**:
   ```
   POST /api/v1/keywords
   ```

3. **Fetch Jobs**:
   ```
   GET /api/v1/jobs/?search=iOS&limit=20
   ```

4. **Get Job Matches**:
   ```
   GET /api/v1/matches/{device_id}
   ```

5. **Mark Match as Read**:
   ```
   POST /api/v1/matches/{match_id}/read?device_id={device_id}
   ```

This comprehensive API documentation provides all the information needed to build an iOS app that can register devices, manage keyword subscriptions, fetch job listings, receive push notifications, and track job matches through this backend system.