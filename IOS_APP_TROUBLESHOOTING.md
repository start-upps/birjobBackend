# iOS App Troubleshooting Guide

**Backend**: `https://birjobbackend-ir3e.onrender.com`  
**Status**: Production Ready ✅  
**Last Updated**: July 3, 2025

---

## 🚨 Common iOS App Connection Issues

### Issue #1: "User not found for device" Error

**Problem**: iOS app gets 404 errors when trying to access user profile or saved jobs

**Root Cause**: Device not registered with backend

**Solution**: Register device first before any other API calls

```swift
// ALWAYS call this first when app launches
func registerDevice() async {
    let deviceId = UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString
    
    do {
        let response: UserRegistrationResponse = try await APIClient.shared.request(
            endpoint: .registerUser(
                deviceId: deviceId,
                email: "user@example.com", // Get from user input
                keywords: ["iOS", "Swift"] // Get from user selection
            ),
            responseType: UserRegistrationResponse.self
        )
        
        if response.success {
            print("Device registered: \(response.data.deviceId)")
            // Now other API calls will work
        }
    } catch {
        print("Registration failed: \(error)")
    }
}
```

**Testing**: Device `C92CE417-A9A3-43D9-9279-00FC75AE2DF7` has been registered for testing

---

### Issue #2: Network Timeout Errors

**Problem**: API calls taking too long or timing out

**Root Cause**: Backend might be sleeping (Render.com free tier)

**Solution**: Implement retry logic and proper timeout handling

```swift
extension APIClient {
    func requestWithRetry<T: Codable>(
        endpoint: APIEndpoint,
        responseType: T.Type,
        retries: Int = 3
    ) async throws -> T {
        for attempt in 1...retries {
            do {
                return try await request(endpoint: endpoint, responseType: responseType)
            } catch {
                if attempt == retries {
                    throw error
                }
                
                // Wait before retry (exponential backoff)
                try await Task.sleep(nanoseconds: UInt64(attempt * 1_000_000_000)) // 1, 2, 3 seconds
                print("Retry attempt \(attempt + 1)")
            }
        }
        
        throw NetworkError.serverError(0)
    }
}
```

---

### Issue #3: JSON Parsing Errors

**Problem**: App crashes when parsing API responses

**Root Cause**: Mismatched model structures

**Solution**: Use exact models from documentation

```swift
// Use these EXACT models - they match backend responses

struct User: Codable {
    let id: String
    let deviceId: String
    let email: String
    let keywords: String // Note: Backend returns JSON string, not array
    let preferredSources: String
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
    
    // Helper to get keywords as array
    var keywordsArray: [String] {
        guard let data = keywords.data(using: .utf8),
              let array = try? JSONDecoder().decode([String].self, from: data) else {
            return []
        }
        return array
    }
}
```

---

### Issue #4: Device ID Changes Between Sessions

**Problem**: Different device IDs generated on each app launch

**Root Cause**: Not storing device ID persistently

**Solution**: Store device ID in UserDefaults

```swift
class DeviceManager: ObservableObject {
    static let shared = DeviceManager()
    
    private let deviceIdKey = "stored_device_id"
    
    var deviceId: String {
        // Check if we have a stored device ID
        if let storedId = UserDefaults.standard.string(forKey: deviceIdKey) {
            return storedId
        }
        
        // Generate new device ID
        let newId = UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString
        
        // Store it for future use
        UserDefaults.standard.set(newId, forKey: deviceIdKey)
        
        return newId
    }
    
    // Call this to reset device ID (for testing)
    func resetDeviceId() {
        UserDefaults.standard.removeObject(forKey: deviceIdKey)
    }
}
```

---

### Issue #5: Authentication Errors

**Problem**: 401 Unauthorized errors

**Root Cause**: Backend uses device-based auth, not JWT tokens

**Solution**: Include device_id in every request

```swift
// CORRECT - Include device_id in request body
let data = [
    "device_id": DeviceManager.shared.deviceId,
    "job_id": jobId
]

// WRONG - Don't add Authorization headers
// request.setValue("Bearer token", forHTTPHeaderField: "Authorization")
```

---

## 🔧 Backend Status Check

### Quick Health Check
```bash
curl https://birjobbackend-ir3e.onrender.com/health
# Expected: {"status":"healthy","message":"Service is running"}
```

### Test User Registration
```bash
curl -X POST "https://birjobbackend-ir3e.onrender.com/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "YOUR-DEVICE-ID",
    "email": "test@example.com",
    "keywords": ["iOS", "Swift"],
    "notifications_enabled": true
  }'
```

