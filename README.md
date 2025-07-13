# 📱 iOS Job App Backend - AI-Optimized Documentation

## 🎯 Overview

**Ultra-minimal, production-ready backend for iOS job notification apps**. Features device-based registration, hash-based notification deduplication, and real-time analytics. Perfect for AI models developing iOS applications.

**🌐 Production API**: `https://birjobbackend-ir3e.onrender.com`  
**📚 Interactive Docs**: `https://birjobbackend-ir3e.onrender.com/docs`

---

## 🏗️ System Architecture

### Core Philosophy
- **Device-First**: No email required - just device tokens + keywords
- **Hash Deduplication**: MD5-based job uniqueness (never spam users)
- **Real-Time**: Live job matching and instant push notifications
- **Minimal Schema**: Only 3 essential tables for maximum performance

### Database Schema (Current)
```sql
-- 1. Device Users (Primary Table)
CREATE TABLE iosapp.device_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_token VARCHAR(64) NOT NULL UNIQUE,     -- APNs token (exactly 64 hex chars)
    keywords JSONB NOT NULL DEFAULT '[]',         -- Job search keywords
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT device_token_length CHECK (length(device_token) >= 64)
);

-- 2. Notification Deduplication (Hash-Based)
CREATE TABLE iosapp.notification_hashes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES device_users(id) ON DELETE CASCADE,
    job_hash VARCHAR(32) NOT NULL,               -- MD5 hash of job_title + company
    job_title VARCHAR(500),
    job_company VARCHAR(200), 
    job_source VARCHAR(100),
    matched_keywords JSONB,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(device_id, job_hash)                   -- Prevents duplicate notifications
);

-- 3. Analytics Tracking (Lightweight)
CREATE TABLE iosapp.user_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES device_users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,                 -- 'registration', 'notification_received', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Job Data Source (External - Maintained by Scraper)
-- scraper.jobs_jobpost table contains 4,396+ live jobs
```

### Data Flow
```
iOS App → Device Registration → Job Matching → Push Notifications
   ↓            ↓                    ↓              ↓
Keywords → Keyword Matching → Hash Check → APNs Delivery
```

---

## 📱 Ultra-Minimal Registration Flow

### For iOS Apps (Perfect for AI Development)
```swift
// STEP 1: Request notification permission & get device token
UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound])
UIApplication.shared.registerForRemoteNotifications()

// STEP 2: Single API call registration (30 seconds total)
func registerDevice(deviceToken: String, keywords: [String]) {
    let request = [
        "device_token": deviceToken,    // 64 hex chars from Apple
        "keywords": keywords           // ["iOS", "Swift", "Remote"]
    ]
    // POST /api/v1/device/register
}

// STEP 3: Done! User ready for job notifications
```

**User Experience**: `App Launch → Select Keywords → Ready!`

---

## 🔔 Core API Endpoints

### 1. Health & System Status
```http
GET /health
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-13T05:24:12.738688+00:00",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "apns": "healthy",
    "scraper": "healthy"
  },
  "metrics": {
    "active_devices": 0,
    "active_subscriptions": 0,
    "matches_last_24h": 0,
    "notifications_sent_last_24h": 1
  }
}
```

**iOS Implementation:**
```swift
func checkHealth() async throws -> HealthResponse {
    let url = URL(string: "\(baseURL)/health")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(HealthResponse.self, from: data)
}
```

### 2. Device Registration (Primary Endpoint)
```http
POST /api/v1/devices/register
```

**Request:**
```json
{
  "device_token": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "device_id": "ios-unique-device-uuid",
  "email": "user@example.com",
  "keywords": ["iOS", "Swift", "Mobile", "Remote"],
  "preferred_sources": ["linkedin", "indeed"],
  "notifications_enabled": true,
  "device_info": {
    "device_model": "iPhone 15 Pro",
    "os_version": "17.2",
    "app_version": "1.0.0",
    "timezone": "America/New_York"
  }
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Device registered successfully",
  "data": {
    "user_id": "uuid-here",
    "device_id": "ios-unique-device-uuid"
  }
}
```

