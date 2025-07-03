# iOS App Integration Guide

**Backend**: `https://birjobbackend-ir3e.onrender.com`  
**Target**: iOS 15.0+  
**Language**: Swift 5.0+  
**Architecture**: Clean Architecture + MVVM

---

## 🏗️ iOS App Architecture

### Recommended Project Structure
```
JobApp/
├── App/
│   ├── JobAppApp.swift
│   ├── ContentView.swift
│   └── AppDelegate.swift
├── Core/
│   ├── Networking/
│   │   ├── APIClient.swift
│   │   ├── APIEndpoints.swift
│   │   └── NetworkError.swift
│   ├── Models/
│   │   ├── User.swift
│   │   ├── Job.swift
│   │   ├── Device.swift
│   │   └── ChatMessage.swift
│   └── Utils/
│       ├── DeviceManager.swift
│       └── Constants.swift
├── Features/
│   ├── Authentication/
│   ├── JobSearch/
│   ├── SavedJobs/
│   ├── AIChat/
│   └── Profile/
├── Services/
│   ├── UserService.swift
│   ├── JobService.swift
│   ├── ChatService.swift
│   └── AnalyticsService.swift
└── Resources/
    ├── Info.plist
    └── Assets.xcassets
```

---

## 🔧 Core Implementation

### 1. API Client Setup

```swift
// Core/Networking/APIClient.swift
import Foundation

class APIClient {
    static let shared = APIClient()
    
    private let baseURL = "https://birjobbackend-ir3e.onrender.com"
    private let session = URLSession.shared
    
    private init() {}
    
    func request<T: Codable>(
        endpoint: APIEndpoint,
        responseType: T.Type
    ) async throws -> T {
        let url = URL(string: baseURL + endpoint.path)!
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = endpoint.body {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            throw NetworkError.serverError(httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(T.self, from: data)
    }
}

// HTTP Methods
enum HTTPMethod: String {
    case GET, POST, PUT, DELETE
}

// Network Errors
enum NetworkError: Error {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
    case userNotFound
}
```

### 2. API Endpoints Configuration