### Test Job Search
```bash
curl "https://birjobbackend-ir3e.onrender.com/api/v1/jobs/?search=iOS&limit=5"
# Should return 5 iOS-related jobs
```

---

## 📱 iOS App Integration Checklist

### ✅ Before First API Call
- [ ] Generate or retrieve stored device ID
- [ ] Implement APIClient with correct base URL
- [ ] Add proper error handling for network requests
- [ ] Test health endpoint connectivity

### ✅ User Registration Flow
- [ ] Get user email and keywords
- [ ] Call `/api/v1/users/register` endpoint
- [ ] Store registration success state
- [ ] Handle registration errors gracefully

### ✅ Main App Features
- [ ] Test job search with real queries
- [ ] Implement job saving functionality
- [ ] Test saved jobs retrieval
- [ ] Add AI chat integration
- [ ] Track analytics events

### ✅ Error Handling
- [ ] Handle "User not found" errors
- [ ] Implement retry logic for timeouts
- [ ] Show user-friendly error messages
- [ ] Log errors for debugging

---

## 🐛 Debug Information

### Current Production Status
- **Backend URL**: `https://birjobbackend-ir3e.onrender.com`
- **Health Status**: ✅ Operational
- **Total Jobs**: 4,367+ active listings
- **Job Sources**: 39 different platforms
- **AI Status**: ✅ Gemini 2.5 Flash operational

### Test Device Registration
```json
{
  "device_id": "C92CE417-A9A3-43D9-9279-00FC75AE2DF7",
  "user_id": "ed9486e0-4854-4358-814f-0356249bc122",
  "email": "ios-app-test@example.com",
  "keywords": ["iOS", "Swift", "Mobile Development"],
  "registered_at": "2025-07-03T16:25:47.781018+00:00"
}
```

### Sample API Responses

#### User Profile Response
```json
{
  "success": true,
  "message": "User profile found",
  "data": {
    "id": "ed9486e0-4854-4358-814f-0356249bc122",
    "device_id": "C92CE417-A9A3-43D9-9279-00FC75AE2DF7",
    "email": "ios-app-test@example.com",
    "keywords": "[\"iOS\", \"Swift\", \"Mobile Development\"]",
    "preferred_sources": "[]",
    "notifications_enabled": true,
    "created_at": "2025-07-03T16:25:47.781018+00:00",
    "updated_at": "2025-07-03T16:25:47.781018+00:00"
  }
}
```

#### Saved Jobs Response (Empty)
```json
{
  "success": true,
  "data": {
    "saved_jobs": []
  }
}
```

---

## 🆘 If You're Still Having Issues

### 1. Check Backend Logs
Look for these error patterns in logs:
- `"User profile not found"` → Device not registered
- `"Invalid device ID format"` → Wrong device ID format
- `"JSON decode error"` → Malformed request body

### 2. Test Individual Endpoints
Use curl commands to test each endpoint:

```bash
# Health check
curl https://birjobbackend-ir3e.onrender.com/health

# Register user (replace device_id)
curl -X POST "https://birjobbackend-ir3e.onrender.com/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"YOUR-DEVICE-ID","email":"test@example.com","keywords":["iOS"],"notifications_enabled":true}'

# Get profile (replace device_id)
curl "https://birjobbackend-ir3e.onrender.com/api/v1/users/profile/YOUR-DEVICE-ID"

# Search jobs
curl "https://birjobbackend-ir3e.onrender.com/api/v1/jobs/?search=iOS&limit=5"
```

### 3. Enable Detailed Logging
```swift
// Add to your APIClient
private func logRequest(_ request: URLRequest) {
    print("🌐 API Request:")
    print("URL: \(request.url?.absoluteString ?? "nil")")
    print("Method: \(request.httpMethod ?? "nil")")
    print("Headers: \(request.allHTTPHeaderFields ?? [:])")
    
    if let body = request.httpBody {
        print("Body: \(String(data: body, encoding: .utf8) ?? "nil")")
    }
}

private func logResponse(_ data: Data, _ response: URLResponse?) {
    print("📡 API Response:")
    if let httpResponse = response as? HTTPURLResponse {
        print("Status: \(httpResponse.statusCode)")
    }
    print("Data: \(String(data: data, encoding: .utf8) ?? "nil")")
}
```

### 4. Contact Support
If issues persist, provide:
- Device ID being used
- Exact error messages
- API endpoint being called
- Request/response logs
- iOS version and device model

---

**The backend is 100% operational and ready for iOS app integration!** 🚀

Most connection issues are resolved by proper device registration and using the correct API patterns documented in this guide.