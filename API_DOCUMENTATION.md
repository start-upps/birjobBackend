# iOS Job Matching Backend - Complete API Documentation

## Base Information
- **Base URL**: `https://birjobbackend-ir3e.onrender.com` (Production) / `http://localhost:8000` (Development)
- **API Version**: v1.1.0
- **API Prefix**: `/api/v1`
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## System Status (Updated: 2025-06-29 - Unified User System)
- ✅ **Working**: 95%+ of endpoints fully operational
- 🎯 **Status**: Unified user system deployed, all core functionality working
- 📊 **Database**: PostgreSQL (unified users_unified table), Redis, APNs - All healthy
- 📈 **Current Data**: 4,482+ jobs from multiple sources
- 🚀 **Latest**: Database consolidation complete, enhanced keyword matching system

---

## 1. Root Endpoints

### GET `/`
**Status**: ✅ Working  
**Description**: API service information

**Response**:
```json
{
  "message": "iOS Native App Backend API",
  "version": "1.1.0"
}
```

### GET `/api`
**Status**: ✅ Working  
**Description**: API root endpoint

**Response**:
```json
{
  "message": "iOS Native App Backend API",
  "version": "1.1.0"
}
```

---

## 2. Health & System Endpoints

### GET `/api/v1/health`
**Status**: ✅ Working  
**Description**: Comprehensive system health check

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-29T01:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "apns": "healthy",
    "scraper": "healthy"
  },
  "uptime": "15d 4h 23m",
  "version": "1.1.0"
}
```

### GET `/api/v1/health/status/scraper`
**Status**: ✅ Working  
**Description**: Scraper service status

### GET `/api/v1/health/scheduler-status`
**Status**: ✅ Working  
**Description**: Job scheduler status

### GET `/api/v1/health/check-user-tables`
**Status**: ✅ Working  
**Description**: Verify user table structure

### GET `/api/v1/health/db-debug`
**Status**: ✅ Working  
**Description**: Database connectivity debug information

### POST `/api/v1/health/create-user-tables`
**Status**: ✅ Working  
**Description**: Create/update user tables structure

---

## 3. Jobs Endpoints

### GET `/api/v1/jobs/`
**Status**: ✅ Working  
**Description**: Get paginated list of jobs

**Parameters**:
- `limit` (optional): Number of jobs to return (default: 20, max: 100)
- `offset` (optional): Number of jobs to skip (default: 0)

**Response**:
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Software Engineer",
      "company": "Tech Corp",
      "apply_link": "https://example.com/apply",
      "source": "indeed",
      "created_at": "2025-06-29T01:00:00Z"
    }
  ],
  "total": 4482,
  "limit": 20,
  "offset": 0
}
```

### GET `/api/v1/jobs/stats/summary`
**Status**: ✅ Working  
**Description**: Get job statistics summary

**Response**:
```json
{
  "totalJobs": 4482,
  "totalCompanies": 1751,
  "totalSources": 37,
  "lastUpdated": "2025-06-29T01:00:00Z",
  "jobsBySource": {
    "indeed": 2500,
    "linkedin": 1200,
    "glassdoor": 782
  }
}
```

---

## 4. Analytics Endpoints

### GET `/api/v1/analytics/jobs/overview`
**Status**: ✅ Working  
**Description**: Job market overview analytics

**Response**:
```json
{
  "totalJobs": 4482,
  "totalCompanies": 1751,
  "averageJobsPerCompany": 2.56,
  "topJobTitles": ["Software Engineer", "Data Analyst"],
  "lastUpdated": "2025-06-29T01:00:00Z"
}
```

### GET `/api/v1/analytics/jobs/by-source`
**Status**: ✅ Working  
**Description**: Jobs breakdown by source

### GET `/api/v1/analytics/jobs/by-company`
**Status**: ✅ Working  
**Description**: Jobs breakdown by company

**Parameters**:
- `limit` (optional): Number of companies to return (default: 10)

### GET `/api/v1/analytics/jobs/current-cycle`
**Status**: ✅ Working  
**Description**: Current scraping cycle information

### GET `/api/v1/analytics/jobs/keywords`
**Status**: ✅ Working  
**Description**: Popular job keywords analysis

**Parameters**:
- `limit` (optional): Number of keywords to return (default: 10)

### GET `/api/v1/analytics/jobs/search`
**Status**: ✅ Working  
**Description**: Search jobs by keyword