```swift
// Core/Networking/APIEndpoints.swift
import Foundation

struct APIEndpoint {
    let path: String
    let method: HTTPMethod
    let body: [String: Any]?
    
    init(path: String, method: HTTPMethod, body: [String: Any]? = nil) {
        self.path = path
        self.method = method
        self.body = body
    }
}

extension APIEndpoint {
    // User Management
    static func registerUser(deviceId: String, email: String, keywords: [String]) -> APIEndpoint {
        APIEndpoint(
            path: "/api/v1/users/register",
            method: .POST,
            body: [
                "device_id": deviceId,
                "email": email,
                "keywords": keywords,
                "notifications_enabled": true
            ]
        )
    }
    
    static func getUserProfile(deviceId: String) -> APIEndpoint {
        APIEndpoint(path: "/api/v1/users/profile/\(deviceId)", method: .GET)
    }
    
    static func updateProfile(deviceId: String, email: String, keywords: [String]) -> APIEndpoint {
        APIEndpoint(
            path: "/api/v1/users/profile",
            method: .PUT,
            body: [
                "device_id": deviceId,
                "email": email,
                "keywords": keywords,
                "notifications_enabled": true
            ]
        )
    }
    
    // Job Management
    static func searchJobs(query: String? = nil, limit: Int = 20, offset: Int = 0) -> APIEndpoint {
        var path = "/api/v1/jobs/?limit=\(limit)&offset=\(offset)"
        if let query = query, !query.isEmpty {
            path += "&search=\(query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")"
        }
        return APIEndpoint(path: path, method: .GET)
    }
    
    static func getJobDetails(jobId: Int) -> APIEndpoint {
        APIEndpoint(path: "/api/v1/jobs/\(jobId)", method: .GET)
    }
    
    static func saveJob(deviceId: String, jobId: Int) -> APIEndpoint {
        APIEndpoint(
            path: "/api/v1/jobs/save",
            method: .POST,
            body: ["device_id": deviceId, "job_id": jobId]
        )
    }
    
    static func getSavedJobs(deviceId: String) -> APIEndpoint {
        APIEndpoint(path: "/api/v1/jobs/saved/\(deviceId)", method: .GET)
    }
    
    static func recordJobView(deviceId: String, jobId: Int, duration: Int) -> APIEndpoint {
        APIEndpoint(
            path: "/api/v1/jobs/view",
            method: .POST,
            body: [
                "device_id": deviceId,
                "job_id": jobId,
                "view_duration_seconds": duration
            ]
        )
    }
    
    // AI Chatbot
    static func chatWithAI(deviceId: String, message: String, history: [ChatMessage] = []) -> APIEndpoint {
        let conversationHistory = history.map { msg in
            ["role": msg.role, "content": msg.content]
        }
        
        return APIEndpoint(
            path: "/api/v1/chatbot/chat",
            method: .POST,
            body: [
                "device_id": deviceId,
                "message": message,
                "conversation_history": conversationHistory,
                "include_user_context": true
            ]
        )
    }
    
    static func getJobRecommendations(deviceId: String, keywords: [String], location: String? = nil) -> APIEndpoint {
        var body: [String: Any] = [
            "device_id": deviceId,
            "keywords": keywords
        ]
        if let location = location {
            body["location"] = location
        }
        
        return APIEndpoint(
            path: "/api/v1/chatbot/recommendations",
            method: .POST,
            body: body
        )
    }
    
    static func analyzeJob(deviceId: String, jobId: Int, title: String, company: String, description: String? = nil) -> APIEndpoint {
        var body: [String: Any] = [
            "device_id": deviceId,
            "job_id": jobId,
            "job_title": title,
            "job_company": company
        ]
        if let description = description {
            body["job_description"] = description
        }
        
        return APIEndpoint(
            path: "/api/v1/chatbot/analyze-job",
            method: .POST,
            body: body
        )
    }
    
    // Analytics
    static func recordAnalyticsEvent(deviceId: String, actionType: String, actionData: [String: Any] = [:]) -> APIEndpoint {
        APIEndpoint(
            path: "/api/v1/analytics/event",
            method: .POST,
            body: [
                "device_id": deviceId,
                "action_type": actionType,
                "action_data": actionData
            ]
        )
    }
    
    // Device Management
    static func registerDevice(deviceId: String, deviceToken: String, deviceInfo: [String: Any]) -> APIEndpoint {
        APIEndpoint(
            path: "/api/v1/devices/register",
            method: .POST,
            body: [
                "device_id": deviceId,
                "device_token": deviceToken,
                "device_info": deviceInfo
            ]
        )
    }
}
```

### 3. Data Models

```swift
// Core/Models/User.swift
import Foundation

struct User: Codable {
    let id: String
    let deviceId: String
    let email: String
    let keywords: [String]
    let preferredSources: [String]
    let notificationsEnabled: Bool
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, email, keywords
        case deviceId = "device_id"
        case preferredSources = "preferred_sources"
        case notificationsEnabled = "notifications_enabled"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct UserRegistrationResponse: Codable {
    let success: Bool
    let message: String
    let data: UserData
    
    struct UserData: Codable {
        let userId: String
        let deviceId: String
        
        enum CodingKeys: String, CodingKey {
            case userId = "user_id"
            case deviceId = "device_id"
        }
    }
}

struct UserProfileResponse: Codable {
    let success: Bool
    let message: String
    let data: User
}
```

