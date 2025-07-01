# iOS Backend API Documentation
**Complete API Reference for iOS App Development**

**Base URL**: `https://birjobbackend-ir3e.onrender.com/api/v1`  
**Authentication**: API Key required in header `X-API-Key: birjob-ios-api-key-2024`  
**Content-Type**: `application/json`  
**Database Schema**: Optimized RDBMS with proper foreign key relationships

---

## 📱 Core Authentication & Headers

All API requests must include these headers:

```http
X-API-Key: birjob-ios-api-key-2024
Content-Type: application/json
```

---

## 🏥 Health & System Status

### GET `/health`
**Purpose**: Check system health and database connectivity  
**iOS Usage**: App startup health check, connectivity monitoring

**Request**:
```http
GET /api/v1/health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "database_status": "connected",
  "redis_status": "connected", 
  "timestamp": "2025-06-30T12:00:00Z",
  "version": "1.0.0"
}
```

**iOS Implementation**:
```swift
func checkSystemHealth() async throws -> HealthResponse {
    let url = baseURL.appendingPathComponent("health")
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(HealthResponse.self, from: data)
}
```

### GET `/health/db-debug`
**Purpose**: Detailed database connection debugging  
**iOS Usage**: Troubleshooting connectivity issues

**Response** (200 OK):
```json
{
  "database_connection": "active",
  "tables_accessible": true,
  "schema_version": "optimized_v2",
  "foreign_keys": 10,
  "indexes": 62
}
```

---

## 👤 User Profile Management

### POST `/users/profile`
**Purpose**: Create or update user profile (UPSERT operation)  
**iOS Usage**: User registration, profile updates, settings changes

**Request Body**:
```json
{
  "device_id": "unique_device_identifier",
  "first_name": "John",
  "last_name": "Doe", 
  "email": "john.doe@email.com",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "current_job_title": "iOS Developer",
  "years_of_experience": 5,
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  "portfolio_url": "https://johndoe.dev",
  "bio": "Passionate iOS developer with 5 years experience",
  
  "desired_job_types": ["full-time", "contract", "remote"],
  "remote_work_preference": "hybrid",
  "skills": ["Swift", "SwiftUI", "iOS", "UIKit", "Core Data"],
  "preferred_locations": ["San Francisco", "New York", "Remote"],
  "match_keywords": ["ios developer", "swift", "mobile"],
  
  "min_salary": 120000,
  "max_salary": 180000,
  "salary_currency": "USD",
  "salary_negotiable": true,
  
  "job_matches_enabled": true,
  "application_reminders_enabled": true,
  "weekly_digest_enabled": false,
  "market_insights_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "preferred_notification_time": "09:00",
  
  "profile_visibility": "private",
  "share_analytics": false,
  "share_job_view_history": false,
  "allow_personalized_recommendations": true,
  
  "additional_personal_info": {},
  "additional_job_preferences": {},
  "additional_notification_settings": {},
  "additional_privacy_settings": {}
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "User profile created/updated successfully",
  "profile_completeness": 85,
  "updated_fields": ["bio", "skills", "salary_range"],
  "timestamp": "2025-06-30T12:00:00Z"
}
```