**Parameters**:
- `keyword` (required): Keyword to search for

---

## 5. User Profile Management (Unified System)

### POST `/api/v1/users/profile`
**Status**: ✅ Working  
**Description**: Create or update user profile using unified system

**Request Body**:
```json
{
  "device_id": "user-device-123",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "location": "San Francisco",
  "current_job_title": "Software Engineer",
  "skills": ["python", "react", "docker"],
  "match_keywords": ["python", "backend", "api"],
  "desired_job_types": ["Full-time", "Remote"],
  "min_salary": 80000,
  "max_salary": 120000,
  "job_matches_enabled": true,
  "profile_visibility": "private"
}
```

**Response**:
```json
{
  "success": true,
  "message": "User profile created/updated successfully",
  "data": {
    "userId": "ca26a660-f391-42ff-9439-f51dc057e456",
    "deviceId": "user-device-123",
    "profileCompleteness": 75,
    "lastUpdated": "2025-06-29T01:00:00Z"
  }
}
```

### GET `/api/v1/users/profile/{device_id}`
**Status**: ✅ Working  
**Description**: Get user profile by device ID

**Response**:
```json
{
  "success": true,
  "message": "Profile retrieved successfully",
  "data": {
    "userId": "ca26a660-f391-42ff-9439-f51dc057e456",
    "deviceId": "user-device-123",
    "personalInfo": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com",
      "location": "San Francisco",
      "currentJobTitle": "Software Engineer"
    },
    "jobPreferences": {
      "desiredJobTypes": ["Full-time", "Remote"],
      "skills": ["python", "react", "docker"],
      "matchKeywords": ["python", "backend", "api"],
      "salaryRange": {
        "minSalary": 80000,
        "maxSalary": 120000,
        "currency": "USD",
        "isNegotiable": true
      }
    },
    "notificationSettings": {
      "jobMatchesEnabled": true,
      "applicationRemindersEnabled": true,
      "weeklyDigestEnabled": true
    },
    "privacySettings": {
      "profileVisibility": "private",
      "shareAnalytics": false
    },
    "profileCompleteness": 75,
    "createdAt": "2025-06-29T01:00:00Z",
    "lastUpdated": "2025-06-29T01:00:00Z"
  }
}
```

---

## 6. Keyword Management System

### GET `/api/v1/users/{device_id}/profile/keywords`
**Status**: ✅ Working  
**Description**: Get user's profile keywords for job matching

**Response**:
```json
{
  "success": true,
  "data": {
    "matchKeywords": ["python", "backend", "api"],
    "keywordCount": 3,
    "lastUpdated": "2025-06-29T01:00:00Z",
    "relatedSkills": ["python", "react", "docker"]
  }
}
```

### POST `/api/v1/users/{device_id}/profile/keywords/add`
**Status**: ✅ Working  
**Description**: Add a single keyword to user's profile

**Request Body**:
```json
{
  "keyword": "kubernetes"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Keyword added successfully",
  "data": {
    "matchKeywords": ["python", "backend", "api", "kubernetes"],
    "keywordCount": 4,
    "addedKeyword": "kubernetes",
    "lastUpdated": "2025-06-29T01:00:00Z"
  }
}
```

### POST `/api/v1/users/{device_id}/profile/keywords`
**Status**: ✅ Working  
**Description**: Update complete keywords list

**Request Body**:
```json
{
  "match_keywords": ["python", "fastapi", "docker", "kubernetes", "postgresql"]
}
```

**Response**:
```json
{
  "success": true,
  "message": "Keywords updated successfully",
  "data": {
    "matchKeywords": ["python", "fastapi", "docker", "kubernetes", "postgresql"],
    "keywordCount": 5,
    "lastUpdated": "2025-06-29T01:00:00Z"
  }
}
```

### DELETE `/api/v1/users/{device_id}/profile/keywords/{keyword}`
**Status**: ✅ Working  
**Description**: Remove a keyword from user's profile

**Response**:
```json
{
  "success": true,
  "message": "Keyword removed successfully",
  "data": {
    "matchKeywords": ["python", "fastapi", "docker", "postgresql"],
    "keywordCount": 4,
    "removedKeyword": "kubernetes",
    "lastUpdated": "2025-06-29T01:00:00Z"
  }
}
```

---

## 7. Intelligent Job Matching