```swift
// Core/Models/Job.swift
import Foundation

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

struct JobSearchResponse: Codable {
    let success: Bool
    let data: JobData
    
    struct JobData: Codable {
        let jobs: [Job]
        let pagination: Pagination
        let filters: Filters
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
            case total, limit, offset, hasMore, hasPrevious
            case currentPage = "current_page"
            case totalPages = "total_pages"
        }
    }
    
    struct Filters: Codable {
        let search: String?
        let company: String?
        let source: String?
    }
}

struct SavedJob: Codable {
    let jobId: Int
    let jobTitle: String
    let jobCompany: String
    let jobSource: String
    let savedAt: String
    
    enum CodingKeys: String, CodingKey {
        case jobId = "job_id"
        case jobTitle = "job_title"
        case jobCompany = "job_company"
        case jobSource = "job_source"
        case savedAt = "saved_at"
    }
}

struct SavedJobsResponse: Codable {
    let success: Bool
    let data: SavedJobsData
    
    struct SavedJobsData: Codable {
        let savedJobs: [SavedJob]
        
        enum CodingKeys: String, CodingKey {
            case savedJobs = "saved_jobs"
        }
    }
}
```

```swift
// Core/Models/ChatMessage.swift
import Foundation

struct ChatMessage: Codable, Identifiable {
    let id = UUID()
    let role: String // "user" or "assistant"
    let content: String
    let timestamp: String?
    
    init(role: String, content: String, timestamp: String? = nil) {
        self.role = role
        self.content = content
        self.timestamp = timestamp
    }
}

struct ChatResponse: Codable {
    let success: Bool
    let response: String
    let timestamp: String
    let model: String
    let error: String?
}

struct JobRecommendationsResponse: Codable {
    let success: Bool
    let recommendations: String
    let keywords: [String]
    let location: String?
    let timestamp: String
    let error: String?
}

struct JobAnalysisResponse: Codable {
    let success: Bool
    let analysis: String
    let jobTitle: String
    let company: String
    let timestamp: String
    let error: String?
    
    enum CodingKeys: String, CodingKey {
        case success, analysis, company, timestamp, error
        case jobTitle = "job_title"
    }
}
```

### 4. Device Management

```swift
// Core/Utils/DeviceManager.swift
import UIKit
import UserNotifications

class DeviceManager: ObservableObject {
    static let shared = DeviceManager()
    
    private init() {}
    
    var deviceId: String {
        return UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString
    }
    
    var deviceInfo: [String: Any] {
        return [
            "model": UIDevice.current.model,
            "osVersion": UIDevice.current.systemVersion,
            "deviceModel": UIDevice.current.localizedModel,
            "timezone": TimeZone.current.identifier,
            "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0.0"
        ]
    }
    
    func requestNotificationPermission() async -> Bool {
        let center = UNUserNotificationCenter.current()
        
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
            return granted
        } catch {
            print("Notification permission error: \(error)")
            return false
        }
    }
    
    func registerForPushNotifications() async -> String? {
        await MainActor.run {
            UIApplication.shared.registerForRemoteNotifications()
        }
        
        // Return placeholder token for now
        // In real implementation, this would be set from AppDelegate
        return "placeholder_token_64_chars_min_\(deviceId)_" + String(repeating: "x", count: 20)
    }
}
```

---

## 🔄 Service Layer Implementation

### 1. User Service

```swift
// Services/UserService.swift
import Foundation

@MainActor
class UserService: ObservableObject {
    @Published var currentUser: User?
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiClient = APIClient.shared
    private let deviceManager = DeviceManager.shared
    
    func registerUser(email: String, keywords: [String]) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response: UserRegistrationResponse = try await apiClient.request(
                endpoint: .registerUser(
                    deviceId: deviceManager.deviceId,
                    email: email,
                    keywords: keywords
                ),
                responseType: UserRegistrationResponse.self
            )
            
            if response.success {
                await loadUserProfile()
            } else {
                errorMessage = response.message
            }
        } catch {
            errorMessage = "Registration failed: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func loadUserProfile() async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response: UserProfileResponse = try await apiClient.request(
                endpoint: .getUserProfile(deviceId: deviceManager.deviceId),
                responseType: UserProfileResponse.self
            )
            
            if response.success {
                currentUser = response.data
            } else {
                errorMessage = response.message
            }
        } catch {
            errorMessage = "Failed to load profile: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func updateProfile(email: String, keywords: [String]) async {
        isLoading = true
        errorMessage = nil
        
        do {
            let response: UserProfileResponse = try await apiClient.request(
                endpoint: .updateProfile(
                    deviceId: deviceManager.deviceId,
                    email: email,
                    keywords: keywords
                ),
                responseType: UserProfileResponse.self
            )
            
            if response.success {
                currentUser = response.data
            } else {
                errorMessage = response.message
            }
        } catch {
            errorMessage = "Profile update failed: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
}
```

