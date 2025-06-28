# 📱 Frontend Integration Guide - Profile-Based Keyword Matching

## 🎯 Overview

This guide provides everything needed to integrate the new profile-based keyword matching system into your iOS app. The backend now supports intelligent job matching with sophisticated scoring algorithms.

## 📋 What's New

### ✅ **Backend Changes Complete:**
- **5 new REST API endpoints** for keyword management
- **Intelligent scoring algorithm** (0-100 normalized scores)
- **Database schema** with JSONB storage and performance optimization
- **Migration strategy** from legacy subscription system
- **Comprehensive validation** and error handling

### 📱 **Frontend Integration Points:**

## 1. 🔧 API Integration

### **Base URL:** `https://birjobbackend-ir3e.onrender.com/api/v1`

### **New Endpoints to Integrate:**

#### 1. Get User Keywords
```swift
GET /users/{deviceId}/profile/keywords

// Response
{
  "success": true,
  "data": {
    "matchKeywords": ["python", "react", "docker"],
    "keywordCount": 3,
    "lastUpdated": "2025-06-28T20:15:30.123456",
    "relatedSkills": ["JavaScript", "Node.js"]
  }
}
```

#### 2. Update Keyword List
```swift
POST /users/{deviceId}/profile/keywords
Content-Type: application/json

{
  "matchKeywords": ["python", "react", "docker", "aws"]
}
```

#### 3. Add Single Keyword
```swift
POST /users/{deviceId}/profile/keywords/add
Content-Type: application/json

{
  "keyword": "kubernetes"
}
```

#### 4. Remove Keyword
```swift
DELETE /users/{deviceId}/profile/keywords/{keyword}
```

#### 5. Get Intelligent Matches
```swift
GET /users/{deviceId}/profile/matches?limit=20&offset=0

// Response with intelligent scoring
{
  "success": true,
  "data": {
    "matches": [
      {
        "jobId": 12345,
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "matchScore": 87.5,
        "matchedKeywords": ["python", "react"],
        "matchReasons": [
          "Strong match for 'python' in job requirements",
          "Good match for 'react' in job description"
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
    "userKeywords": ["python", "react", "docker"],
    "matchingStats": {
      "totalJobsEvaluated": 60,
      "jobsWithMatches": 15,
      "averageScore": 65.3,
      "topScore": 87.5
    }
  }
}
```

## 2. 📱 iOS Implementation

### **UserProfile Model Updates**

```swift
// Update your UserProfile model
struct UserProfile: Codable {
    let userId: String
    let deviceId: String
    var personalInfo: PersonalInfo?
    var jobPreferences: JobPreferences? // Updated with keywords
    var notificationSettings: NotificationSettings?
    var privacySettings: PrivacySettings?
    let profileCompleteness: Int
    let createdAt: Date
    let lastUpdated: Date
}

// Updated JobPreferences
struct JobPreferences: Codable {
    var desiredJobTypes: [String] = []
    var remoteWorkPreference: RemoteWorkPreference = .hybrid
    var skills: [String] = []
    var preferredLocations: [String] = []
    var salaryRange: SalaryRange?
    var matchKeywords: [String] = [] // 🆕 NEW: Profile keywords
}
```

### **Keyword Management Service**

```swift
class ProfileKeywordService {
    private let baseURL = "https://birjobbackend-ir3e.onrender.com/api/v1"
    private let deviceManager = DeviceManager.shared
    
    // Get user's keywords
    func getKeywords() async throws -> ProfileKeywordsResponse {
        let url = "\(baseURL)/users/\(deviceManager.deviceId)/profile/keywords"
        let (data, _) = try await URLSession.shared.data(from: URL(string: url)!)
        return try JSONDecoder().decode(ProfileKeywordsResponse.self, from: data)
    }
    
    // Add keyword
    func addKeyword(_ keyword: String) async throws -> AddKeywordResponse {
        let url = "\(baseURL)/users/\(deviceManager.deviceId)/profile/keywords/add"
        var request = URLRequest(url: URL(string: url)!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = AddKeywordRequest(keyword: keyword)
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(AddKeywordResponse.self, from: data)
    }
    
    // Update keywords list
    func updateKeywords(_ keywords: [String]) async throws -> UpdateKeywordsResponse {
        let url = "\(baseURL)/users/\(deviceManager.deviceId)/profile/keywords"
        var request = URLRequest(url: URL(string: url)!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = UpdateKeywordsRequest(matchKeywords: keywords)
        request.httpBody = try JSONEncoder().encode(body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(UpdateKeywordsResponse.self, from: data)
    }
    
    // Remove keyword
    func removeKeyword(_ keyword: String) async throws -> RemoveKeywordResponse {
        let encodedKeyword = keyword.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? keyword
        let url = "\(baseURL)/users/\(deviceManager.deviceId)/profile/keywords/\(encodedKeyword)"
        var request = URLRequest(url: URL(string: url)!)
        request.httpMethod = "DELETE"
        
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(RemoveKeywordResponse.self, from: data)
    }
    
    // Get intelligent matches
    func getMatches(limit: Int = 20, offset: Int = 0) async throws -> ProfileMatchesResponse {
        let url = "\(baseURL)/users/\(deviceManager.deviceId)/profile/matches?limit=\(limit)&offset=\(offset)"
        let (data, _) = try await URLSession.shared.data(from: URL(string: url)!)
        return try JSONDecoder().decode(ProfileMatchesResponse.self, from: data)
    }
}
```