### GET `/api/v1/users/{device_id}/profile/matches`
**Status**: ✅ Working  
**Description**: Get intelligent job matches based on profile keywords

**Parameters**:
- `limit` (optional): Number of matches to return (default: 20, max: 100)
- `offset` (optional): Number of matches to skip (default: 0)

**Response**:
```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "jobId": 12345,
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "Remote",
        "salary": "Competitive",
        "description": "Senior Python Developer position...",
        "source": "indeed",
        "postedAt": "2025-06-29T01:00:00Z",
        "matchScore": 87.5,
        "matchedKeywords": ["python", "fastapi"],
        "matchReasons": [
          "Strong match for 'python' in job title",
          "Good match for 'fastapi' in job description"
        ],
        "keywordRelevance": {
          "python": {
            "score": 45.2,
            "matches": ["title (1.3x)", "requirements (1.2x)"]
          }
        }
      }
    ],
    "totalCount": 15,
    "userKeywords": ["python", "fastapi", "docker", "kubernetes", "postgresql"],
    "matchingStats": {
      "totalJobsEvaluated": 60,
      "jobsWithMatches": 15,
      "averageScore": 65.3,
      "topScore": 87.5
    }
  }
}
```

---

## 8. Device Management

### POST `/api/v1/devices/register`
**Status**: ✅ Working  
**Description**: Register a new device for push notifications

**Request Body**:
```json
{
  "deviceToken": "valid-apns-token-64-chars-long",
  "deviceType": "iOS",
  "appVersion": "1.0.0"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Device registered successfully",
  "deviceId": "generated-device-id",
  "registeredAt": "2025-06-29T01:00:00Z"
}
```

### GET `/api/v1/devices/{device_id}/status`
**Status**: ✅ Working  
**Description**: Get device registration status

### DELETE `/api/v1/devices/{device_id}`
**Status**: ✅ Working  
**Description**: Unregister a device

---

## 9. AI Services

### POST `/api/v1/ai/analyze`
**Status**: ✅ Working  
**Description**: Analyze job description or resume content

**Request Body**:
```json
{
  "text": "Job description or resume content to analyze"
}
```

### POST `/api/v1/ai/job-advice`
**Status**: ✅ Working  
**Description**: Get AI-powered job advice

**Request Body**:
```json
{
  "jobTitle": "Software Engineer",
  "experience": "3 years",
  "skills": ["python", "react"]
}
```

### POST `/api/v1/ai/resume-review`
**Status**: ✅ Working  
**Description**: Get AI resume review and suggestions

**Request Body**:
```json
{
  "resumeText": "Complete resume content"
}
```

---

## 10. Legacy Compatibility

### POST `/api/v1/users/profile/sync`
**Status**: ✅ Working  
**Description**: Sync user profile between devices

**Parameters**:
- `sourceDeviceId` (query): Source device ID
- `targetDeviceId` (query): Target device ID

**Response**:
```json
{
  "success": true,
  "message": "Profile synced successfully",
  "data": {
    "targetDeviceId": "target-device-id",
    "profileCompleteness": 75
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message",
  "details": "Additional error details"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `404`: Not Found (resource doesn't exist)
- `422`: Unprocessable Entity (invalid data format)
- `500`: Internal Server Error

---

## Key Features

### 🚀 **Unified User System**
- Single optimized database table
- Auto-calculating profile completeness (0-100%)
- Enhanced performance with GIN indexes
- Backward compatibility maintained

### 🎯 **Intelligent Job Matching**
- Keyword-based scoring system (0-100 scale)
- Multi-factor scoring: Title (40%), Requirements (30%), Description (20%), Company (10%)
- Detailed match explanations and keyword relevance
- Real-time matching with comprehensive statistics

### 📊 **Performance Optimizations**
- Sub-second response times
- Optimized database queries
- JSONB storage for flexible data
- Comprehensive indexing strategy

### 📱 **iOS App Ready**
- Complete backward compatibility
- Legacy API format maintained
- No breaking changes required
- Immediate benefits from unified system

---

## Rate Limiting

No rate limiting currently implemented, but recommended for production:
- User endpoints: 100 requests/minute per device
- Analytics endpoints: 50 requests/minute per IP
- Job search: 20 requests/minute per device

---

## Authentication

Currently using device-based identification. No OAuth or API keys required.
Device ID serves as the primary identifier for user-specific operations.

---

*Last Updated: June 29, 2025 - Unified User System v1.1.0*