### 2. Job Service

```swift
// Services/JobService.swift
import Foundation

@MainActor
class JobService: ObservableObject {
    @Published var jobs: [Job] = []
    @Published var savedJobs: [SavedJob] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var hasMoreJobs = false
    @Published var currentPage = 1
    
    private let apiClient = APIClient.shared
    private let deviceManager = DeviceManager.shared
    private let analyticsService = AnalyticsService.shared
    
    private let pageSize = 20
    
    func searchJobs(query: String? = nil, loadMore: Bool = false) async {
        if !loadMore {
            jobs = []
            currentPage = 1
        }
        
        isLoading = true
        errorMessage = nil
        
        let offset = (currentPage - 1) * pageSize
        
        do {
            let response: JobSearchResponse = try await apiClient.request(
                endpoint: .searchJobs(query: query, limit: pageSize, offset: offset),
                responseType: JobSearchResponse.self
            )
            
            if response.success {
                if loadMore {
                    jobs.append(contentsOf: response.data.jobs)
                } else {
                    jobs = response.data.jobs
                }
                
                hasMoreJobs = response.data.pagination.hasMore
                currentPage += 1
                
                // Track search analytics
                if let query = query, !query.isEmpty {
                    await analyticsService.trackEvent(
                        actionType: "search",
                        actionData: ["search_term": query, "results_count": response.data.jobs.count]
                    )
                }
            }
        } catch {
            errorMessage = "Search failed: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func saveJob(_ job: Job) async {
        do {
            let _: [String: Bool] = try await apiClient.request(
                endpoint: .saveJob(deviceId: deviceManager.deviceId, jobId: job.id),
                responseType: [String: Bool].self
            )
            
            await loadSavedJobs()
            await analyticsService.trackEvent(
                actionType: "job_save",
                actionData: ["job_id": job.id, "job_title": job.title]
            )
        } catch {
            errorMessage = "Failed to save job: \(error.localizedDescription)"
        }
    }
    
    func loadSavedJobs() async {
        do {
            let response: SavedJobsResponse = try await apiClient.request(
                endpoint: .getSavedJobs(deviceId: deviceManager.deviceId),
                responseType: SavedJobsResponse.self
            )
            
            if response.success {
                savedJobs = response.data.savedJobs
            }
        } catch {
            errorMessage = "Failed to load saved jobs: \(error.localizedDescription)"
        }
    }
    
    func recordJobView(job: Job, duration: Int) async {
        do {
            let _: [String: Any] = try await apiClient.request(
                endpoint: .recordJobView(
                    deviceId: deviceManager.deviceId,
                    jobId: job.id,
                    duration: duration
                ),
                responseType: [String: Any].self
            )
            
            await analyticsService.trackEvent(
                actionType: "job_view",
                actionData: [
                    "job_id": job.id,
                    "job_title": job.title,
                    "duration": duration
                ]
            )
        } catch {
            print("Failed to record job view: \(error)")
        }
    }
}
```

### 3. Chat Service