**Response** (422 Validation Error):
```json
{
  "detail": [
    {
      "loc": ["body", "device_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**iOS Implementation**:
```swift
func createOrUpdateProfile(_ profile: UserProfile) async throws -> ProfileResponse {
    var request = URLRequest(url: baseURL.appendingPathComponent("users/profile"))
    request.httpMethod = "POST"
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.httpBody = try JSONEncoder().encode(profile)
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(ProfileResponse.self, from: data)
}
```

### GET `/users/profile/{device_id}`
**Purpose**: Retrieve complete user profile  
**iOS Usage**: Load user data, display profile, check completeness

**Path Parameters**:
- `device_id` (string, required): Unique device identifier

**Request**:
```http
GET /api/v1/users/profile/device_12345abcdef
```

**Response** (200 OK):
```json
{
  "id": "uuid-user-id",
  "device_id": "device_12345abcdef",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@email.com",
  "phone": "+1234567890",
  "location": "San Francisco, CA",
  "current_job_title": "iOS Developer",
  "years_of_experience": 5,
  "linkedin_profile": "https://linkedin.com/in/johndoe",
  "portfolio_url": "https://johndoe.dev",
  "bio": "Passionate iOS developer",
  
  "desired_job_types": ["full-time", "remote"],
  "remote_work_preference": "hybrid",
  "skills": ["Swift", "SwiftUI", "iOS"],
  "preferred_locations": ["San Francisco", "Remote"],
  "match_keywords": ["ios developer", "swift"],
  
  "min_salary": 120000,
  "max_salary": 180000,
  "salary_currency": "USD",
  "salary_negotiable": true,
  
  "job_matches_enabled": true,
  "application_reminders_enabled": true,
  "weekly_digest_enabled": false,
  "market_insights_enabled": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00",
  "quiet_hours_end": "08:00",
  "preferred_notification_time": "09:00",
  
  "profile_visibility": "private",
  "share_analytics": false,
  "share_job_view_history": false,
  "allow_personalized_recommendations": true,
  
  "profile_completeness": 85,
  "is_active": true,
  "created_at": "2025-06-30T12:00:00Z",
  "updated_at": "2025-06-30T12:00:00Z",
  
  "additional_personal_info": {},
  "additional_job_preferences": {},
  "additional_notification_settings": {},
  "additional_privacy_settings": {}
}
```

**Response** (404 Not Found):
```json
{
  "detail": "User profile not found for device_id: device_12345abcdef"
}
```

**iOS Implementation**:
```swift
func getUserProfile(deviceId: String) async throws -> UserProfile {
    let url = baseURL.appendingPathComponent("users/profile/\(deviceId)")
    var request = URLRequest(url: url)
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(UserProfile.self, from: data)
}
```

---

## 🔑 Keywords Management

### GET `/users/{device_id}/profile/keywords`
**Purpose**: Get user's job search keywords and preferences  
**iOS Usage**: Display current keywords, keyword management screen

**Path Parameters**:
- `device_id` (string, required): Unique device identifier

**Response** (200 OK):
```json
{
  "device_id": "device_12345abcdef",
  "keywords": ["ios developer", "swift engineer", "mobile developer"],
  "location_filters": {
    "cities": ["San Francisco", "New York"],
    "remote_ok": true,
    "countries": ["US"]
  },
  "source_filters": ["linkedin", "indeed", "glassdoor"],
  "is_active": true,
  "total_keywords": 3,
  "last_updated": "2025-06-30T12:00:00Z"
}
```

**iOS Implementation**:
```swift
func getUserKeywords(deviceId: String) async throws -> KeywordsResponse {
    let url = baseURL.appendingPathComponent("users/\(deviceId)/profile/keywords")
    var request = URLRequest(url: url)
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(KeywordsResponse.self, from: data)
}
```

### POST `/users/{device_id}/profile/keywords`
**Purpose**: Update user's complete keyword preferences  
**iOS Usage**: Save keyword preferences, bulk keyword update

**Path Parameters**:
- `device_id` (string, required): Unique device identifier

**Request Body**:
```json
{
  "keywords": ["ios developer", "swift engineer", "mobile architect"],
  "location_filters": {
    "cities": ["San Francisco", "Seattle", "Austin"],
    "remote_ok": true,
    "countries": ["US", "CA"]
  },
  "source_filters": ["linkedin", "indeed", "glassdoor", "stackoverflow"]
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Keywords updated successfully",
  "keywords_count": 3,
  "location_filters_count": 3,
  "source_filters_count": 4,
  "updated_at": "2025-06-30T12:00:00Z"
}
```

### POST `/users/{device_id}/profile/keywords/add`
**Purpose**: Add a single keyword to existing keywords  
**iOS Usage**: Quick add keyword functionality, search suggestions

**Request Body**:
```json
{
  "keyword": "react native developer"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Keyword added successfully",
  "keyword": "react native developer",
  "total_keywords": 4,
  "updated_at": "2025-06-30T12:00:00Z"
}
```

### DELETE `/users/{device_id}/profile/keywords/{keyword}`
**Purpose**: Remove a specific keyword  
**iOS Usage**: Delete keyword from list, keyword management

**Path Parameters**:
- `device_id` (string, required): Device identifier
- `keyword` (string, required): URL-encoded keyword to remove

**Request**:
```http
DELETE /api/v1/users/device_12345abcdef/profile/keywords/ios%20developer
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Keyword removed successfully",
  "removed_keyword": "ios developer",
  "remaining_keywords": 2,
  "updated_at": "2025-06-30T12:00:00Z"
}
```

---

## 🎯 Job Matching

### GET `/users/{device_id}/profile/matches`
**Purpose**: Get personalized job matches for user  
**iOS Usage**: Main job feed, match notifications, job recommendations

**Path Parameters**:
- `device_id` (string, required): Device identifier

**Query Parameters**:
- `limit` (integer, optional): Number of matches to return (default: 20, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `min_score` (float, optional): Minimum match score 0-100 (default: 50)

**Request**:
```http
GET /api/v1/users/device_12345abcdef/profile/matches?limit=10&min_score=70
```

**Response** (200 OK):
```json
{
  "device_id": "device_12345abcdef",
  "matches": [
    {
      "match_id": "uuid-match-id",
      "job_id": 12345,
      "match_score": 89.5,
      "matched_keywords": ["ios developer", "swift"],
      "match_reasons": [
        "Skills match: Swift, iOS development",
        "Location preference: San Francisco",
        "Salary range compatibility"
      ],
      "keyword_relevance": {
        "ios developer": 0.95,
        "swift": 0.87,
        "mobile": 0.73
      },
      "job_details": {
        "title": "Senior iOS Developer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "salary_range": "140000-170000",
        "job_type": "full-time",
        "remote_ok": true,
        "posted_date": "2025-06-29T10:00:00Z",
        "description_snippet": "We're looking for an experienced iOS developer..."
      },
      "is_read": false,
      "is_saved": false,
      "is_applied": false,
      "created_at": "2025-06-30T12:00:00Z"
    }
  ],
  "pagination": {
    "total_matches": 45,
    "current_page": 1,
    "total_pages": 5,
    "has_more": true
  },
  "match_summary": {
    "average_score": 78.3,
    "highest_score": 89.5,
    "total_unread": 12,
    "last_updated": "2025-06-30T11:30:00Z"
  }
}
```

**iOS Implementation**:
```swift
func getJobMatches(deviceId: String, limit: Int = 20, minScore: Double = 50) async throws -> JobMatchesResponse {
    var components = URLComponents(url: baseURL.appendingPathComponent("users/\(deviceId)/profile/matches"), resolvingAgainstBaseURL: true)!
    components.queryItems = [
        URLQueryItem(name: "limit", value: String(limit)),
        URLQueryItem(name: "min_score", value: String(minScore))
    ]
    
    var request = URLRequest(url: components.url!)
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(JobMatchesResponse.self, from: data)
}
```

---

## 🏢 Device Management

### POST `/devices/register`
**Purpose**: Register device for push notifications  
**iOS Usage**: App installation, push notification setup

**Request Body**:
```json
{
  "device_token": "apns_device_token_here",
  "device_type": "iOS",
  "device_info": {
    "model": "iPhone 15 Pro",
    "os_version": "17.0",
    "app_version": "1.2.0",
    "timezone": "America/Los_Angeles"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Device registered successfully",
  "device_id": "uuid-device-id",
  "push_enabled": true,
  "registered_at": "2025-06-30T12:00:00Z"
}
```

### PUT `/devices/update`
**Purpose**: Update device information  
**iOS Usage**: App updates, device info changes

**Request Body**:
```json
{
  "device_token": "existing_device_token",
  "device_info": {
    "model": "iPhone 15 Pro Max",
    "os_version": "17.1",
    "app_version": "1.3.0"
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Device updated successfully",
  "updated_fields": ["device_info"],
  "updated_at": "2025-06-30T12:00:00Z"
}
```

---

## 📊 Analytics & Insights

### GET `/analytics/jobs/overview`
**Purpose**: Get job market overview statistics  
**iOS Usage**: Dashboard, market insights screen

**Response** (200 OK):
```json
{
  "data": {
    "total_jobs": 15678,
    "new_jobs_today": 234,
    "new_jobs_this_week": 1456,
    "top_locations": [
      {"location": "San Francisco", "count": 2345},
      {"location": "New York", "count": 1987},
      {"location": "Remote", "count": 3456}
    ],
    "top_companies": [
      {"company": "Apple", "count": 45},
      {"company": "Google", "count": 38},
      {"company": "Meta", "count": 29}
    ],
    "salary_insights": {
      "average_salary": 145000,
      "median_salary": 135000,
      "salary_range": {"min": 80000, "max": 250000}
    },
    "last_updated": "2025-06-30T12:00:00Z"
  }
}
```

### GET `/analytics/jobs/by-source`
**Purpose**: Job distribution by source platforms  
**iOS Usage**: Source insights, platform analytics

**Response** (200 OK):
```json
{
  "data": {
    "sources": [
      {"source": "LinkedIn", "count": 5678, "percentage": 36.2},
      {"source": "Indeed", "count": 4321, "percentage": 27.6},
      {"source": "Glassdoor", "count": 3456, "percentage": 22.0},
      {"source": "AngelList", "count": 2223, "percentage": 14.2}
    ],
    "total_jobs": 15678,
    "last_updated": "2025-06-30T12:00:00Z"
  }
}
```

### GET `/analytics/jobs/by-company`
**Purpose**: Top hiring companies  
**iOS Usage**: Company insights, trending employers

**Response** (200 OK):
```json
{
  "data": {
    "companies": [
      {
        "company": "Apple",
        "count": 45,
        "avg_salary": 165000,
        "locations": ["Cupertino", "Austin", "Seattle"],
        "job_types": ["full-time", "contract"]
      },
      {
        "company": "Google", 
        "count": 38,
        "avg_salary": 158000,
        "locations": ["Mountain View", "New York", "Remote"],
        "job_types": ["full-time"]
      }
    ],
    "total_companies": 1234,
    "last_updated": "2025-06-30T12:00:00Z"
  }
}
```

### GET `/analytics/jobs/keywords`
**Purpose**: Trending job keywords and skills  
**iOS Usage**: Skill insights, keyword suggestions

**Query Parameters**:
- `limit` (integer, required): Number of keywords (minimum: 10, maximum: 100)

**Request**:
```http
GET /api/v1/analytics/jobs/keywords?limit=20
```

**Response** (200 OK):
```json
{
  "data": {
    "keywords": [
      {
        "keyword": "React",
        "count": 2345,
        "trend": "up",
        "avg_salary": 125000,
        "growth_rate": 15.3
      },
      {
        "keyword": "Swift",
        "count": 1876,
        "trend": "stable", 
        "avg_salary": 135000,
        "growth_rate": 8.7
      },
      {
        "keyword": "Python",
        "count": 3456,
        "trend": "up",
        "avg_salary": 130000,
        "growth_rate": 22.1
      }
    ],
    "total_keywords": 1500,
    "last_updated": "2025-06-30T12:00:00Z"
  }
}
```

---

## 🤖 AI Services

### POST `/ai/analyze-cv`
**Purpose**: Extract skills and experience from CV/resume text  
**iOS Usage**: Resume parsing, skill extraction, profile auto-fill

**Request Body**:
```json
{
  "cv_text": "John Doe\n\nSoftware Engineer with 5 years of experience in iOS development using Swift, Objective-C, and SwiftUI. Expertise in Core Data, UIKit, and REST API integration..."
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "extracted_data": {
    "skills": [
      {"skill": "Swift", "confidence": 0.95},
      {"skill": "iOS Development", "confidence": 0.92},
      {"skill": "SwiftUI", "confidence": 0.88},
      {"skill": "Core Data", "confidence": 0.85},
      {"skill": "UIKit", "confidence": 0.83},
      {"skill": "REST API", "confidence": 0.78}
    ],
    "experience_years": 5,
    "job_titles": ["Software Engineer", "iOS Developer"],
    "technologies": ["Swift", "Objective-C", "SwiftUI", "Core Data"],
    "suggested_keywords": [
      "ios developer",
      "swift engineer", 
      "mobile developer",
      "ios architect"
    ]
  },
  "processing_time_ms": 1234,
  "confidence_score": 0.87
}
```

**iOS Implementation**:
```swift
func analyzeCVText(_ cvText: String) async throws -> CVAnalysisResponse {
    var request = URLRequest(url: baseURL.appendingPathComponent("ai/analyze-cv"))
    request.httpMethod = "POST"
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let requestBody = ["cv_text": cvText]
    request.httpBody = try JSONEncoder().encode(requestBody)
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(CVAnalysisResponse.self, from: data)
}
```

### POST `/ai/recommend-jobs`
**Purpose**: Get AI-powered job recommendations  
**iOS Usage**: Personalized job suggestions, career recommendations

**Request Body**:
```json
{
  "user_skills": ["Swift", "iOS", "SwiftUI", "Core Data"],
  "experience_level": "mid",
  "location_preference": "Remote",
  "salary_expectation": {
    "min": 120000,
    "max": 160000,
    "currency": "USD"
  },
  "job_type_preference": ["full-time", "contract"],
  "limit": 10
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "recommendations": [
    {
      "job_id": 12345,
      "title": "Senior iOS Developer",
      "company": "TechStartup Inc",
      "location": "Remote",
      "salary_range": "130000-155000",
      "match_score": 92.5,
      "match_reasons": [
        "Skills perfectly align with requirements",
        "Salary matches expectations",
        "Remote work available"
      ],
      "required_skills": ["Swift", "iOS", "SwiftUI"],
      "missing_skills": ["Combine"],
      "recommendation_confidence": 0.925
    }
  ],
  "total_recommendations": 45,
  "processing_time_ms": 2100,
  "recommendation_quality": "high"
}
```

---

## ⚠️ Error Handling

### Standard Error Responses

**401 Unauthorized** (Missing/Invalid API Key):
```json
{
  "detail": "Invalid API key"
}
```

**404 Not Found** (Resource doesn't exist):
```json
{
  "detail": "User profile not found for device_id: invalid_device"
}
```

**422 Validation Error** (Invalid request data):
```json
{
  "detail": [
    {
      "loc": ["body", "device_id"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error",
  "error_id": "uuid-error-id",
  "timestamp": "2025-06-30T12:00:00Z"
}
```

---

## 📱 iOS Data Models

### Essential Swift Models

```swift
struct UserProfile: Codable {
    let id: String?
    let deviceId: String
    let firstName: String?
    let lastName: String?
    let email: String?
    let phone: String?
    let location: String?
    let currentJobTitle: String?
    let yearsOfExperience: Int?
    let linkedinProfile: String?
    let portfolioUrl: String?
    let bio: String?
    
    let desiredJobTypes: [String]?
    let remoteWorkPreference: String?
    let skills: [String]?
    let preferredLocations: [String]?
    let matchKeywords: [String]?
    
    let minSalary: Int?
    let maxSalary: Int?
    let salaryCurrency: String?
    let salaryNegotiable: Bool?
    
    let jobMatchesEnabled: Bool?
    let applicationRemindersEnabled: Bool?
    let weeklyDigestEnabled: Bool?
    let marketInsightsEnabled: Bool?
    let quietHoursEnabled: Bool?
    let quietHoursStart: String?
    let quietHoursEnd: String?
    let preferredNotificationTime: String?
    
    let profileVisibility: String?
    let shareAnalytics: Bool?
    let shareJobViewHistory: Bool?
    let allowPersonalizedRecommendations: Bool?
    
    let profileCompleteness: Int?
    let isActive: Bool?
    let createdAt: String?
    let updatedAt: String?
    
    enum CodingKeys: String, CodingKey {
        case id, email, phone, location, bio, skills
        case deviceId = "device_id"
        case firstName = "first_name"
        case lastName = "last_name"
        case currentJobTitle = "current_job_title"
        case yearsOfExperience = "years_of_experience"
        case linkedinProfile = "linkedin_profile"
        case portfolioUrl = "portfolio_url"
        case desiredJobTypes = "desired_job_types"
        case remoteWorkPreference = "remote_work_preference"
        case preferredLocations = "preferred_locations"
        case matchKeywords = "match_keywords"
        case minSalary = "min_salary"
        case maxSalary = "max_salary"
        case salaryCurrency = "salary_currency"
        case salaryNegotiable = "salary_negotiable"
        case jobMatchesEnabled = "job_matches_enabled"
        case applicationRemindersEnabled = "application_reminders_enabled"
        case weeklyDigestEnabled = "weekly_digest_enabled"
        case marketInsightsEnabled = "market_insights_enabled"
        case quietHoursEnabled = "quiet_hours_enabled"
        case quietHoursStart = "quiet_hours_start"
        case quietHoursEnd = "quiet_hours_end"
        case preferredNotificationTime = "preferred_notification_time"
        case profileVisibility = "profile_visibility"
        case shareAnalytics = "share_analytics"
        case shareJobViewHistory = "share_job_view_history"
        case allowPersonalizedRecommendations = "allow_personalized_recommendations"
        case profileCompleteness = "profile_completeness"
        case isActive = "is_active"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct JobMatch: Codable {
    let matchId: String
    let jobId: Int
    let matchScore: Double
    let matchedKeywords: [String]
    let matchReasons: [String]
    let keywordRelevance: [String: Double]
    let jobDetails: JobDetails
    let isRead: Bool
    let isSaved: Bool
    let isApplied: Bool
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case matchId = "match_id"
        case jobId = "job_id"
        case matchScore = "match_score"
        case matchedKeywords = "matched_keywords"
        case matchReasons = "match_reasons"
        case keywordRelevance = "keyword_relevance"
        case jobDetails = "job_details"
        case isRead = "is_read"
        case isSaved = "is_saved"
        case isApplied = "is_applied"
        case createdAt = "created_at"
    }
}

struct JobDetails: Codable {
    let title: String
    let company: String
    let location: String
    let salaryRange: String
    let jobType: String
    let remoteOk: Bool
    let postedDate: String
    let descriptionSnippet: String
    
    enum CodingKeys: String, CodingKey {
        case title, company, location
        case salaryRange = "salary_range"
        case jobType = "job_type"
        case remoteOk = "remote_ok"
        case postedDate = "posted_date"
        case descriptionSnippet = "description_snippet"
    }
}

struct AnalyticsOverview: Codable {
    let data: AnalyticsData
}

struct AnalyticsData: Codable {
    let totalJobs: Int
    let newJobsToday: Int
    let newJobsThisWeek: Int
    let topLocations: [LocationStat]
    let topCompanies: [CompanyStat]
    let salaryInsights: SalaryInsights
    let lastUpdated: String
    
    enum CodingKeys: String, CodingKey {
        case totalJobs = "total_jobs"
        case newJobsToday = "new_jobs_today"
        case newJobsThisWeek = "new_jobs_this_week"
        case topLocations = "top_locations"
        case topCompanies = "top_companies"
        case salaryInsights = "salary_insights"
        case lastUpdated = "last_updated"
    }
}
```

---

## 🔄 API Client Implementation

### Complete iOS API Client

```swift
class BirjobAPIClient: ObservableObject {
    private let baseURL = URL(string: "https://birjobbackend-ir3e.onrender.com/api/v1")!
    private let apiKey = "birjob-ios-api-key-2024"
    
    private var session: URLSession {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        return URLSession(configuration: config)
    }
    
    // MARK: - Health Check
    func checkHealth() async throws -> HealthResponse {
        let request = createRequest(endpoint: "health", method: "GET")
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }
    
    // MARK: - User Profile Management
    func createOrUpdateProfile(_ profile: UserProfile) async throws -> ProfileResponse {
        let request = createRequest(endpoint: "users/profile", method: "POST", body: profile)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(ProfileResponse.self, from: data)
    }
    
    func getUserProfile(deviceId: String) async throws -> UserProfile {
        let request = createRequest(endpoint: "users/profile/\(deviceId)", method: "GET")
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(UserProfile.self, from: data)
    }
    
    // MARK: - Job Matching
    func getJobMatches(deviceId: String, limit: Int = 20, minScore: Double = 50) async throws -> JobMatchesResponse {
        var components = URLComponents(url: baseURL.appendingPathComponent("users/\(deviceId)/profile/matches"), resolvingAgainstBaseURL: true)!
        components.queryItems = [
            URLQueryItem(name: "limit", value: String(limit)),
            URLQueryItem(name: "min_score", value: String(minScore))
        ]
        
        let request = createRequest(url: components.url!, method: "GET")
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(JobMatchesResponse.self, from: data)
    }
    
    // MARK: - Analytics
    func getAnalyticsOverview() async throws -> AnalyticsOverview {
        let request = createRequest(endpoint: "analytics/jobs/overview", method: "GET")
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(AnalyticsOverview.self, from: data)
    }
    
    // MARK: - Keywords Management
    func getUserKeywords(deviceId: String) async throws -> KeywordsResponse {
        let request = createRequest(endpoint: "users/\(deviceId)/profile/keywords", method: "GET")
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(KeywordsResponse.self, from: data)
    }
    
    func updateKeywords(deviceId: String, keywords: KeywordUpdateRequest) async throws -> SuccessResponse {
        let request = createRequest(endpoint: "users/\(deviceId)/profile/keywords", method: "POST", body: keywords)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(SuccessResponse.self, from: data)
    }
    
    // MARK: - AI Services
    func analyzeCVText(_ cvText: String) async throws -> CVAnalysisResponse {
        let requestBody = ["cv_text": cvText]
        let request = createRequest(endpoint: "ai/analyze-cv", method: "POST", body: requestBody)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(CVAnalysisResponse.self, from: data)
    }
    
    // MARK: - Helper Methods
    private func createRequest<T: Encodable>(endpoint: String, method: String, body: T? = nil) -> URLRequest {
        let url = baseURL.appendingPathComponent(endpoint)
        return createRequest(url: url, method: method, body: body)
    }
    
    private func createRequest<T: Encodable>(url: URL, method: String, body: T? = nil) -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            do {
                request.httpBody = try JSONEncoder().encode(body)
            } catch {
                print("Failed to encode request body: \(error)")
            }
        }
        
        return request
    }
}
```

---

## 🚀 Integration Checklist

### iOS App Update Tasks

1. **✅ Update Base URL**: Change to `https://birjobbackend-ir3e.onrender.com/api/v1`
2. **✅ Add API Key**: Include `X-API-Key: birjob-ios-api-key-2024` in all requests
3. **✅ Update User Profile Model**: Use new `UserProfile` structure with device_id
4. **✅ Update Endpoints**: Change to `/users/profile/*` pattern
5. **✅ Update Keywords Management**: Use new keywords API endpoints
6. **✅ Update Job Matching**: Use `/users/{device_id}/profile/matches`
7. **✅ Update Analytics**: Use new analytics endpoints structure
8. **✅ Add Error Handling**: Handle 401, 404, 422, 500 status codes
9. **✅ Test Device Flow**: Verify profile creation and retrieval
10. **✅ Test Matching Flow**: Verify job matches and scoring

### Backward Compatibility

- ✅ **No breaking changes**: All existing data preserved
- ✅ **Same functionality**: All features working as before
- ✅ **Enhanced performance**: New RDBMS design improves speed
- ✅ **New capabilities**: Better analytics and matching accuracy

This documentation provides everything needed for updating your iOS app to work with the optimized backend infrastructure.