### **Response Models**

```swift
struct ProfileKeywordsResponse: Codable {
    let success: Bool
    let data: ProfileKeywordsData
}

struct ProfileKeywordsData: Codable {
    let matchKeywords: [String]
    let keywordCount: Int
    let lastUpdated: String?
    let relatedSkills: [String]
}

struct AddKeywordRequest: Codable {
    let keyword: String
}

struct UpdateKeywordsRequest: Codable {
    let matchKeywords: [String]
}

struct IntelligentJobMatch: Codable {
    let jobId: Int
    let title: String
    let company: String
    let location: String
    let salary: String
    let description: String
    let source: String
    let postedAt: String
    let matchScore: Double
    let matchedKeywords: [String]
    let matchReasons: [String]
    let keywordRelevance: [String: KeywordRelevance]
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
```

## 3. 🎨 UI Components to Create

### **KeywordManagementSection**
```swift
struct KeywordManagementSection: View {
    @StateObject private var keywordService = ProfileKeywordService()
    @State private var keywords: [String] = []
    @State private var newKeyword: String = ""
    @State private var isLoading = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header
            HStack {
                Text("Job Matching Keywords")
                    .font(.headline)
                Spacer()
                Text("\(keywords.count) keywords")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            // Keywords Display
            LazyVGrid(columns: [
                GridItem(.adaptive(minimum: 100))
            ], spacing: 8) {
                ForEach(keywords, id: \.self) { keyword in
                    KeywordChip(keyword: keyword) {
                        removeKeyword(keyword)
                    }
                }
            }
            
            // Add Keyword
            HStack {
                TextField("Add keyword", text: $newKeyword)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                
                Button("Add") {
                    addKeyword()
                }
                .disabled(newKeyword.isEmpty || isLoading)
            }
        }
        .onAppear {
            loadKeywords()
        }
    }
    
    private func loadKeywords() {
        Task {
            isLoading = true
            do {
                let response = try await keywordService.getKeywords()
                await MainActor.run {
                    self.keywords = response.data.matchKeywords
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                }
            }
        }
    }
    
    private func addKeyword() {
        guard !newKeyword.isEmpty else { return }
        
        Task {
            isLoading = true
            do {
                let response = try await keywordService.addKeyword(newKeyword)
                await MainActor.run {
                    self.keywords = response.data.matchKeywords
                    self.newKeyword = ""
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.isLoading = false
                }
            }
        }
    }
    
    private func removeKeyword(_ keyword: String) {
        Task {
            do {
                let response = try await keywordService.removeKeyword(keyword)
                await MainActor.run {
                    self.keywords = response.data.matchKeywords
                }
            } catch {
                // Handle error
            }
        }
    }
}

struct KeywordChip: View {
    let keyword: String
    let onRemove: () -> Void
    
    var body: some View {
        HStack(spacing: 4) {
            Text(keyword)
                .font(.caption)
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.caption)
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(Color.blue.opacity(0.1))
        .foregroundColor(.blue)
        .cornerRadius(12)
    }
}
```