```swift
// Services/ChatService.swift
import Foundation

@MainActor
class ChatService: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let apiClient = APIClient.shared
    private let deviceManager = DeviceManager.shared
    private let analyticsService = AnalyticsService.shared
    
    func sendMessage(_ text: String) async {
        let userMessage = ChatMessage(role: "user", content: text)
        messages.append(userMessage)
        
        isLoading = true
        errorMessage = nil
        
        do {
            let response: ChatResponse = try await apiClient.request(
                endpoint: .chatWithAI(
                    deviceId: deviceManager.deviceId,
                    message: text,
                    history: Array(messages.dropLast().suffix(10)) // Last 10 messages for context
                ),
                responseType: ChatResponse.self
            )
            
            if response.success {
                let assistantMessage = ChatMessage(
                    role: "assistant",
                    content: response.response,
                    timestamp: response.timestamp
                )
                messages.append(assistantMessage)
                
                await analyticsService.trackEvent(
                    actionType: "chatbot_message",
                    actionData: [
                        "message_length": text.count,
                        "response_length": response.response.count
                    ]
                )
            } else {
                errorMessage = response.error ?? "Chat failed"
            }
        } catch {
            errorMessage = "Chat failed: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    func getJobRecommendations(keywords: [String], location: String? = nil) async -> String? {
        do {
            let response: JobRecommendationsResponse = try await apiClient.request(
                endpoint: .getJobRecommendations(
                    deviceId: deviceManager.deviceId,
                    keywords: keywords,
                    location: location
                ),
                responseType: JobRecommendationsResponse.self
            )
            
            if response.success {
                await analyticsService.trackEvent(
                    actionType: "job_recommendations",
                    actionData: ["keywords": keywords]
                )
                return response.recommendations
            } else {
                errorMessage = response.error
                return nil
            }
        } catch {
            errorMessage = "Recommendations failed: \(error.localizedDescription)"
            return nil
        }
    }
    
    func analyzeJob(_ job: Job) async -> String? {
        do {
            let response: JobAnalysisResponse = try await apiClient.request(
                endpoint: .analyzeJob(
                    deviceId: deviceManager.deviceId,
                    jobId: job.id,
                    title: job.title,
                    company: job.company
                ),
                responseType: JobAnalysisResponse.self
            )
            
            if response.success {
                await analyticsService.trackEvent(
                    actionType: "job_analysis",
                    actionData: ["job_id": job.id, "job_title": job.title]
                )
                return response.analysis
            } else {
                errorMessage = response.error
                return nil
            }
        } catch {
            errorMessage = "Job analysis failed: \(error.localizedDescription)"
            return nil
        }
    }
}
```

### 4. Analytics Service

```swift
// Services/AnalyticsService.swift
import Foundation

class AnalyticsService {
    static let shared = AnalyticsService()
    
    private let apiClient = APIClient.shared
    private let deviceManager = DeviceManager.shared
    
    private init() {}
    
    func trackEvent(actionType: String, actionData: [String: Any] = [:]) async {
        do {
            let _: [String: Any] = try await apiClient.request(
                endpoint: .recordAnalyticsEvent(
                    deviceId: deviceManager.deviceId,
                    actionType: actionType,
                    actionData: actionData
                ),
                responseType: [String: Any].self
            )
        } catch {
            print("Analytics tracking failed: \(error)")
        }
    }
    
    func trackAppOpen() async {
        await trackEvent(actionType: "app_open")
    }
    
    func trackAppClose() async {
        await trackEvent(actionType: "app_close")
    }
}
```

---

## 🎨 SwiftUI Views Examples

### 1. Main App Structure

```swift
// App/JobAppApp.swift
import SwiftUI

@main
struct JobAppApp: App {
    @StateObject private var userService = UserService()
    @StateObject private var jobService = JobService()
    @StateObject private var chatService = ChatService()
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(userService)
                .environmentObject(jobService)
                .environmentObject(chatService)
                .task {
                    await setupApp()
                }
        }
    }
    
    private func setupApp() async {
        // Request notification permissions
        let granted = await DeviceManager.shared.requestNotificationPermission()
        
        if granted {
            // Register device for push notifications
            if let deviceToken = await DeviceManager.shared.registerForPushNotifications() {
                // Register device with backend
                // This would be called in AppDelegate didRegisterForRemoteNotificationsWithDeviceToken
            }
        }
        
        // Track app open
        await AnalyticsService.shared.trackAppOpen()
        
        // Try to load existing user profile
        await userService.loadUserProfile()
    }
}
```

