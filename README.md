# 🚀 iOS Job App Backend - Complete Developer Guide

> **AI-Friendly Documentation**: This README provides comprehensive information for AI models to understand, build, and update the iOS job application backend and mobile app.

## 📋 Project Overview

A production-ready FastAPI backend for an iOS job search application with real-time job matching, AI-powered career assistance, and push notifications. Currently serving **4,367+ live jobs** from 39 sources with full APNs integration.

**🌐 Live Production API**: `https://birjobbackend-ir3e.onrender.com`

## 🎯 Core Features

### Backend Capabilities
- ✅ **Real-time Job Matching**: Automated keyword-based job notifications
- ✅ **Push Notifications**: Full APNs integration with production support
- ✅ **AI Career Assistant**: Gemini 2.5 Flash powered chatbot
- ✅ **User Management**: Device-based and email-based user systems
- ✅ **Job Management**: Save, search, view tracking with analytics
- ✅ **RDBMS Design**: Proper PostgreSQL schema with foreign keys

### Production Stats
- **Active Jobs**: 4,367+ (updated every 2 hours)
- **Job Sources**: 39 different platforms
- **Response Time**: <200ms average
- **Uptime**: 99.9% availability
- **Push Notifications**: ✅ Working (APNs key: 834XDMQ3QB)

## 🏗️ Architecture & Database Schema

### Core Database Tables

#### 1. Users (`iosapp.users`)
```sql
id                   UUID PRIMARY KEY
email                VARCHAR(255) UNIQUE
keywords             JSONB DEFAULT []        -- User's job search keywords
preferred_sources    JSONB DEFAULT []        -- Preferred job sources
notifications_enabled BOOLEAN DEFAULT true
last_notified_at     TIMESTAMP
created_at           TIMESTAMP DEFAULT NOW()
updated_at           TIMESTAMP DEFAULT NOW()
```

#### 2. Device Tokens (`iosapp.device_tokens`)
```sql
id              UUID PRIMARY KEY
user_id         UUID REFERENCES users(id) CASCADE
device_id       VARCHAR(255) UNIQUE        -- Device identifier
device_token    VARCHAR(500)               -- APNs push token
device_info     JSONB                      -- Device metadata
is_active       BOOLEAN DEFAULT true
registered_at   TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

#### 3. Saved Jobs (`iosapp.saved_jobs`)
```sql
id           UUID PRIMARY KEY
user_id      UUID REFERENCES users(id) CASCADE
job_id       INTEGER                     -- Reference to scraper.jobs_jobpost
job_title    VARCHAR(500)               -- Cached for performance
job_company  VARCHAR(255)               -- Cached for performance
job_source   VARCHAR(100)               -- Cached for performance
created_at   TIMESTAMP DEFAULT NOW()
```

#### 4. Job Views (`iosapp.job_views`)
```sql
id                    UUID PRIMARY KEY
user_id               UUID REFERENCES users(id) CASCADE
job_id                INTEGER                  -- Reference to scraper.jobs_jobpost
job_title             VARCHAR(500)            -- Analytics cache
job_company           VARCHAR(255)            -- Analytics cache
job_source            VARCHAR(100)            -- Analytics cache
view_duration_seconds INTEGER DEFAULT 0
viewed_at             TIMESTAMP DEFAULT NOW()
```

#### 5. Push Notifications (`iosapp.push_notifications`)
```sql
id                   UUID PRIMARY KEY
device_id            VARCHAR(255)
user_id              UUID REFERENCES users(id)
job_notification_id  UUID                     -- Reference to notification
notification_type    VARCHAR(50)
payload              JSONB
status               VARCHAR(20)              -- pending/sent/failed
apns_response        JSONB
sent_at              TIMESTAMP
created_at           TIMESTAMP DEFAULT NOW()
```

### External Job Data (`scraper.jobs_jobpost`)
```sql
id          INTEGER PRIMARY KEY
title       TEXT
company     VARCHAR(255)
location    TEXT
description TEXT
apply_link  TEXT
source      VARCHAR(100)
created_at  TIMESTAMP
```

## 📡 Complete API Reference

### 🏥 Health & System
```http
GET /                           # Root endpoint info
GET /health                     # Simple health check
GET /api/v1/health             # Detailed health status
```

### 👤 User Management
```http
POST /api/v1/users/register                    # Register user with device
GET  /api/v1/users/profile/{device_id}         # Get user profile
PUT  /api/v1/users/profile                     # Update user profile
PUT  /api/v1/users/{device_id}                 # Update user by device ID

