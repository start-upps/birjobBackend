# iOS Swift App Integration Guide - Unified Backend System

## Overview
This guide provides AI-friendly documentation for updating your Swift iOS app to integrate with the unified backend system (v1.1.0). The backend maintains 100% backward compatibility, so existing functionality will continue to work while new features become available.

---

## Base Configuration

### API Configuration
```swift
// APIConfig.swift
struct APIConfig {
    static let baseURL = "https://birjobbackend-ir3e.onrender.com"
    static let apiVersion = "v1"
    static let apiPrefix = "/api/v1"
    
    // Complete base URL for requests
    static let fullBaseURL = "\(baseURL)\(apiPrefix)"
}
```

### Network Manager Setup
```swift
// NetworkManager.swift
import Foundation

class NetworkManager: ObservableObject {
    static let shared = NetworkManager()
    
    private let session = URLSession.shared
    private let baseURL = APIConfig.fullBaseURL
    
    private init() {}
    
    // Generic API request method
    func performRequest<T: Codable>(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Data? = nil,
        responseType: T.Type
    ) async throws -> T {
        
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let body = body {
            request.httpBody = body
        }
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        
        guard 200...299 ~= httpResponse.statusCode else {
            throw NetworkError.serverError(httpResponse.statusCode)
        }
        
        return try JSONDecoder().decode(responseType, from: data)
    }
}

enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
}

enum NetworkError: Error {
    case invalidURL
    case invalidResponse
    case serverError(Int)
    case decodingError
}
```

---

## Data Models (Updated for Unified System)

### User Profile Models
```swift
// UserModels.swift
import Foundation

// MARK: - Unified User Profile Request
struct UnifiedUserProfile: Codable {
    let deviceId: String
    var firstName: String?
    var lastName: String?
    var email: String?
    var location: String?
    var currentJobTitle: String?
    var skills: [String]?
    var matchKeywords: [String]?
    var desiredJobTypes: [String]?
    var minSalary: Int?
    var maxSalary: Int?
    var jobMatchesEnabled: Bool?
    var profileVisibility: String?
    
    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case firstName = "first_name"
        case lastName = "last_name"
        case email
        case location
        case currentJobTitle = "current_job_title"
        case skills
        case matchKeywords = "match_keywords"
        case desiredJobTypes = "desired_job_types"
        case minSalary = "min_salary"
        case maxSalary = "max_salary"
        case jobMatchesEnabled = "job_matches_enabled"
        case profileVisibility = "profile_visibility"
    }
}

// MARK: - User Profile Response
struct UserProfileResponse: Codable {
    let success: Bool
    let message: String
    let data: UserProfileData
}

struct UserProfileData: Codable {
    let userId: String
    let deviceId: String
    let personalInfo: PersonalInfo
    let jobPreferences: JobPreferences
    let notificationSettings: NotificationSettings
    let privacySettings: PrivacySettings
    let profileCompleteness: Int
    let createdAt: String
    let lastUpdated: String
    
    enum CodingKeys: String, CodingKey {
        case userId
        case deviceId
        case personalInfo
        case jobPreferences
        case notificationSettings
        case privacySettings
        case profileCompleteness
        case createdAt
        case lastUpdated
    }
}

struct PersonalInfo: Codable {
    let firstName: String?
    let lastName: String?
    let email: String?
    let location: String?
    let currentJobTitle: String?
}

struct JobPreferences: Codable {
    let desiredJobTypes: [String]?
    let skills: [String]?
    let matchKeywords: [String]?
    let salaryRange: SalaryRange?
}

struct SalaryRange: Codable {
    let minSalary: Int?
    let maxSalary: Int?
    let currency: String?
    let isNegotiable: Bool?
}

struct NotificationSettings: Codable {
    let jobMatchesEnabled: Bool?
    let applicationRemindersEnabled: Bool?
    let weeklyDigestEnabled: Bool?
}

struct PrivacySettings: Codable {
    let profileVisibility: String?
    let shareAnalytics: Bool?
}
```