**iOS Data Models:**
```swift
struct DeviceRegistrationRequest: Codable {
    let device_token: String        // Required: 64 hex chars
    let device_id: String          // Required: unique identifier
    let email: String?             // Optional
    let keywords: [String]         // Required: job keywords
    let preferred_sources: [String]? // Optional
    let notifications_enabled: Bool // Required: true
    let device_info: DeviceInfo    // Required
}

struct DeviceInfo: Codable {
    let device_model: String       // "iPhone 15 Pro"
    let os_version: String         // "17.2"
    let app_version: String        // "1.0.0"
    let timezone: String           // "America/New_York"
}

struct DeviceRegistrationResponse: Codable {
    let success: Bool
    let message: String
    let data: RegistrationData
}

struct RegistrationData: Codable {
    let user_id: String
    let device_id: String
}
```

**iOS Implementation:**
```swift
func registerDevice() async throws {
    guard let deviceToken = UserDefaults.standard.string(forKey: "deviceToken") else {
        throw APIError.noDeviceToken
    }
    
    let request = DeviceRegistrationRequest(
        device_token: deviceToken,
        device_id: UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString,
        email: nil,
        keywords: UserDefaults.standard.stringArray(forKey: "selectedKeywords") ?? [],
        preferred_sources: ["linkedin", "indeed"],
        notifications_enabled: true,
        device_info: DeviceInfo.current()
    )
    
    let url = URL(string: "\(baseURL)/api/v1/devices/register")!
    var urlRequest = URLRequest(url: url)
    urlRequest.httpMethod = "POST"
    urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
    urlRequest.httpBody = try JSONEncoder().encode(request)
    
    let (data, response) = try await URLSession.shared.data(for: urlRequest)
    
    guard let httpResponse = response as? HTTPURLResponse,
          200...299 ~= httpResponse.statusCode else {
        throw APIError.registrationFailed
    }
    
    let result = try JSONDecoder().decode(DeviceRegistrationResponse.self, from: data)
    
    // Store user data locally
    UserDefaults.standard.set(result.data.user_id, forKey: "userId")
    UserDefaults.standard.set(result.data.device_id, forKey: "deviceId")
}
```

### 3. Update Keywords
```http
PUT /api/v1/users/{device_id}
```

**Request:**
```json
{
  "keywords": ["iOS", "Swift", "SwiftUI", "Remote"],
  "notifications_enabled": true
}
```

**iOS Implementation:**
```swift
func updateKeywords(_ keywords: [String]) async throws {
    guard let deviceId = UserDefaults.standard.string(forKey: "deviceId") else {
        throw APIError.noDeviceId
    }
    
    let url = URL(string: "\(baseURL)/api/v1/users/\(deviceId)")!
    let request = ["keywords": keywords, "notifications_enabled": true] as [String: Any]
    
    try await performRequest(url: url, method: "PUT", body: request)
    
    // Update local storage
    UserDefaults.standard.set(keywords, forKey: "selectedKeywords")
}
```

### 4. Check User Status by Email
```http
POST /api/v1/users/check-email
```

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response (Existing User):**
```json
{
  "success": true,
  "message": "User found - profile check complete",
  "data": {
    "exists": true,
    "user_id": "uuid-here",
    "email": "user@example.com",
    "has_profile": true,
    "has_keywords": true,
    "keywords": ["iOS", "Swift", "Remote"],
    "keywords_count": 3,
    "can_skip_onboarding": true,
    "requires_keywords_setup": false
  }
}
```

**Response (New User):**
```json
{
  "success": true,
  "message": "Email not found - full registration required",
  "data": {
    "exists": false,
    "has_profile": false,
    "has_keywords": false,
    "requires_full_registration": true,
    "email": "user@example.com"
  }
}
```

### 5. Get Jobs
```http
GET /api/v1/jobs/
```

**Query Parameters:**
- `search` (string): Job title/description search
- `company` (string): Filter by company
- `location` (string): Filter by location  
- `source` (string): Filter by source (linkedin, indeed, etc.)
- `employment_type` (string): full_time, part_time, contract
- `experience_level` (string): entry, mid, senior, lead
- `remote_allowed` (boolean): true/false
- `limit` (int): Results per page (default: 20, max: 100)
- `offset` (int): Pagination offset

