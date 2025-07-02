# iOS Job App Backend - Complete API Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Authentication Strategy](#authentication-strategy)
6. [Push Notifications](#push-notifications)
7. [Deployment & Environment](#deployment--environment)
8. [Error Handling](#error-handling)
9. [iOS Integration Guide](#ios-integration-guide)
10. [Testing Instructions](#testing-instructions)

---

## System Overview

This is a **simplified, email-based backend system** for an iOS job matching application. The system is designed around **trust-based authentication** with no traditional usernames/passwords, focusing on email-based user management and device identification.

### Key Design Principles
- **Email-first approach**: Users identified primarily by email addresses
- **Device-centric**: Each device gets a unique identifier for push notifications
- **Auto-registration**: Users are created automatically on first interaction
- **Trust-based security**: No complex authentication - suitable for consumer job apps
- **Minimal schema**: Only 4 essential database tables

### Core Functionality
1. **User Management**: Email-based user creation and keyword management
2. **Device Registration**: iOS device token management for push notifications
3. **Job Operations**: Job saving, viewing, and basic analytics
4. **Health Monitoring**: System health checks and status reporting

---

## Architecture

### Technology Stack
- **Framework**: FastAPI (Python async web framework)
- **Database**: PostgreSQL with asyncpg driver
- **Caching**: Redis for performance optimization
- **Push Notifications**: Apple Push Notification Service (APNS)
- **Deployment**: Render.com with containerized deployment

### Application Structure
```
birjobBackend/
├── application.py              # Main FastAPI application entry point
├── requirements.txt            # Python dependencies
├── render.yaml                # Render.com deployment configuration
├── recreate_minimal_tables.sql # Database schema recreation script
└── app/
    ├── api/v1/
    │   ├── router.py          # Main API router
    │   └── endpoints/
    │       ├── users.py       # User management endpoints
    │       ├── devices.py     # Device registration endpoints
    │       ├── jobs.py        # Job-related endpoints
    │       ├── analytics.py   # Basic analytics endpoints
    │       └── health.py      # Health check endpoints
    ├── core/
    │   ├── config.py          # Application configuration
    │   ├── database.py        # Database connection and initialization
    │   └── redis_client.py    # Redis connection management
    ├── models/
    │   ├── user.py           # User database model
    │   └── device.py         # Device token database model
    ├── schemas/
    │   ├── user.py           # User request/response schemas
    │   └── device.py         # Device request/response schemas
    └── services/
        └── push_notifications.py # APNS integration service
```

---

## Database Schema

The system uses **4 essential tables** in the `iosapp` PostgreSQL schema:

### 1. users
Primary user management table supporting email-based identification.

```sql
CREATE TABLE iosapp.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,           -- Unique device identifier
    email VARCHAR(255),                               -- User email (optional)
    keywords JSONB DEFAULT '[]'::jsonb,              -- Job search keywords array
    preferred_sources JSONB DEFAULT '[]'::jsonb,     -- Preferred job sources array
    notifications_enabled BOOLEAN DEFAULT TRUE,       -- Push notification preference
    last_notified_at TIMESTAMP WITH TIME ZONE,       -- Last notification timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_users_device_id` on `device_id`
- `idx_users_email` on `email`

### 2. device_tokens
Device registration for push notifications.

```sql
CREATE TABLE iosapp.device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(255) UNIQUE NOT NULL,           -- Device identifier (links to users)
    device_token VARCHAR(500) NOT NULL,               -- APNS device token
    device_info JSONB DEFAULT '{}'::jsonb,           -- Device metadata (OS, app version)
    user_id UUID,                                     -- Reference to users.id (optional)
    is_active BOOLEAN DEFAULT TRUE,                   -- Token validity status
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes:**
- `idx_device_tokens_device_id` on `device_id`
- `idx_device_tokens_user_id` on `user_id`

### 3. saved_jobs
User's saved/bookmarked jobs.

```sql
CREATE TABLE iosapp.saved_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- Reference to users.id
    job_id INTEGER NOT NULL,                         -- External job system ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, job_id)                         -- Prevent duplicate saves
);
```

### 4. job_views
Basic analytics for job viewing behavior.

```sql
CREATE TABLE iosapp.job_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,                           -- Reference to users.id
    job_id INTEGER NOT NULL,                         -- External job system ID
    viewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/` and return JSON responses.

### User Management Endpoints

#### GET /api/v1/users/by-email
**Purpose**: Retrieve or auto-create user by email address
**Use Case**: Website integration, user lookup, auto-registration

**Parameters:**
- `email` (query parameter, required): Valid email address

**Request:**
```bash
GET /api/v1/users/by-email?email=user@example.com
```

**Response (User Created):**
```json
{
  "success": true,
  "message": "User created",
  "data": {
    "id": "cb4089a3-f871-47dc-a4df-88879b8f3490",
    "email": "user@example.com",
    "keywords": [],
    "preferred_sources": [],
    "notifications_enabled": true,
    "created_at": "2025-07-02T14:35:36.940871+00:00"
  }
}
```

**Response (Existing User):**
```json
{
  "success": true,
  "message": "User found",
  "data": {
    "id": "cb4089a3-f871-47dc-a4df-88879b8f3490",
    "email": "user@example.com",
    "keywords": ["react", "javascript"],
    "preferred_sources": ["linkedin", "indeed"],
    "notifications_enabled": true,
    "created_at": "2025-07-02T14:35:36.940871+00:00"
  }
}
```

#### POST /api/v1/users/keywords/add
**Purpose**: Add job search keyword for email-based user
**Use Case**: Website keyword subscription, preference management

**Request Body:**
```json
{
  "email": "user@example.com",
  "keyword": "python developer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Keyword added successfully"
}
```

#### DELETE /api/v1/users/keywords/remove
**Purpose**: Remove job search keyword for email-based user

**Request Body:**
```json
{
  "email": "user@example.com",
  "keyword": "python developer"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Keyword removed successfully"
}
```

#### GET /api/v1/users/profile/{device_id}
**Purpose**: Get user profile by device ID
**Use Case**: iOS app profile retrieval

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "cb4089a3-f871-47dc-a4df-88879b8f3490",
    "device_id": "ABC123DEF456",
    "email": "user@example.com",
    "keywords": ["react", "javascript"],
    "preferred_sources": ["linkedin"],
    "notifications_enabled": true,
    "created_at": "2025-07-02T14:35:36.940871+00:00"
  }
}
```

#### POST /api/v1/users/profile
**Purpose**: Create or update user profile via device ID
**Use Case**: iOS app user registration, profile updates

**Request Body:**
```json
{
  "device_id": "ABC123DEF456",
  "email": "user@example.com",
  "keywords": ["react", "node.js"],
  "preferred_sources": ["linkedin", "indeed"],
  "notifications_enabled": true
}
```

#### GET /api/v1/users/profile/exists/{device_id}
**Purpose**: Check if user profile exists for device
**Use Case**: iOS app profile recovery logic

**Response (Exists):**
```json
{
  "success": true,
  "data": {"exists": true}
}
```

**Response (Not Found):**
```json
{
  "success": true,
  "data": {"exists": false}
}
```

### Device Management Endpoints

#### POST /api/v1/devices/register
**Purpose**: Register iOS device for push notifications
**Use Case**: iOS app startup, device token registration

**Request Body:**
```json
{
  "device_token": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456",
  "device_info": {
    "osVersion": "17.0",
    "appVersion": "1.0.0",
    "deviceModel": "iPhone14,2",
    "timezone": "America/New_York"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "device_id": "ABC123DEF456",
    "registered_at": "2025-07-02T14:35:36.940871+00:00"
  }
}
```

### Job Management Endpoints

#### POST /api/v1/jobs/save
**Purpose**: Save/bookmark a job for user
**Use Case**: iOS app job bookmarking

**Request Body:**
```json
{
  "device_id": "ABC123DEF456",
  "job_id": 12345
}
```

#### DELETE /api/v1/jobs/unsave
**Purpose**: Remove saved job bookmark

**Request Body:**
```json
{
  "device_id": "ABC123DEF456",
  "job_id": 12345
}
```

#### GET /api/v1/jobs/saved/{device_id}
**Purpose**: Get all saved jobs for user
**Use Case**: iOS app saved jobs list

**Response:**
```json
{
  "success": true,
  "data": {
    "saved_jobs": [
      {"job_id": 12345, "saved_at": "2025-07-02T14:35:36.940871+00:00"},
      {"job_id": 67890, "saved_at": "2025-07-02T14:30:15.123456+00:00"}
    ]
  }
}
```

#### POST /api/v1/jobs/view
**Purpose**: Record job view for analytics
**Use Case**: iOS app job detail view tracking

**Request Body:**
```json
{
  "device_id": "ABC123DEF456",
  "job_id": 12345
}
```

### Analytics Endpoints

#### GET /api/v1/analytics/user/{device_id}
**Purpose**: Get user-specific analytics
**Use Case**: iOS app usage statistics

**Response:**
```json
{
  "success": true,
  "data": {
    "total_saved_jobs": 5,
    "total_job_views": 42,
    "keywords_count": 3,
    "account_age_days": 15
  }
}
```

### Health Check Endpoint

#### GET /api/v1/health
**Purpose**: System health monitoring
**Use Case**: Deployment monitoring, service status

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-02T14:35:29.591723+00:00",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "apns": "healthy",
    "scraper": "healthy"
  },
  "metrics": {
    "active_devices": 150,
    "active_subscriptions": 89,
    "matches_last_24h": 1247,
    "notifications_sent_last_24h": 256
  }
}
```

### Root Endpoints

#### GET /
**Purpose**: API root information

**Response:**
```json
{
  "message": "iOS Native App Backend API",
  "version": "1.0.0"
}
```

---

## Authentication Strategy

### Trust-Based Authentication Model
This system implements a **trust-based authentication** approach suitable for consumer job applications:

1. **No Passwords**: Users never create passwords or traditional accounts
2. **Device-Centric**: Each iOS device gets a unique `device_id`
3. **Email Optional**: Email addresses are used for web integration but not required
4. **Auto-Registration**: Users created automatically on first interaction

### Device Identification Flow
```
iOS App Startup
    ↓
Generate/Retrieve Local Device ID
    ↓
Register Device Token with Backend (/devices/register)
    ↓
Backend Returns device_id
    ↓
Use device_id for All Subsequent API Calls
```

### Security Considerations
- **Suitable for**: Consumer job apps, non-sensitive user data
- **Not suitable for**: Financial apps, medical apps, enterprise systems
- **Device loss**: User loses access if device is lost (by design)
- **Privacy**: Users can use app without providing email

---

## Push Notifications

### APNS Integration
The system integrates with Apple Push Notification Service for job match notifications.

#### Device Token Registration
1. iOS app generates APNS device token
2. App calls `/devices/register` with token and device info
3. Backend stores token for future notifications

#### Device Token Format
- **Length**: Exactly 64 characters (hex string)
- **Format**: Lowercase hexadecimal
- **Example**: `a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456`

#### Notification Scenarios
- New job matches based on user keywords
- System maintenance notifications
- Feature update announcements

#### Development Note
In development environment, APNS service is mocked to prevent errors.

---

## Deployment & Environment

### Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database?sslmode=require

# Redis Configuration  
REDIS_URL=redis://localhost:6379

# APNS Configuration (Production)
APNS_KEY_ID=your_key_id
APNS_TEAM_ID=your_team_id
APNS_BUNDLE_ID=com.yourcompany.yourapp
APNS_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...

# Application Settings
ALLOWED_ORIGINS=["*"]  # Configure for production
ENVIRONMENT=production
```

### Render.com Deployment
The application is configured for Render.com deployment with:

```yaml
# render.yaml
services:
  - type: web
    name: ios-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python application.py
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: ios-backend-db
          property: connectionString
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://..."
export REDIS_URL="redis://localhost:6379"

# Run application
python application.py
```

### Database Setup
```bash
# Create minimal tables
psql $DATABASE_URL -f recreate_minimal_tables.sql
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "detail": "Error description",
  "status_code": 400
}
```

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid input)
- **404**: Not Found (user/resource doesn't exist)
- **422**: Validation Error (invalid data format)
- **500**: Internal Server Error

### Device ID Validation
- Device IDs must be valid UUID format
- Invalid device IDs return 400 Bad Request

### Email Validation
- Email addresses validated using Pydantic EmailStr
- Invalid emails return 422 Validation Error

---

## iOS Integration Guide

### Required iOS Dependencies
```swift
// For HTTP requests
import Foundation

// For push notifications
import UserNotifications
```

### 1. Device Registration on App Launch
```swift
// Generate or retrieve stored device ID
let deviceId = UserDefaults.standard.string(forKey: "device_id") ?? UUID().uuidString
UserDefaults.standard.set(deviceId, forKey: "device_id")

// Register for push notifications
UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
    if granted {
        DispatchQueue.main.async {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
}

// When device token received
func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
    registerDeviceWithBackend(deviceToken: tokenString)
}
```

### 2. User Profile Management
```swift
struct UserProfile {
    let deviceId: String
    let email: String?
    let keywords: [String]
    let preferredSources: [String]
    let notificationsEnabled: Bool
}

// Check if profile exists
func checkProfileExists(deviceId: String) async {
    let url = URL(string: "\(baseURL)/api/v1/users/profile/exists/\(deviceId)")!
    // Make GET request
}

// Create/Update profile
func saveProfile(_ profile: UserProfile) async {
    let url = URL(string: "\(baseURL)/api/v1/users/profile")!
    // Make POST request with profile data
}
```

### 3. Job Management
```swift
// Save job
func saveJob(jobId: Int, deviceId: String) async {
    let url = URL(string: "\(baseURL)/api/v1/jobs/save")!
    let body = ["device_id": deviceId, "job_id": jobId]
    // Make POST request
}

// Get saved jobs
func getSavedJobs(deviceId: String) async -> [SavedJob] {
    let url = URL(string: "\(baseURL)/api/v1/jobs/saved/\(deviceId)")!
    // Make GET request and parse response
}
```

### 4. Network Layer Example
```swift
class APIClient {
    private let baseURL = "https://your-backend-url.com"
    
    func makeRequest<T: Codable>(
        endpoint: String,
        method: HTTPMethod,
        body: [String: Any]? = nil,
        responseType: T.Type
    ) async throws -> T {
        
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              200...299 ~= httpResponse.statusCode else {
            throw APIError.serverError
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
}
```

### 5. Profile Recovery Strategy
Since this is a trust-based system without traditional authentication:

```swift
// On app launch, check if profile exists for device
func handleAppLaunch() async {
    let deviceId = getOrCreateDeviceId()
    
    let profileExists = await checkProfileExists(deviceId: deviceId)
    
    if profileExists {
        // Load existing profile
        await loadUserProfile(deviceId: deviceId)
    } else {
        // Show onboarding/profile creation
        showOnboarding()
    }
}
```

---

## Testing Instructions

### 1. Local Testing Setup
```bash
# Start the application
python application.py

# Test root endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/api/v1/health
```

### 2. User Management Testing
```bash
# Create user by email
curl "http://localhost:8000/api/v1/users/by-email?email=test@example.com"

# Add keyword
curl -X POST http://localhost:8000/api/v1/users/keywords/add \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "keyword": "python developer"}'

# Check profile exists
curl http://localhost:8000/api/v1/users/profile/exists/TEST_DEVICE_123
```

### 3. Device Registration Testing
```bash
# Register device
curl -X POST http://localhost:8000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234567890123456",
    "device_info": {
      "osVersion": "17.0",
      "appVersion": "1.0.0", 
      "deviceModel": "iPhone14,2",
      "timezone": "America/New_York"
    }
  }'
```

### 4. Job Operations Testing
```bash
# Save job
curl -X POST http://localhost:8000/api/v1/jobs/save \
  -H "Content-Type: application/json" \
  -d '{"device_id": "TEST_DEVICE_123", "job_id": 12345}'

# Get saved jobs
curl http://localhost:8000/api/v1/jobs/saved/TEST_DEVICE_123
```

### 5. Production Testing
Replace `localhost:8000` with your production URL:
- `https://your-backend-url.onrender.com`

### 6. Database Verification
```sql
-- Check created users
SELECT * FROM iosapp.users LIMIT 5;

-- Check device registrations  
SELECT * FROM iosapp.device_tokens LIMIT 5;

-- Check saved jobs
SELECT * FROM iosapp.saved_jobs LIMIT 5;
```

---

## Important Notes for iOS Development

### Data Persistence Strategy
- **Device ID**: Store in UserDefaults, generate UUID on first launch
- **Profile Data**: Cache locally, sync with backend periodically
- **Offline Support**: Store critical data locally, sync when online

### Error Handling Best Practices
- Always handle network errors gracefully
- Implement retry logic for failed requests
- Show user-friendly error messages
- Log errors for debugging but don't expose sensitive info

### Performance Considerations
- Cache profile data locally to reduce API calls
- Use background queues for network requests
- Implement request throttling to avoid overwhelming backend

### Privacy Compliance
- Request notification permissions appropriately
- Handle email collection with proper privacy notices
- Allow users to opt out of notifications
- Implement data deletion if required

### Testing Recommendations
- Test app behavior with poor network conditions
- Test profile recovery after app reinstall
- Test notification permissions flow
- Test with various iOS versions and device types

---

This documentation provides everything needed to integrate with the backend system. The API is designed to be simple, reliable, and suitable for a consumer job application with trust-based authentication.