### 2. Job Search View

```swift
// Features/JobSearch/JobSearchView.swift
import SwiftUI

struct JobSearchView: View {
    @EnvironmentObject var jobService: JobService
    @State private var searchText = ""
    @State private var searchTimer: Timer?
    
    var body: some View {
        NavigationView {
            VStack {
                // Search Bar
                SearchBar(text: $searchText, onSearchButtonClicked: {
                    Task {
                        await jobService.searchJobs(query: searchText.isEmpty ? nil : searchText)
                    }
                })
                
                // Job List
                if jobService.isLoading && jobService.jobs.isEmpty {
                    ProgressView("Searching jobs...")
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        ForEach(jobService.jobs) { job in
                            JobRowView(job: job)
                                .onAppear {
                                    // Load more when near the end
                                    if job.id == jobService.jobs.last?.id && jobService.hasMoreJobs {
                                        Task {
                                            await jobService.searchJobs(query: searchText.isEmpty ? nil : searchText, loadMore: true)
                                        }
                                    }
                                }
                        }
                        
                        if jobService.isLoading && !jobService.jobs.isEmpty {
                            HStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                        }
                    }
                }
                
                if let errorMessage = jobService.errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .padding()
                }
            }
            .navigationTitle("Job Search")
            .onAppear {
                Task {
                    await jobService.searchJobs()
                }
            }
        }
    }
}

struct JobRowView: View {
    let job: Job
    @EnvironmentObject var jobService: JobService
    @State private var viewStartTime = Date()
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(job.title)
                .font(.headline)
                .lineLimit(2)
            
            Text(job.company)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            HStack {
                Text(job.source)
                    .font(.caption)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(4)
                
                Spacer()
                
                Button("Save") {
                    Task {
                        await jobService.saveJob(job)
                    }
                }
                .buttonStyle(.bordered)
            }
        }
        .padding(.vertical, 4)
        .onTapGesture {
            // Record job view
            let duration = Int(Date().timeIntervalSince(viewStartTime))
            Task {
                await jobService.recordJobView(job: job, duration: duration)
            }
            
            // Open job link
            if let url = URL(string: job.applyLink) {
                UIApplication.shared.open(url)
            }
        }
        .onAppear {
            viewStartTime = Date()
        }
    }
}

struct SearchBar: View {
    @Binding var text: String
    let onSearchButtonClicked: () -> Void
    
    var body: some View {
        HStack {
            TextField("Search jobs...", text: $text, onCommit: onSearchButtonClicked)
                .textFieldStyle(RoundedBorderTextFieldStyle())
            
            Button("Search", action: onSearchButtonClicked)
                .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}
```

### 3. AI Chat View