**Example:**
```http
GET /api/v1/jobs/?search=iOS&company=Apple&limit=10&remote_allowed=true
```

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": 12345,
        "title": "Senior iOS Developer",
        "company": "Apple Inc",
        "location": "Cupertino, CA",
        "description": "Looking for experienced iOS developer...",
        "apply_link": "https://jobs.apple.com/...",
        "source": "linkedin",
        "employment_type": "full_time",
        "experience_level": "senior",
        "salary_range": "$150,000 - $200,000",
        "remote_allowed": true,
        "created_at": "2025-07-13T10:00:00Z",
        "updated_at": "2025-07-13T10:00:00Z"
      }
    ],
    "total_count": 1247,
    "pagination": {
      "limit": 10,
      "offset": 0,
      "has_more": true,
      "next_offset": 10
    }
  }
}
```

**iOS Implementation:**
```swift
func searchJobs(query: String?, limit: Int = 20, offset: Int = 0) async throws -> JobSearchResponse {
    var components = URLComponents(string: "\(baseURL)/api/v1/jobs/")!
    var queryItems = [
        URLQueryItem(name: "limit", value: String(limit)),
        URLQueryItem(name: "offset", value: String(offset))
    ]
    
    if let query = query, !query.isEmpty {
        queryItems.append(URLQueryItem(name: "search", value: query))
    }
    
    components.queryItems = queryItems
    
    let (data, _) = try await URLSession.shared.data(from: components.url!)
    return try JSONDecoder().decode(JobSearchResponse.self, from: data)
}
```

### 6. Save/Unsave Jobs
```http
POST /api/v1/jobs/save
DELETE /api/v1/jobs/unsave
```

**Request:**
```json
{
  "device_id": "ios-device-uuid",
  "job_id": 12345
}
```

### 7. Get Saved Jobs
```http
GET /api/v1/jobs/saved/{device_id}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 12345,
      "title": "iOS Developer",
      "company": "Apple",
      "saved_at": "2025-07-13T10:30:00Z",
      "job_details": { /* full job object */ }
    }
  ]
}
```

### 8. Track Job View
```http
POST /api/v1/jobs/view
```

**Request:**
```json
{
  "device_id": "ios-device-uuid",
  "job_id": 12345,
  "view_duration_seconds": 45
}
```

---

## 🔔 Push Notification System

### Notification Registration
```http
POST /api/v1/notifications/token
```

**Request:**
```json
{
  "device_token": "64-char-hex-token",
  "device_id": "ios-device-uuid",
  "email": "user@example.com",
  "device_info": {
    "device_model": "iPhone 15 Pro",
    "os_version": "17.2"
  }
}
```

### Notification History
```http
GET /api/v1/notifications/history/{device_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "uuid-here",
    "total_notifications": 23,
    "recent_notifications": [
      {
        "id": "notif-uuid",
        "job_id": 12345,
        "job_title": "iOS Developer",
        "job_company": "Apple Inc",
        "matched_keywords": ["iOS", "Swift"],
        "sent_at": "2025-07-13T09:15:00Z",
        "opened": false
      }
    ]
  }
}
```

### Notification Inbox (Grouped)
```http
GET /api/v1/notifications/inbox/{device_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "batch-uuid",
        "type": "job_match",
        "title": "3 New Jobs Found!",
        "message": "💼 iOS, Swift, Remote",
        "job_count": 3,
        "matched_keywords": ["iOS", "Swift"],
        "created_at": "2025-07-13T09:15:00Z",
        "is_read": false,
        "jobs": [
          {
            "id": 12345,
            "title": "iOS Developer",
            "company": "Apple Inc",
            "location": "Remote",
            "apply_link": "https://..."
          }
        ]
      }
    ],
    "unread_count": 5,
    "total_count": 23
  }
}
```

### Mark as Read/Delete
```http
POST /api/v1/notifications/{notification_id}/read
DELETE /api/v1/notifications/{notification_id}
```

### Test Notifications
```http
POST /api/v1/notifications/test-push/{device_id}
```

---

## 📊 Analytics

### User Analytics
```http
GET /api/v1/analytics/user/{device_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "registration_date": "2025-07-10T14:30:00Z",
    "total_notifications_received": 23,
    "notifications_opened": 18,
    "open_rate": 78.3,
    "favorite_keywords": ["iOS", "Swift", "Remote"],
    "jobs_saved": 5,
    "last_active": "2025-07-13T10:45:00Z"
  }
}
```

### Track Events
```http
POST /api/v1/analytics/event
```

**Request:**
```json
{
  "device_id": "ios-device-uuid",
  "event_type": "job_applied",
  "event_data": {
    "job_id": 12345,
    "source": "notification"
  }
}
```

### System Statistics
```http
GET /api/v1/analytics/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_users": 156,
    "active_users_24h": 45,
    "active_users_7d": 89,
    "notifications_sent_24h": 234,
    "top_keywords": [
      {"keyword": "iOS", "users": 89},
      {"keyword": "Remote", "users": 67},
      {"keyword": "Swift", "users": 54}
    ]
  }
}
```

---

## 🤖 AI Chatbot (Optional)

### Chat with AI
```http
POST /api/v1/chatbot/chat
```

**Request:**
```json
{
  "message": "What iOS jobs would be good for a Swift developer with 3 years experience?",
  "user_id": "device-id-here",
  "context": {
    "user_keywords": ["iOS", "Swift"],
    "experience_level": "mid"
  }
}
```

### Job Analysis
```http
POST /api/v1/chatbot/analyze-job
```

**Request:**
```json
{
  "job_id": 12345,
  "device_id": "ios-device-uuid"
}
```

### AI Recommendations
```http
GET /api/v1/chatbot/recommendations/{device_id}
```

---

## 🔧 iOS Implementation Guide

### Complete AppDelegate Setup
```swift
import UIKit
import UserNotifications