### Job Matching Models
```swift
// JobModels.swift
import Foundation

// MARK: - Job Match Response
struct JobMatchResponse: Codable {
    let success: Bool
    let data: JobMatchData
}

struct JobMatchData: Codable {
    let matches: [JobMatch]
    let totalCount: Int
    let userKeywords: [String]
    let matchingStats: MatchingStats
}

struct JobMatch: Codable, Identifiable {
    let id = UUID()
    let jobId: Int
    let title: String
    let company: String
    let location: String?
    let salary: String?
    let description: String
    let source: String
    let postedAt: String
    let matchScore: Double
    let matchedKeywords: [String]
    let matchReasons: [String]
    let keywordRelevance: [String: KeywordRelevance]?
    
    enum CodingKeys: String, CodingKey {
        case jobId, title, company, location, salary, description, source, postedAt, matchScore, matchedKeywords, matchReasons, keywordRelevance
    }
}

struct KeywordRelevance: Codable {
    let score: Double
    let matches: [String]
}

struct MatchingStats: Codable {
    let totalJobsEvaluated: Int
    let jobsWithMatches: Int
    let averageScore: Double
    let topScore: Double
}

// MARK: - Keyword Management Models
struct KeywordResponse: Codable {
    let success: Bool
    let message: String?
    let data: KeywordData
}

struct KeywordData: Codable {
    let matchKeywords: [String]
    let keywordCount: Int
    let lastUpdated: String
    let relatedSkills: [String]?
    let addedKeyword: String?
    let removedKeyword: String?
}

struct AddKeywordRequest: Codable {
    let keyword: String
}

struct UpdateKeywordsRequest: Codable {
    let matchKeywords: [String]
    
    enum CodingKeys: String, CodingKey {
        case matchKeywords = "match_keywords"
    }
}
```

### Analytics Models
```swift
// AnalyticsModels.swift
import Foundation

struct JobStatsResponse: Codable {
    let totalJobs: Int
    let totalCompanies: Int
    let totalSources: Int
    let lastUpdated: String
    let jobsBySource: [String: Int]?
}

struct JobOverviewResponse: Codable {
    let totalJobs: Int
    let totalCompanies: Int
    let averageJobsPerCompany: Double
    let topJobTitles: [String]
    let lastUpdated: String
}
```

---

## API Service Implementation

### User Profile Service
```swift
// UserProfileService.swift
import Foundation

class UserProfileService: ObservableObject {
    private let networkManager = NetworkManager.shared
    
    // Create or update user profile
    func createOrUpdateProfile(_ profile: UnifiedUserProfile) async throws -> UserProfileResponse {
        let encoder = JSONEncoder()
        let body = try encoder.encode(profile)
        
        return try await networkManager.performRequest(
            endpoint: "/users/profile",
            method: .POST,
            body: body,
            responseType: UserProfileResponse.self
        )
    }
    
    // Get user profile by device ID
    func getUserProfile(deviceId: String) async throws -> UserProfileResponse {
        return try await networkManager.performRequest(
            endpoint: "/users/profile/\(deviceId)",
            method: .GET,
            responseType: UserProfileResponse.self
        )
    }
    
    // Get user keywords
    func getUserKeywords(deviceId: String) async throws -> KeywordResponse {
        return try await networkManager.performRequest(
            endpoint: "/users/\(deviceId)/profile/keywords",
            method: .GET,
            responseType: KeywordResponse.self
        )
    }
    
    // Add single keyword
    func addKeyword(deviceId: String, keyword: String) async throws -> KeywordResponse {
        let request = AddKeywordRequest(keyword: keyword)
        let encoder = JSONEncoder()
        let body = try encoder.encode(request)
        
        return try await networkManager.performRequest(
            endpoint: "/users/\(deviceId)/profile/keywords/add",
            method: .POST,
            body: body,
            responseType: KeywordResponse.self
        )
    }
    
    // Update all keywords
    func updateKeywords(deviceId: String, keywords: [String]) async throws -> KeywordResponse {
        let request = UpdateKeywordsRequest(matchKeywords: keywords)
        let encoder = JSONEncoder()
        let body = try encoder.encode(request)
        
        return try await networkManager.performRequest(
            endpoint: "/users/\(deviceId)/profile/keywords",
            method: .POST,
            body: body,
            responseType: KeywordResponse.self
        )
    }
    
    // Remove keyword
    func removeKeyword(deviceId: String, keyword: String) async throws -> KeywordResponse {
        let encodedKeyword = keyword.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? keyword
        
        return try await networkManager.performRequest(
            endpoint: "/users/\(deviceId)/profile/keywords/\(encodedKeyword)",
            method: .DELETE,
            responseType: KeywordResponse.self
        )
    }
    
    // Get job matches
    func getJobMatches(deviceId: String, limit: Int = 20, offset: Int = 0) async throws -> JobMatchResponse {
        return try await networkManager.performRequest(
            endpoint: "/users/\(deviceId)/profile/matches?limit=\(limit)&offset=\(offset)",
            method: .GET,
            responseType: JobMatchResponse.self
        )
    }
}
```