# Email-based (for web interface)
GET    /api/v1/users/by-email?email={email}    # Get/create user by email
POST   /api/v1/users/keywords/email            # Add keyword by email
DELETE /api/v1/users/keywords/email            # Remove keyword by email
```

### 💼 Job Management
```http
GET    /api/v1/jobs/                           # Search jobs with filters
GET    /api/v1/jobs/{job_id}                   # Get specific job details
GET    /api/v1/jobs/stats/summary              # Job database statistics
POST   /api/v1/jobs/save                       # Save job for user
DELETE /api/v1/jobs/unsave                     # Remove saved job
GET    /api/v1/jobs/saved/{device_id}          # Get user's saved jobs
POST   /api/v1/jobs/view                       # Record job view for analytics
```

### 📱 Device & Push Notifications
```http
POST   /api/v1/devices/register                # Register device for push notifications
POST   /api/v1/devices/token                   # Update device token
DELETE /api/v1/devices/{device_id}             # Unregister device
GET    /api/v1/devices/{device_id}/status      # Get device status
GET    /api/v1/notifications/inbox/{device_id} # Get notification history
```

### 🤖 AI Chatbot (Gemini 2.5 Flash)
```http
POST /api/v1/chatbot/chat                      # Chat with AI assistant
POST /api/v1/chatbot/recommendations           # Get AI job recommendations
POST /api/v1/chatbot/analyze-job               # AI job analysis
GET  /api/v1/chatbot/stats                     # Chatbot usage statistics
```

### 📊 Analytics
```http
POST   /api/v1/analytics/event                 # Record user analytics event
GET    /api/v1/analytics/user/{device_id}      # Get user analytics
GET    /api/v1/analytics/stats                 # Overall analytics
DELETE /api/v1/analytics/user/{device_id}      # GDPR: Clear user data
```

## 🔔 Push Notification System

### APNs Configuration (Production Ready)
```bash
APNS_KEY_ID=834XDMQ3QB              # Active APNs key
APNS_TEAM_ID=KK5HUUQ3HR             # Apple Developer Team
APNS_BUNDLE_ID=com.ismats.birjob    # iOS app bundle ID
APNS_SANDBOX=false                  # Production mode
```

### Notification Flow
1. **Job Scraper** runs every 5 minutes
2. **Keyword Matching** against user preferences
3. **Push Notification** sent via APNs
4. **Notification History** stored in database

### Notification Types
```json
// Job Match Notification
{
  "aps": {
    "alert": {
      "title": "New Job Match! 🎯",
      "subtitle": "Senior iOS Developer at Apple",
      "body": "Matches your keywords: iOS, Swift, Mobile"
    },
    "badge": 1,
    "sound": "default",
    "category": "JOB_MATCH"
  },
  "custom_data": {
    "type": "job_match",
    "job_id": "12345",
    "matched_keywords": ["iOS", "Swift"],
    "deep_link": "birjob://job/12345"
  }
}
```

## 🛠️ Environment Configuration

### Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# Redis (Optional)
REDIS_URL=redis://host:port/db
UPSTASH_REDIS_REST_URL=https://redis-rest-url
UPSTASH_REDIS_REST_TOKEN=redis-token

# Security
SECRET_KEY=your-secret-key

# APNs Push Notifications
APNS_KEY_ID=834XDMQ3QB
APNS_TEAM_ID=KK5HUUQ3HR
APNS_BUNDLE_ID=com.ismats.birjob
APNS_SANDBOX=false
APNS_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"

# AI Integration
GEMINI_API_KEY=your-gemini-api-key

# App Configuration
LOG_LEVEL=INFO
MATCH_ENGINE_INTERVAL_MINUTES=5
MAX_NOTIFICATIONS_PER_HOUR=5
MAX_NOTIFICATIONS_PER_DAY=20
```