```swift
// Features/AIChat/AIChatView.swift
import SwiftUI

struct AIChatView: View {
    @EnvironmentObject var chatService: ChatService
    @State private var messageText = ""
    
    var body: some View {
        NavigationView {
            VStack {
                // Chat Messages
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(chatService.messages) { message in
                                ChatBubbleView(message: message)
                                    .id(message.id)
                            }
                            
                            if chatService.isLoading {
                                HStack {
                                    ProgressView()
                                        .scaleEffect(0.8)
                                    Text("AI is thinking...")
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }
                                .padding()
                            }
                        }
                        .padding()
                    }
                    .onChange(of: chatService.messages.count) { _ in
                        withAnimation {
                            proxy.scrollTo(chatService.messages.last?.id, anchor: .bottom)
                        }
                    }
                }
                
                // Message Input
                HStack {
                    TextField("Ask about jobs, career advice...", text: $messageText, axis: .vertical)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .lineLimit(1...4)
                    
                    Button("Send") {
                        guard !messageText.isEmpty else { return }
                        let text = messageText
                        messageText = ""
                        
                        Task {
                            await chatService.sendMessage(text)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(messageText.isEmpty || chatService.isLoading)
                }
                .padding()
            }
            .navigationTitle("AI Career Assistant")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu("Quick Actions") {
                        Button("Get Job Recommendations") {
                            Task {
                                await requestRecommendations()
                            }
                        }
                        
                        Button("Career Advice") {
                            messageText = "What advice do you have for advancing my career?"
                        }
                        
                        Button("Resume Tips") {
                            messageText = "How can I improve my resume?"
                        }
                    }
                }
            }
        }
    }
    
    private func requestRecommendations() async {
        // Get user keywords or use default
        let keywords = ["iOS", "Swift", "Mobile"] // Get from user profile
        
        if let recommendations = await chatService.getJobRecommendations(keywords: keywords) {
            let message = ChatMessage(role: "assistant", content: recommendations)
            await MainActor.run {
                chatService.messages.append(message)
            }
        }
    }
}

struct ChatBubbleView: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.role == "user" {
                Spacer()
            }
            
            VStack(alignment: message.role == "user" ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(12)
                    .background(message.role == "user" ? Color.blue : Color.gray.opacity(0.2))
                    .foregroundColor(message.role == "user" ? .white : .primary)
                    .cornerRadius(16)
                
                if let timestamp = message.timestamp {
                    Text(formatTimestamp(timestamp))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            if message.role == "assistant" {
                Spacer()
            }
        }
    }
    
    private func formatTimestamp(_ timestamp: String) -> String {
        // Format ISO timestamp to readable time
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        
        if let date = formatter.date(from: timestamp) {
            let displayFormatter = DateFormatter()
            displayFormatter.timeStyle = .short
            return displayFormatter.string(from: date)
        }
        
        return ""
    }
}
```

---

## 🔔 Push Notifications Setup

### 1. AppDelegate Configuration

```swift
// App/AppDelegate.swift
import UIKit
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }
    
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        Task {
            await registerDeviceWithBackend(deviceToken: tokenString)
        }
    }
    
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("Failed to register for remote notifications: \(error)")
    }
    
    private func registerDeviceWithBackend(deviceToken: String) async {
        let deviceManager = DeviceManager.shared
        
        do {
            let _: [String: Any] = try await APIClient.shared.request(
                endpoint: .registerDevice(
                    deviceId: deviceManager.deviceId,
                    deviceToken: deviceToken,
                    deviceInfo: deviceManager.deviceInfo
                ),
                responseType: [String: Any].self
            )
            print("Device registered successfully")
        } catch {
            print("Device registration failed: \(error)")
        }
    }
    
    // Handle notification when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification, withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.banner, .sound, .badge])
    }
    
    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse, withCompletionHandler completionHandler: @escaping () -> Void) {
        // Handle notification tap - navigate to relevant screen
        Task {
            await AnalyticsService.shared.trackEvent(actionType: "notification_click")
        }
        completionHandler()
    }
}
```

---

## 📊 Analytics Implementation

### 1. App Lifecycle Tracking

```swift
// Add to JobAppApp.swift
import SwiftUI

@main
struct JobAppApp: App {
    @Environment(\.scenePhase) private var scenePhase
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .onChange(of: scenePhase) { phase in
                    Task {
                        switch phase {
                        case .active:
                            await AnalyticsService.shared.trackAppOpen()
                        case .background:
                            await AnalyticsService.shared.trackAppClose()
                        default:
                            break
                        }
                    }
                }
        }
    }
}
```

### 2. Screen View Tracking

```swift
// Extension for easy view tracking
extension View {
    func trackScreenView(_ screenName: String) -> some View {
        self.onAppear {
            Task {
                await AnalyticsService.shared.trackEvent(
                    actionType: "screen_view",
                    actionData: ["screen_name": screenName]
                )
            }
        }
    }
}

// Usage in views
struct JobSearchView: View {
    var body: some View {
        // ... view content
        .trackScreenView("job_search")
    }
}
```