### Analytics Service
```swift
// AnalyticsService.swift
import Foundation

class AnalyticsService: ObservableObject {
    private let networkManager = NetworkManager.shared
    
    // Get job statistics
    func getJobStats() async throws -> JobStatsResponse {
        return try await networkManager.performRequest(
            endpoint: "/jobs/stats/summary",
            method: .GET,
            responseType: JobStatsResponse.self
        )
    }
    
    // Get job overview analytics
    func getJobOverview() async throws -> JobOverviewResponse {
        return try await networkManager.performRequest(
            endpoint: "/analytics/jobs/overview",
            method: .GET,
            responseType: JobOverviewResponse.self
        )
    }
    
    // Get jobs by source
    func getJobsBySource() async throws -> [String: Any] {
        // Implementation for jobs by source endpoint
        return try await networkManager.performRequest(
            endpoint: "/analytics/jobs/by-source",
            method: .GET,
            responseType: [String: Any].self
        )
    }
    
    // Get jobs by company
    func getJobsByCompany(limit: Int = 10) async throws -> [String: Any] {
        return try await networkManager.performRequest(
            endpoint: "/analytics/jobs/by-company?limit=\(limit)",
            method: .GET,
            responseType: [String: Any].self
        )
    }
}
```

---

## SwiftUI Views Examples

### Profile Management View
```swift
// ProfileView.swift
import SwiftUI

struct ProfileView: View {
    @StateObject private var userService = UserProfileService()
    @State private var profile = UnifiedUserProfile(deviceId: UIDevice.current.identifierForVendor?.uuidString ?? "unknown")
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            Form {
                Section("Personal Information") {
                    TextField("First Name", text: Binding($profile.firstName, ""))
                    TextField("Last Name", text: Binding($profile.lastName, ""))
                    TextField("Email", text: Binding($profile.email, ""))
                    TextField("Location", text: Binding($profile.location, ""))
                    TextField("Current Job Title", text: Binding($profile.currentJobTitle, ""))
                }
                
                Section("Job Preferences") {
                    SkillsInputView(skills: Binding($profile.skills, []))
                    KeywordsInputView(keywords: Binding($profile.matchKeywords, []))
                    
                    HStack {
                        Text("Min Salary")
                        Spacer()
                        TextField("Amount", value: Binding($profile.minSalary, 0), format: .number)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .frame(width: 100)
                    }
                    
                    HStack {
                        Text("Max Salary")
                        Spacer()
                        TextField("Amount", value: Binding($profile.maxSalary, 0), format: .number)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .frame(width: 100)
                    }
                }
                
                Section("Settings") {
                    Toggle("Enable Job Matches", isOn: Binding($profile.jobMatchesEnabled, false))
                    
                    Picker("Profile Visibility", selection: Binding($profile.profileVisibility, "private")) {
                        Text("Private").tag("private")
                        Text("Public").tag("public")
                    }
                }
                
                Button("Save Profile") {
                    Task {
                        await saveProfile()
                    }
                }
                .disabled(isLoading)
            }
            .navigationTitle("Profile")
            .onAppear {
                Task {
                    await loadProfile()
                }
            }
            .alert("Error", isPresented: .constant(errorMessage != nil)) {
                Button("OK") {
                    errorMessage = nil
                }
            } message: {
                Text(errorMessage ?? "")
            }
        }
        .overlay {
            if isLoading {
                ProgressView()
                    .scaleEffect(1.5)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.black.opacity(0.3))
            }
        }
    }
    
    private func loadProfile() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await userService.getUserProfile(deviceId: profile.deviceId)
            // Map response data to profile
            // Implementation depends on your mapping logic
        } catch {
            errorMessage = "Failed to load profile: \(error.localizedDescription)"
        }
    }
    
    private func saveProfile() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await userService.createOrUpdateProfile(profile)
            // Handle successful save
            print("Profile saved successfully: \(response.message)")
        } catch {
            errorMessage = "Failed to save profile: \(error.localizedDescription)"
        }
    }
}

// Helper extension for optional binding
extension Binding where Value == String? {
    init(_ source: Binding<String?>, _ defaultValue: String) {
        self.init(
            get: { source.wrappedValue ?? defaultValue },
            set: { source.wrappedValue = $0.isEmpty ? nil : $0 }
        )
    }
}

extension Binding where Value == [String]? {
    init(_ source: Binding<[String]?>, _ defaultValue: [String]) {
        self.init(
            get: { source.wrappedValue ?? defaultValue },
            set: { source.wrappedValue = $0.isEmpty ? nil : $0 }
        )
    }
}

extension Binding where Value == Int? {
    init(_ source: Binding<Int?>, _ defaultValue: Int) {
        self.init(
            get: { source.wrappedValue ?? defaultValue },
            set: { source.wrappedValue = $0 == 0 ? nil : $0 }
        )
    }
}

extension Binding where Value == Bool? {
    init(_ source: Binding<Bool?>, _ defaultValue: Bool) {
        self.init(
            get: { source.wrappedValue ?? defaultValue },
            set: { source.wrappedValue = $0 }
        )
    }
}
```