@main
class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        
        // Setup notification center
        UNUserNotificationCenter.current().delegate = self
        
        // Request permissions
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            DispatchQueue.main.async {
                if granted {
                    application.registerForRemoteNotifications()
                }
            }
        }
        
        return true
    }
    
    // Handle device token
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        // Store locally
        UserDefaults.standard.set(tokenString, forKey: "deviceToken")
        
        // Send to backend
        Task {
            try await APIService.shared.registerDevice()
        }
    }
    
    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
        
        let userInfo = response.notification.request.content.userInfo
        
        if let customData = userInfo["custom_data"] as? [String: Any],
           let type = customData["type"] as? String {
            
            switch type {
            case "job_match":
                if let jobId = customData["job_id"] as? Int {
                    // Navigate to job detail
                    NotificationCenter.default.post(name: .openJobDetail, object: jobId)
                }
            case "bulk_job_match":
                // Navigate to job list
                NotificationCenter.default.post(name: .openJobList, object: nil)
            default:
                break
            }
        }
        
        completionHandler()
    }
    
    // Show notifications in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.alert, .badge, .sound])
    }
}

extension Notification.Name {
    static let openJobDetail = Notification.Name("openJobDetail")
    static let openJobList = Notification.Name("openJobList")
}
```

### Complete API Service
```swift
import Foundation

class APIService: ObservableObject {
    static let shared = APIService()
    
    private let baseURL = "https://birjobbackend-ir3e.onrender.com"
    private let session = URLSession.shared
    
    private init() {}
    
    // MARK: - Device Registration
    
    func registerDevice() async throws {
        guard let deviceToken = UserDefaults.standard.string(forKey: "deviceToken"),
              !deviceToken.isEmpty else {
            throw APIError.noDeviceToken
        }
        
        let keywords = UserDefaults.standard.stringArray(forKey: "selectedKeywords") ?? []
        
        let request = DeviceRegistrationRequest(
            device_token: deviceToken,
            device_id: UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString,
            email: UserDefaults.standard.string(forKey: "userEmail"),
            keywords: keywords,
            preferred_sources: ["linkedin", "indeed", "glassdoor"],
            notifications_enabled: true,
            device_info: DeviceInfo(
                device_model: UIDevice.current.model,
                os_version: UIDevice.current.systemVersion,
                app_version: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0",
                timezone: TimeZone.current.identifier
            )
        )
        
        let response: DeviceRegistrationResponse = try await performRequest(
            endpoint: "/api/v1/devices/register",
            method: "POST",
            body: request
        )
        
        // Store user data
        UserDefaults.standard.set(response.data.user_id, forKey: "userId")
        UserDefaults.standard.set(response.data.device_id, forKey: "deviceId")
    }
    
    // MARK: - Job Management
    
    func searchJobs(query: String? = nil, limit: Int = 20, offset: Int = 0) async throws -> JobSearchResponse {
        var components = URLComponents(string: "\(baseURL)/api/v1/jobs/")!
        
        var queryItems = [
            URLQueryItem(name: "limit", value: String(limit)),
            URLQueryItem(name: "offset", value: String(offset))
        ]
        
        if let query = query, !query.isEmpty {
            queryItems.append(URLQueryItem(name: "search", value: query))
        }
        
        components.queryItems = queryItems
        
        return try await performRequest(url: components.url!, method: "GET")
    }
    