## 📱 iOS App Integration Guide

### 1. Project Setup (Xcode)
```swift
// Required Capabilities
- Push Notifications
- Background App Refresh
- Background Modes: remote-notification

// Bundle Configuration
Bundle Identifier: com.ismats.birjob
Team: Your Apple Developer Team
```

### 2. Core iOS Implementation

#### App Delegate Setup
```swift
import UserNotifications
import UIKit

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    
    func application(_ application: UIApplication, 
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        
        // Configure push notifications
        UNUserNotificationCenter.current().delegate = self
        application.registerForRemoteNotifications()
        
        return true
    }
    
    // Handle device token registration
    func application(_ application: UIApplication, 
                    didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        // Send to backend
        Task {
            await registerDeviceToken(tokenString)
        }
    }
    
    // Handle push notifications
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                              willPresent notification: UNNotification,
                              withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.alert, .badge, .sound])
    }
    
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                              didReceive response: UNNotificationResponse,
                              withCompletionHandler completionHandler: @escaping () -> Void) {
        // Handle notification tap
        handleNotificationResponse(response)
        completionHandler()
    }
}
```

#### API Service Layer
```swift
import Foundation

class APIService {
    static let shared = APIService()
    private let baseURL = "https://birjobbackend-ir3e.onrender.com/api/v1"
    
    // Device Registration
    func registerDevice(deviceToken: String, deviceInfo: [String: Any]) async throws {
        let url = URL(string: "\(baseURL)/devices/register")!
        let payload = [
            "device_token": deviceToken,
            "device_info": deviceInfo
        ]
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        // Handle response
    }
    
    // Search Jobs
    func searchJobs(query: String? = nil, 
                   source: String? = nil,
                   limit: Int = 20,
                   offset: Int = 0) async throws -> JobSearchResponse {
        
        var components = URLComponents(string: "\(baseURL)/jobs/")!
        components.queryItems = [
            URLQueryItem(name: "limit", value: String(limit)),
            URLQueryItem(name: "offset", value: String(offset))
        ]
        
        if let query = query { components.queryItems?.append(URLQueryItem(name: "search", value: query)) }
        if let source = source { components.queryItems?.append(URLQueryItem(name: "source", value: source)) }
        
        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode(JobSearchResponse.self, from: data)
    }
    
    // Update User Keywords
    func updateUserKeywords(deviceId: String, keywords: [String]) async throws {
        let url = URL(string: "\(baseURL)/users/\(deviceId)")!
        let payload = ["keywords": keywords]
        
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        
        let (_, _) = try await URLSession.shared.data(for: request)
    }
}
```

#### Data Models
```swift
struct Job: Codable, Identifiable {
    let id: Int
    let title: String
    let company: String
    let location: String?
    let description: String?
    let applyLink: String
    let source: String
    let createdAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, title, company, location, description, source
        case applyLink = "apply_link"
        case createdAt = "created_at"
    }
}

struct JobSearchResponse: Codable {
    let success: Bool
    let data: JobSearchData
}

struct JobSearchData: Codable {
    let jobs: [Job]
    let totalCount: Int
    let pagination: Pagination
    
    enum CodingKeys: String, CodingKey {
        case jobs
        case totalCount = "total_count"
        case pagination
    }
}

struct User: Codable {
    let id: String
    var keywords: [String]
    var notificationsEnabled: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, keywords
        case notificationsEnabled = "notifications_enabled"
    }
}
```