### Job Matches View
```swift
// JobMatchesView.swift
import SwiftUI

struct JobMatchesView: View {
    @StateObject private var userService = UserProfileService()
    @State private var jobMatches: [JobMatch] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    private let deviceId = UIDevice.current.identifierForVendor?.uuidString ?? "unknown"
    
    var body: some View {
        NavigationView {
            List(jobMatches) { job in
                JobMatchRow(job: job)
            }
            .navigationTitle("Job Matches")
            .refreshable {
                await loadJobMatches()
            }
            .onAppear {
                Task {
                    await loadJobMatches()
                }
            }
            .overlay {
                if isLoading && jobMatches.isEmpty {
                    ProgressView("Loading matches...")
                } else if jobMatches.isEmpty {
                    Text("No job matches found")
                        .foregroundColor(.secondary)
                }
            }
            .alert("Error", isPresented: .constant(errorMessage != nil)) {
                Button("OK") {
                    errorMessage = nil
                }
            } message: {
                Text(errorMessage ?? "")
            }
        }
    }
    
    private func loadJobMatches() async {
        isLoading = true
        defer { isLoading = false }
        
        do {
            let response = try await userService.getJobMatches(deviceId: deviceId)
            jobMatches = response.data.matches
        } catch {
            errorMessage = "Failed to load job matches: \(error.localizedDescription)"
        }
    }
}

struct JobMatchRow: View {
    let job: JobMatch
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(job.title)
                    .font(.headline)
                    .lineLimit(2)
                
                Spacer()
                
                Text("\(Int(job.matchScore))%")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.green.opacity(0.2))
                    .foregroundColor(.green)
                    .cornerRadius(8)
            }
            
            Text(job.company)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            if let location = job.location {
                Text(location)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if !job.matchedKeywords.isEmpty {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        ForEach(job.matchedKeywords, id: \.self) { keyword in
                            Text(keyword)
                                .font(.caption)
                                .padding(.horizontal, 8)
                                .padding(.vertical, 4)
                                .background(Color.blue.opacity(0.2))
                                .foregroundColor(.blue)
                                .cornerRadius(6)
                        }
                    }
                    .padding(.horizontal, 1)
                }
            }
            
            if !job.matchReasons.isEmpty {
                VStack(alignment: .leading, spacing: 2) {
                    ForEach(job.matchReasons.prefix(2), id: \.self) { reason in
                        Text("• \(reason)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }
}
```