    func saveJob(jobId: Int) async throws {
        guard let deviceId = UserDefaults.standard.string(forKey: "deviceId") else {
            throw APIError.noDeviceId
        }
        
        let request = ["device_id": deviceId, "job_id": jobId] as [String: Any]
        
        let _: GenericResponse = try await performRequest(
            endpoint: "/api/v1/jobs/save",
            method: "POST",
            body: request
        )
    }
    
    func getSavedJobs() async throws -> SavedJobsResponse {
        guard let deviceId = UserDefaults.standard.string(forKey: "deviceId") else {
            throw APIError.noDeviceId
        }
        
        return try await performRequest(
            endpoint: "/api/v1/jobs/saved/\(deviceId)",
            method: "GET"
        )
    }
    
    // MARK: - Analytics
    
    func trackEvent(eventType: String, eventData: [String: Any] = [:]) async {
        guard let deviceId = UserDefaults.standard.string(forKey: "deviceId") else {
            return
        }
        
        let request = [
            "device_id": deviceId,
            "event_type": eventType,
            "event_data": eventData
        ] as [String: Any]
        
        do {
            let _: GenericResponse = try await performRequest(
                endpoint: "/api/v1/analytics/event",
                method: "POST",
                body: request
            )
        } catch {
            print("⚠️ Analytics tracking failed: \(error)")
        }
    }
    
    // MARK: - Helper Methods
    
    private func performRequest<T: Codable>(
        endpoint: String,
        method: String,
        body: Any? = nil
    ) async throws -> T {
        let url = URL(string: "\(baseURL)\(endpoint)")!
        return try await performRequest(url: url, method: method, body: body)
    }
    