### 3. SwiftUI Views

#### Main Job Search View
```swift
import SwiftUI

struct JobSearchView: View {
    @State private var jobs: [Job] = []
    @State private var searchText = ""
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            VStack {
                SearchBar(text: $searchText, onSearchButtonClicked: performSearch)
                
                if isLoading {
                    ProgressView("Searching jobs...")
                } else {
                    List(jobs) { job in
                        JobRowView(job: job)
                            .onTapGesture {
                                // Navigate to job detail
                            }
                    }
                }
            }
            .navigationTitle("Job Search")
            .onAppear {
                loadJobs()
            }
        }
    }
    
    private func loadJobs() {
        isLoading = true
        Task {
            do {
                let response = try await APIService.shared.searchJobs()
                DispatchQueue.main.async {
                    self.jobs = response.data.jobs
                    self.isLoading = false
                }
            } catch {
                print("Error loading jobs: \(error)")
                self.isLoading = false
            }
        }
    }
    
    private func performSearch() {
        loadJobs()
    }
}

struct JobRowView: View {
    let job: Job
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(job.title)
                .font(.headline)
                .lineLimit(2)
            
            Text(job.company)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            if let location = job.location {
                Text(location)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            HStack {
                Text(job.source)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(4)
                
                Spacer()
                
                Text(formatDate(job.createdAt))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
    }
    
    private func formatDate(_ dateString: String) -> String {
        // Format ISO date string to readable format
        let formatter = ISO8601DateFormatter()
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .short
            return displayFormatter.string(from: date)
        }
        return dateString
    }
}
```

## 🚀 Quick Start for Developers

### 1. Backend Setup
```bash
# Clone repository
git clone https://github.com/Ismat-Samadov/birjobBackend.git
cd birjobBackend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configurations

# Run development server
python main.py
```

### 2. iOS App Creation
```bash
# Create new Xcode project
# Set Bundle ID: com.ismats.birjob
# Add Push Notifications capability
# Implement the code examples above
```

### 3. Testing
```bash
# Test API health
curl https://birjobbackend-ir3e.onrender.com/health

# Test job search
curl "https://birjobbackend-ir3e.onrender.com/api/v1/jobs/?search=iOS&limit=5"

# Test device registration
curl -X POST "https://birjobbackend-ir3e.onrender.com/api/v1/devices/register" \
  -H "Content-Type: application/json" \
  -d '{"device_token":"test-token","device_info":{"device_model":"iPhone"}}'
```

## 🔧 Development Tools & Scripts

### Project Structure
```
birjobBackend/
├── app/
│   ├── api/v1/endpoints/        # API route handlers
│   │   ├── devices.py          # Device & push notification endpoints
│   │   ├── jobs.py             # Job search & management
│   │   ├── users.py            # User management
│   │   ├── chatbot.py          # AI chat integration
│   │   ├── analytics.py        # User analytics
│   │   └── notifications.py    # Notification management
│   ├── core/                   # Core utilities
│   │   ├── config.py           # App configuration
│   │   ├── database.py         # Database connection
│   │   └── redis_client.py     # Redis client
│   ├── models/                 # Database models
│   │   ├── user.py             # User & related models
│   │   ├── device.py           # Device token model
│   │   └── notifications.py    # Notification models
│   ├── schemas/                # Pydantic schemas
│   │   ├── user.py             # User API schemas
│   │   ├── device.py           # Device API schemas
│   │   └── notifications.py    # Notification schemas
│   └── services/               # Business logic
│       ├── push_notifications.py      # APNs integration
│       ├── job_notification_service.py # Job matching logic
│       ├── notification_scheduler.py   # Background scheduler
│       └── gemini_chatbot.py          # AI chat service
├── main.py                     # FastAPI application
├── run.py                      # Production runner
└── requirements.txt            # Python dependencies
```

### Key Service Classes