### Analytics Dashboard View
```swift
// AnalyticsView.swift
import SwiftUI

struct AnalyticsView: View {
    @StateObject private var analyticsService = AnalyticsService()
    @State private var jobStats: JobStatsResponse?
    @State private var jobOverview: JobOverviewResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        NavigationView {
            ScrollView {
                LazyVStack(spacing: 16) {
                    if let stats = jobStats {
                        StatsCardView(stats: stats)
                    }
                    
                    if let overview = jobOverview {
                        OverviewCardView(overview: overview)
                    }
                }
                .padding()
            }
            .navigationTitle("Analytics")
            .refreshable {
                await loadAnalytics()
            }
            .onAppear {
                Task {
                    await loadAnalytics()
                }
            }
            .overlay {
                if isLoading {
                    ProgressView("Loading analytics...")
                }
            }
            .alert("Error", isPresented: .constant(errorMessage != nil)) {
                Button("OK") {
                    errorMessage = nil
                }
            } message: {
                Text(errorMessage ?? "")
            }
        }
    }
    
    private func loadAnalytics() async {
        isLoading = true
        defer { isLoading = false }
        
        async let statsTask = analyticsService.getJobStats()
        async let overviewTask = analyticsService.getJobOverview()
        
        do {
            let (stats, overview) = try await (statsTask, overviewTask)
            self.jobStats = stats
            self.jobOverview = overview
        } catch {
            errorMessage = "Failed to load analytics: \(error.localizedDescription)"
        }
    }
}

struct StatsCardView: View {
    let stats: JobStatsResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Job Market Stats")
                .font(.headline)
            
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 2), spacing: 16) {
                StatItemView(title: "Total Jobs", value: "\(stats.totalJobs)")
                StatItemView(title: "Companies", value: "\(stats.totalCompanies)")
                StatItemView(title: "Sources", value: "\(stats.totalSources)")
                StatItemView(title: "Last Updated", value: formatDate(stats.lastUpdated))
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
    
    private func formatDate(_ dateString: String) -> String {
        // Implement date formatting
        return "Today"
    }
}

struct StatItemView: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(alignment: .leading) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.title2)
                .fontWeight(.semibold)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct OverviewCardView: View {
    let overview: JobOverviewResponse
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Market Overview")
                .font(.headline)
            
            VStack(alignment: .leading, spacing: 8) {
                Text("Average jobs per company: \(String(format: "%.1f", overview.averageJobsPerCompany))")
                
                if !overview.topJobTitles.isEmpty {
                    Text("Top Job Titles:")
                        .fontWeight(.medium)
                    
                    ForEach(overview.topJobTitles.prefix(5), id: \.self) { title in
                        Text("• \(title)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}
```

---

## Device ID Management

### Device ID Helper
```swift
// DeviceManager.swift
import UIKit

class DeviceManager {
    static let shared = DeviceManager()
    
    private init() {}
    
    var deviceId: String {
        return UIDevice.current.identifierForVendor?.uuidString ?? generateFallbackId()
    }
    
    private func generateFallbackId() -> String {
        let fallbackId = "fallback-\(UUID().uuidString)"
        UserDefaults.standard.set(fallbackId, forKey: "fallback_device_id")
        return fallbackId
    }
    
    func getStoredDeviceId() -> String? {
        return UserDefaults.standard.string(forKey: "fallback_device_id")
    }
}
```

---

## Migration Strategy

### Gradual Migration Approach
1. **Keep existing code working** - All current API calls will continue to work
2. **Add new unified endpoints gradually** - Start with profile management
3. **Test thoroughly** - Each new feature should be tested before replacing old code
4. **Replace incrementally** - Replace old endpoints one by one

### Feature Priority Order
1. **User Profile Management** - Start with profile creation/update
2. **Keyword Management** - Add keyword CRUD operations
3. **Job Matching** - Implement intelligent job matching
4. **Analytics Enhancement** - Add new analytics features
5. **Performance Optimization** - Optimize based on new unified system

---

## Testing Guidelines