    private func performRequest<T: Codable>(
        url: URL,
        method: String,
        body: Any? = nil
    ) async throws -> T {
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("BirJob iOS/1.0", forHTTPHeaderField: "User-Agent")
        
        if let body = body {
            if let codableBody = body as? Encodable {
                request.httpBody = try JSONEncoder().encode(codableBody)
            } else {
                request.httpBody = try JSONSerialization.data(withJSONObject: body)
            }
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            if let errorData = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let detail = errorData["detail"] as? String {
                throw APIError.serverError(detail)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
}

// MARK: - Error Handling

enum APIError: LocalizedError {
    case noDeviceToken
    case noDeviceId
    case invalidResponse
    case serverError(String)
    case httpError(Int)
    
    var errorDescription: String? {
        switch self {
        case .noDeviceToken:
            return "Device token not available"
        case .noDeviceId:
            return "Device not registered"
        case .invalidResponse:
            return "Invalid server response"
        case .serverError(let message):
            return "Server error: \(message)"
        case .httpError(let code):
            return "HTTP error: \(code)"
        }
    }
}
```

### SwiftUI Views
```swift
import SwiftUI

struct JobSearchView: View {
    @StateObject private var viewModel = JobSearchViewModel()
    @State private var searchText = ""
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Bar
                SearchBar(text: $searchText, onSearchButtonClicked: viewModel.search)
                
                // Job List
                if viewModel.isLoading && viewModel.jobs.isEmpty {
                    ProgressView("Loading jobs...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(viewModel.jobs) { job in
                            NavigationLink(destination: JobDetailView(job: job)) {
                                JobRowView(job: job)
                            }
                            .onAppear {
                                if job == viewModel.jobs.last {
                                    viewModel.loadMore()
                                }
                            }
                        }
                        
                        if viewModel.isLoadingMore {
                            HStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                        }
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("Jobs")
            .onAppear {
                viewModel.loadJobs()
                APIService.shared.trackEvent(eventType: "app_open")
            }
        }
    }
}

@MainActor
class JobSearchViewModel: ObservableObject {
    @Published var jobs: [Job] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    
    private var currentOffset = 0
    private let pageSize = 20
    
    func loadJobs() {
        isLoading = true
        currentOffset = 0
        
        Task {
            do {
                let response = try await APIService.shared.searchJobs(limit: pageSize, offset: currentOffset)
                self.jobs = response.data.jobs
                self.currentOffset = pageSize
                self.isLoading = false
            } catch {
                self.isLoading = false
                print("Error loading jobs: \(error)")
            }
        }
    }
    
    func loadMore() {
        guard !isLoadingMore else { return }
        
        isLoadingMore = true
        
        Task {
            do {
                let response = try await APIService.shared.searchJobs(limit: pageSize, offset: currentOffset)
                self.jobs.append(contentsOf: response.data.jobs)
                self.currentOffset += pageSize
                self.isLoadingMore = false
            } catch {
                self.isLoadingMore = false
            }
        }
    }
    
    func search(query: String) {
        Task {
            do {
                let response = try await APIService.shared.searchJobs(query: query, limit: pageSize, offset: 0)
                self.jobs = response.data.jobs
                self.currentOffset = pageSize
            } catch {
                print("Search error: \(error)")
            }
        }
    }
    
    func refresh() async {
        currentOffset = 0
        loadJobs()
    }
}
```

---

## 🚨 Error Handling

### Standard Error Response
```json
{
  "success": false,
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-07-13T10:30:00Z"
}
```

### Common HTTP Status Codes
- **200**: Success
- **400**: Bad Request (validation errors)  
- **401**: Unauthorized
- **404**: Not Found
- **429**: Rate Limited
- **500**: Internal Server Error

### iOS Error Handling
```swift
func handleAPIError(_ error: Error) {
    if let apiError = error as? APIError {
        switch apiError {
        case .noDeviceToken:
            // Re-register for notifications
            UIApplication.shared.registerForRemoteNotifications()
        case .serverError(let message):
            // Show user-friendly error
            showAlert(title: "Error", message: message)
        case .httpError(404):
            // Handle not found
            showAlert(title: "Not Found", message: "Resource not available")
        default:
            showAlert(title: "Error", message: apiError.localizedDescription)
        }
    }
}
```

---

## 🔐 Security & Validation

### Device Token Requirements
- **Exactly 64 hexadecimal characters** (APNs production tokens)
- **No test/fake tokens accepted** in production
- **Automatic validation** against Apple's format

### Rate Limiting
- **Registration**: 10 requests per hour per device
- **Job Search**: 1000 requests per hour per device  
- **Analytics**: 100 requests per hour per device

### Data Privacy
- **No personal data stored** beyond keywords and device tokens
- **Complete data deletion** via device deletion endpoint
- **GDPR compliant** data handling

---

## 🚀 Quick Start

### iOS App Setup (5 Minutes)
```swift
// 1. Add to Info.plist
<key>UIBackgroundModes</key>
<array>
    <string>remote-notification</string>
</array>

// 2. Setup AppDelegate (copy code above)

// 3. Request notification permissions
UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, _ in
    if granted {
        DispatchQueue.main.async {
            UIApplication.shared.registerForRemoteNotifications()
        }
    }
}

// 4. Handle device token and register
func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
    UserDefaults.standard.set(tokenString, forKey: "deviceToken")
    
    Task {
        try await APIService.shared.registerDevice()
    }
}

// 5. Done! Your app now receives job notifications
```

### Test Your Integration
```bash
# Health check
curl https://birjobbackend-ir3e.onrender.com/health

# Search jobs  
curl "https://birjobbackend-ir3e.onrender.com/api/v1/jobs/?search=iOS&limit=5"

# Test notification
curl -X POST "https://birjobbackend-ir3e.onrender.com/api/v1/notifications/test-push/YOUR_DEVICE_ID"
```

---

## 📊 Production Status

**✅ System Health**: All services operational  
**✅ Job Data**: 4,396+ live jobs updated every 2 hours  
**✅ Push Notifications**: APNs production ready  
**✅ API Response**: <200ms average response time  
**✅ Database**: PostgreSQL with optimized indexes  
**✅ Analytics**: Real-time user behavior tracking  

**🌐 Production URL**: `https://birjobbackend-ir3e.onrender.com`  
**📚 API Docs**: `https://birjobbackend-ir3e.onrender.com/docs`  
**📊 Health Check**: `https://birjobbackend-ir3e.onrender.com/health`

---

**Last Updated**: July 13, 2025  
**API Version**: v1.0.0  
**Optimized for**: AI Model Consumption & iOS Development  

*This documentation provides complete implementation details for building production-ready iOS job notification apps.*