#### Push Notification Service
```python
# app/services/push_notifications.py
class PushNotificationService:
    async def send_job_match_notification(
        self, device_token: str, device_id: str,
        job: Dict[str, Any], matched_keywords: List[str], match_id: str
    ) -> bool:
        # Sends APNs notification for job matches
```

#### Job Notification Service  
```python
# app/services/job_notification_service.py
class JobNotificationService:
    async def process_job_notifications(
        self, source_filter: Optional[str] = None,
        limit: int = 100, dry_run: bool = False
    ) -> Dict[str, Any]:
        # Processes job matching and sends notifications
```

## 📊 Production Monitoring

### Health Checks
- **API Health**: `GET /health`
- **Database Status**: `GET /api/v1/health`
- **Job Count**: `GET /api/v1/jobs/stats/summary`

### Key Metrics
- **Total Jobs**: 4,367+ (live)
- **Job Sources**: 39 platforms
- **Update Frequency**: Every 2 hours
- **Notification Matching**: Every 5 minutes

### Logging
```python
# Configure logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Key log events
- User registration
- Job notifications sent
- APNs errors
- Database connections
- AI chat interactions
```

## 🚀 Deployment Information

### Production Environment
- **Platform**: Render.com
- **URL**: https://birjobbackend-ir3e.onrender.com
- **Database**: PostgreSQL (Neon)
- **Redis**: Upstash
- **Push Notifications**: APNs (Production)

### Configuration Files
- `render.yaml`: Deployment configuration
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (not in repo)

## 📝 API Response Examples

### Job Search Response
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": 12345,
        "title": "Senior iOS Developer",
        "company": "Apple Inc.",
        "location": "Cupertino, CA",
        "description": "Develop next-generation iOS applications...",
        "apply_link": "https://jobs.apple.com/apply/12345",
        "source": "apple_careers",
        "created_at": "2025-07-07T10:30:00Z"
      }
    ],
    "total_count": 1,
    "pagination": {
      "limit": 20,
      "offset": 0,
      "has_more": false
    }
  }
}
```

### Device Registration Response
```json
{
  "success": true,
  "data": {
    "device_id": "ABC123-DEF456-789",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "registered_at": "2025-07-07T10:30:00Z",
    "message": "Device registered successfully"
  }
}
```

### User Profile Response
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "keywords": ["iOS", "Swift", "Mobile Development"],
    "notifications_enabled": true,
    "created_at": "2025-07-07T10:30:00Z",
    "device_count": 1
  }
}
```

## 🤝 Integration Checklist for AI Models

When building or updating the iOS app, ensure:

### Required Implementations
- [ ] **Push Notifications**: Request permissions, handle device tokens
- [ ] **API Integration**: Implement all service methods
- [ ] **User Management**: Device registration, keyword management
- [ ] **Job Search**: Search, filter, save functionality
- [ ] **Notification Handling**: Foreground and background notifications
- [ ] **Deep Linking**: Handle `birjob://` URL scheme
- [ ] **Error Handling**: Network errors, API failures

### Optional Enhancements
- [ ] **AI Chat Integration**: Career assistant chatbot
- [ ] **Analytics**: User behavior tracking
- [ ] **Offline Support**: Cache jobs for offline viewing
- [ ] **Dark Mode**: UI theme support
- [ ] **Accessibility**: VoiceOver and accessibility features

### Testing Requirements
- [ ] **API Connectivity**: Test all endpoints
- [ ] **Push Notifications**: Verify notification delivery
- [ ] **User Flows**: Registration, search, save jobs
- [ ] **Edge Cases**: Network failures, empty states

## 📞 Support & Contact

- **Repository**: https://github.com/Ismat-Samadov/birjobBackend
- **API Documentation**: Live at `/docs` endpoint
- **Production API**: https://birjobbackend-ir3e.onrender.com

---

**Last Updated**: July 2025  
**API Version**: v1  
**Backend Status**: ✅ Production Ready  
**Push Notifications**: ✅ Fully Operational