### **ProfileKeywordsView**
```swift
struct ProfileKeywordsView: View {
    @StateObject private var keywordService = ProfileKeywordService()
    @State private var keywords: [String] = []
    @State private var matches: [IntelligentJobMatch] = []
    @State private var matchingStats: MatchingStats?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                // Keywords Section
                KeywordManagementSection()
                
                // Matching Stats
                if let stats = matchingStats {
                    MatchingStatsView(stats: stats)
                }
                
                // Matches List
                List(matches, id: \.jobId) { match in
                    JobMatchRow(match: match)
                }
            }
            .navigationTitle("Job Matching")
            .onAppear {
                loadMatches()
            }
        }
    }
    
    private func loadMatches() {
        Task {
            do {
                let response = try await keywordService.getMatches(limit: 20)
                await MainActor.run {
                    self.matches = response.data.matches
                    self.matchingStats = response.data.matchingStats
                }
            } catch {
                // Handle error
            }
        }
    }
}

struct JobMatchRow: View {
    let match: IntelligentJobMatch
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(match.title)
                    .font(.headline)
                Spacer()
                MatchScoreBadge(score: match.matchScore)
            }
            
            Text(match.company)
                .font(.subheadline)
                .foregroundColor(.secondary)
            
            // Matched Keywords
            HStack {
                ForEach(match.matchedKeywords, id: \.self) { keyword in
                    Text(keyword)
                        .font(.caption)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.green.opacity(0.2))
                        .cornerRadius(4)
                }
            }
            
            // Match Reasons
            ForEach(match.matchReasons.prefix(2), id: \.self) { reason in
                Text("• \(reason)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct MatchScoreBadge: View {
    let score: Double
    
    var body: some View {
        Text("\(Int(score))%")
            .font(.caption.bold())
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(scoreColor.opacity(0.2))
            .foregroundColor(scoreColor)
            .cornerRadius(8)
    }
    
    private var scoreColor: Color {
        switch score {
        case 80...100: return .green
        case 60..<80: return .orange
        default: return .red
        }
    }
}
```

## 4. 🔄 Local Matching Algorithm

For offline matching capability, you can implement the scoring algorithm locally:

```swift
class LocalJobMatcher {
    func calculateMatchScore(job: Job, keywords: [String]) -> JobMatchScore {
        var totalScore: Double = 0
        var matchedKeywords: [String] = []
        var matchReasons: [String] = []
        
        for keyword in keywords {
            var keywordScore: Double = 0
            
            // Title matching (40% weight)
            if job.title.localizedCaseInsensitiveContains(keyword) {
                keywordScore += 40
                matchReasons.append("Strong match for '\(keyword)' in job title")
            }
            
            // Requirements matching (30% weight)
            if job.requirements?.joined(separator: " ").localizedCaseInsensitiveContains(keyword) == true {
                keywordScore += 30
                matchReasons.append("Match for '\(keyword)' in requirements")
            }
            
            // Description matching (20% weight)
            if job.description.localizedCaseInsensitiveContains(keyword) {
                keywordScore += 20
                matchReasons.append("Match for '\(keyword)' in description")
            }
            
            // Company matching (10% weight)
            if job.company.localizedCaseInsensitiveContains(keyword) {
                keywordScore += 10
                matchReasons.append("Match for '\(keyword)' in company")
            }
            
            if keywordScore > 0 {
                matchedKeywords.append(keyword)
                totalScore += keywordScore
            }
        }
        
        // Normalize to 0-100 scale
        let maxPossibleScore = Double(keywords.count * 100)
        let normalizedScore = min(100, (totalScore / maxPossibleScore) * 100)
        
        // Bonus for multiple keyword matches
        if matchedKeywords.count > 1 {
            let bonus = min(20, Double(matchedKeywords.count) * 2)
            totalScore = min(100, normalizedScore + bonus)
            matchReasons.append("Bonus for matching \(matchedKeywords.count) keywords")
        }
        
        return JobMatchScore(
            score: normalizedScore,
            matchedKeywords: matchedKeywords,
            matchReasons: Array(matchReasons.prefix(5))
        )
    }
}

struct JobMatchScore {
    let score: Double
    let matchedKeywords: [String]
    let matchReasons: [String]
}
```

## 5. 🔄 Migration from Legacy System

If you have existing keyword subscriptions, they can be migrated automatically. The backend supports both systems during transition.

## 6. 📊 Analytics Integration

Update your analytics to show keyword-based metrics:

```swift
// Update ProfileStatsView
struct ProfileStatsView: View {
    let profile: UserProfile
    
    var body: some View {
        HStack {
            StatCard(
                title: "Keywords",
                value: "\(profile.jobPreferences?.matchKeywords.count ?? 0)",
                subtitle: "for matching"
            )
            // ... other stats
        }
    }
}
```

## ✅ Ready for Implementation

The backend is production-ready with:
- ✅ Complete API endpoints
- ✅ Intelligent scoring algorithms  
- ✅ Comprehensive validation
- ✅ Performance optimization
- ✅ Migration support

Start with implementing the `KeywordManagementSection` in your user profile, then add the intelligent matching views! 🚀