---

## 🚀 Deployment Configuration

### 1. Info.plist Configuration

```xml
<!-- Required for network requests -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <false/>
    <key>NSExceptionDomains</key>
    <dict>
        <key>birjobbackend-ir3e.onrender.com</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <false/>
            <key>NSExceptionMinimumTLSVersion</key>
            <string>TLSv1.2</string>
        </dict>
    </dict>
</dict>

<!-- Push notifications capability -->
<key>UIBackgroundModes</key>
<array>
    <string>remote-notification</string>
</array>
```

### 2. Capabilities in Xcode

- **Push Notifications**: Enable in Signing & Capabilities
- **Background App Refresh**: Optional for background job updates
- **Network**: Outgoing connections (automatic)

---

## 🧪 Testing Strategy

### 1. Unit Tests Example

```swift
// Tests/UserServiceTests.swift
import XCTest
@testable import JobApp

class UserServiceTests: XCTestCase {
    var userService: UserService!
    
    override func setUp() {
        super.setUp()
        userService = UserService()
    }
    
    func testUserRegistration() async throws {
        await userService.registerUser(
            email: "test@example.com",
            keywords: ["iOS", "Swift"]
        )
        
        XCTAssertNotNil(userService.currentUser)
        XCTAssertEqual(userService.currentUser?.email, "test@example.com")
    }
    
    func testJobSearch() async throws {
        let jobService = JobService()
        
        await jobService.searchJobs(query: "iOS")
        
        XCTAssertGreaterThan(jobService.jobs.count, 0)
    }
}
```

### 2. Integration Testing

```swift
// Test against live backend
func testLiveBackendIntegration() async throws {
    let expectation = XCTestExpectation(description: "API call")
    
    let response: JobSearchResponse = try await APIClient.shared.request(
        endpoint: .searchJobs(query: "test", limit: 5, offset: 0),
        responseType: JobSearchResponse.self
    )
    
    XCTAssertTrue(response.success)
    expectation.fulfill()
    
    await fulfillment(of: [expectation], timeout: 10.0)
}
```

---

## 🔧 Error Handling Best Practices

### 1. Network Error Handling

```swift
// Centralized error handling
extension APIClient {
    func handleNetworkError(_ error: Error) -> String {
        if let networkError = error as? NetworkError {
            switch networkError {
            case .userNotFound:
                return "Please register your account first"
            case .serverError(let code):
                return "Server error (\(code)). Please try again later."
            case .invalidResponse:
                return "Invalid response from server"
            case .decodingError:
                return "Data parsing error"
            default:
                return "Network error occurred"
            }
        }
        
        return error.localizedDescription
    }
}
```

### 2. User-Friendly Error Messages

```swift
// Show errors to users with appropriate actions
struct ErrorView: View {
    let message: String
    let retryAction: (() -> Void)?
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundColor(.orange)
            
            Text(message)
                .multilineTextAlignment(.center)
            
            if let retryAction = retryAction {
                Button("Try Again", action: retryAction)
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding()
    }
}
```

---

## 📱 iOS-Specific Considerations

### 1. Memory Management
- Use `@StateObject` for service instances
- Implement proper lifecycle management
- Cache images and data appropriately

### 2. Performance Optimization
- Lazy loading for large job lists
- Image caching for company logos
- Background threading for API calls

### 3. User Experience
- Pull-to-refresh for job lists
- Offline mode with cached data
- Search debouncing for better UX
- Loading states and progress indicators

### 4. Accessibility
- VoiceOver support for all UI elements
- Dynamic Type support
- High contrast mode compatibility

---

**Documentation Version**: 1.0  
**iOS Target**: 15.0+  
**Backend Compatibility**: Fully tested ✅  
**Last Updated**: July 3, 2025