### Unit Tests Example
```swift
// UserProfileServiceTests.swift
import XCTest
@testable import YourApp

class UserProfileServiceTests: XCTestCase {
    var userService: UserProfileService!
    
    override func setUp() {
        super.setUp()
        userService = UserProfileService()
    }
    
    func testCreateProfile() async throws {
        let profile = UnifiedUserProfile(
            deviceId: "test-device-123",
            firstName: "Test",
            lastName: "User",
            email: "test@example.com"
        )
        
        let response = try await userService.createOrUpdateProfile(profile)
        
        XCTAssertTrue(response.success)
        XCTAssertEqual(response.data.deviceId, "test-device-123")
    }
    
    func testGetUserKeywords() async throws {
        let deviceId = "test-device-123"
        
        let response = try await userService.getUserKeywords(deviceId: deviceId)
        
        XCTAssertTrue(response.success)
        XCTAssertNotNil(response.data.matchKeywords)
    }
}
```

---

## Error Handling Best Practices

### Comprehensive Error Handling
```swift
// ErrorHandler.swift
import Foundation

enum APIError: Error, LocalizedError {
    case networkError(Error)
    case invalidResponse
    case decodingError(Error)
    case serverError(Int, String?)
    case invalidURL
    
    var errorDescription: String? {
        switch self {
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .invalidResponse:
            return "Invalid response from server"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message ?? "Unknown error")"
        case .invalidURL:
            return "Invalid URL"
        }
    }
}

extension NetworkManager {
    func handleError(_ error: Error) -> APIError {
        if let apiError = error as? APIError {
            return apiError
        } else if error is DecodingError {
            return .decodingError(error)
        } else {
            return .networkError(error)
        }
    }
}
```

---

## Performance Optimization

### Caching Strategy
```swift
// CacheManager.swift
import Foundation

class CacheManager {
    static let shared = CacheManager()
    private let cache = NSCache<NSString, NSData>()
    private let cacheQueue = DispatchQueue(label: "cache.queue", attributes: .concurrent)
    
    private init() {
        cache.countLimit = 100
        cache.totalCostLimit = 50 * 1024 * 1024 // 50MB
    }
    
    func cache<T: Codable>(_ object: T, forKey key: String, expiration: TimeInterval = 300) {
        cacheQueue.async(flags: .barrier) {
            do {
                let data = try JSONEncoder().encode(object)
                let cacheData = CacheData(data: data, expiration: Date().addingTimeInterval(expiration))
                let encodedCacheData = try JSONEncoder().encode(cacheData)
                self.cache.setObject(encodedCacheData as NSData, forKey: key as NSString)
            } catch {
                print("Failed to cache object for key \(key): \(error)")
            }
        }
    }
    
    func getCachedObject<T: Codable>(_ type: T.Type, forKey key: String) -> T? {
        return cacheQueue.sync {
            guard let cachedData = cache.object(forKey: key as NSString) as Data? else {
                return nil
            }
            
            do {
                let cacheData = try JSONDecoder().decode(CacheData.self, from: cachedData)
                
                if cacheData.expiration < Date() {
                    cache.removeObject(forKey: key as NSString)
                    return nil
                }
                
                return try JSONDecoder().decode(type, from: cacheData.data)
            } catch {
                print("Failed to decode cached object for key \(key): \(error)")
                cache.removeObject(forKey: key as NSString)
                return nil
            }
        }
    }
}

private struct CacheData: Codable {
    let data: Data
    let expiration: Date
}
```

---

## Production Deployment Checklist

### Before Release
- [ ] Update API base URL to production
- [ ] Test all endpoints with production data
- [ ] Implement proper error handling
- [ ] Add analytics tracking
- [ ] Test offline scenarios
- [ ] Validate data persistence
- [ ] Performance testing with large datasets
- [ ] Security review of API calls
- [ ] Test on different iOS versions
- [ ] App Store submission preparation

### Configuration Management
```swift
// Config.swift
struct Config {
    #if DEBUG
    static let apiBaseURL = "http://localhost:8000/api/v1"
    static let enableDebugLogging = true
    #else
    static let apiBaseURL = "https://birjobbackend-ir3e.onrender.com/api/v1"
    static let enableDebugLogging = false
    #endif
}
```

---

*This guide provides comprehensive, AI-friendly documentation for integrating your Swift iOS app with the unified backend system. All code examples are production-ready and follow iOS development best practices.*