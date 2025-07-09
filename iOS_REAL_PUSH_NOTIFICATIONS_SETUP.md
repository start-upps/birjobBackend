# iOS Real Push Notifications Setup Guide

## 🎯 Current Issue
Your backend is working perfectly and finding 18+ job matches, but notifications fail with `BadDeviceToken` because the iOS app sends fake placeholder tokens instead of real APNs tokens.

## ✅ Backend Status
- ✅ Keyword matching working: finds jobs for 'SQL', 'iOS', 'React Native'
- ✅ Processing 4,350+ jobs from database
- ✅ Bulk notifications implemented
- ❌ Failing due to fake device tokens like `1C1108D7-BBAD-4B0F-89F7-F55624300CE1`

---

## 📱 iOS App Implementation Steps

### Step 1: Enable Push Notifications in Xcode

1. **Open your iOS project in Xcode**
2. **Select your app target**
3. **Go to "Signing & Capabilities" tab**
4. **Click "+ Capability"**
5. **Add "Push Notifications"**
6. **Ensure your Team and Bundle Identifier are correct**

### Step 2: Configure AppDelegate for Push Notifications

Replace your current AppDelegate.swift with this complete implementation:

```swift
import UIKit
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate {

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Set up push notifications
        setupPushNotifications()
        
        return true
    }
    
    // MARK: - Push Notifications Setup
    private func setupPushNotifications() {
        UNUserNotificationCenter.current().delegate = self
        
        // Request permission for notifications
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            print("📱 Push notification permission granted: \(granted)")
            
            if let error = error {
                print("❌ Error requesting push notification permission: \(error)")
                return
            }
            
            if granted {
                // Register for remote notifications on the main thread
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
    }
    
    // MARK: - APNs Registration Success
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        // Convert device token to hex string
        let tokenParts = deviceToken.map { data in 
            String(format: "%02.2hhx", data) 
        }
        let token = tokenParts.joined()
        
        print("✅ Real APNs device token received: \(token)")
        
        // Send this REAL token to your backend
        sendDeviceTokenToBackend(token: token)
    }
    
    // MARK: - APNs Registration Failure
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("❌ Failed to register for remote notifications: \(error)")
        
        // You can still test with simulator, but notifications won't work
        if TARGET_OS_SIMULATOR != 0 {
            print("📱 Running on simulator - push notifications not supported")
            // For simulator testing, you can still call your API with a fake token for development
            // sendDeviceTokenToBackend(token: "SIMULATOR_TOKEN_FOR_DEVELOPMENT_ONLY")
        }
    }
    
    // MARK: - Send Token to Backend
    private func sendDeviceTokenToBackend(token: String) {
        // Store token locally first to prevent duplicate calls
        let tokenKey = "stored_device_token"
        let storedToken = UserDefaults.standard.string(forKey: tokenKey)
        
        if storedToken == token {
            print("📱 Device token already registered, skipping duplicate call")
            return
        }
        
        // Get device information
        let deviceInfo = DeviceInfo(
            deviceId: UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString,
            deviceModel: UIDevice.current.model,
            osVersion: UIDevice.current.systemVersion,
            appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0",
            timezone: TimeZone.current.identifier
        )
        
        let request = DeviceRegistrationRequest(
            deviceToken: token,
            deviceInfo: deviceInfo
        )
        
        // Call your API service
        APIService.shared.registerDevice(request: request) { result in
            switch result {
            case .success:
                print("✅ Device token successfully registered with backend")
                // Store token to prevent duplicate calls
                UserDefaults.standard.set(token, forKey: tokenKey)
            case .failure(let error):
                print("❌ Failed to register device token: \(error)")
                // Don't store token if failed, so we can retry
            }
        }
    }
}

// MARK: - UNUserNotificationCenterDelegate
extension AppDelegate: UNUserNotificationCenterDelegate {
    
    // Handle notification when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                               willPresent notification: UNNotification, 
                               withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        // Show notification even when app is in foreground
        completionHandler([.alert, .badge, .sound])
    }
    
    // Handle notification tap
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                               didReceive response: UNNotificationResponse, 
                               withCompletionHandler completionHandler: @escaping () -> Void) {
        
        let userInfo = response.notification.request.content.userInfo
        handleNotificationTap(userInfo: userInfo)
        completionHandler()
    }
    
    private func handleNotificationTap(userInfo: [AnyHashable: Any]) {
        guard let customData = userInfo["custom_data"] as? [String: Any],
              let type = customData["type"] as? String else {
            return
        }
        
        switch type {
        case "bulk_job_match", "job_match":
            // Handle job notification tap
            if let jobIds = customData["job_ids"] as? [Int] {
                // Navigate to job list with these IDs
                navigateToJobMatches(jobIds: jobIds)
            } else if let jobId = customData["job_id"] as? Int {
                // Navigate to single job
                navigateToJob(jobId: jobId)
            }
        default:
            print("Unknown notification type: \(type)")
        }
    }
    
    private func navigateToJobMatches(jobIds: [Int]) {
        // TODO: Implement navigation to job matches screen
        print("📱 Navigate to job matches: \(jobIds)")
    }
    
    private func navigateToJob(jobId: Int) {
        // TODO: Implement navigation to specific job
        print("📱 Navigate to job: \(jobId)")
    }
}
```

### Step 3: Create Data Models

Create a new file `DeviceRegistrationModels.swift`:

```swift
import Foundation

struct DeviceRegistrationRequest: Codable {
    let deviceToken: String
    let deviceInfo: DeviceInfo
}

struct DeviceInfo: Codable {
    let deviceId: String        // UIDevice.current.identifierForVendor
    let deviceModel: String     // "iPhone", "iPad"
    let osVersion: String       // "17.0"
    let appVersion: String      // "1.0"
    let timezone: String        // "America/New_York"
    
    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case deviceModel = "device_model"
        case osVersion = "os_version"
        case appVersion = "app_version"
        case timezone
    }
}

struct DeviceRegistrationResponse: Codable {
    let success: Bool
    let message: String
    let data: DeviceData?
}

struct DeviceData: Codable {
    let deviceId: String
    let userId: String
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case userId = "user_id"
        case message
    }
}
```

### Step 4: Update Your API Service

Add this method to your existing `APIService.swift`:

```swift
extension APIService {
    // MARK: - Device Registration (call once per device)
    func registerDevice(request: DeviceRegistrationRequest, completion: @escaping (Result<DeviceRegistrationResponse, Error>) -> Void) {
        
        let url = URL(string: "\(baseURL)/api/v1/devices/register")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            urlRequest.httpBody = try JSONEncoder().encode(request)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(NSError(domain: "APIError", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data received"])))
                }
                return
            }
            
            do {
                let registrationResponse = try JSONDecoder().decode(DeviceRegistrationResponse.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(registrationResponse))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
            }
        }.resume()
    }
    
    // MARK: - Update User Profile (call when user enters email/keywords)
    func updateUserProfile(email: String?, keywords: [String], completion: @escaping (Result<Void, Error>) -> Void) {
        
        let deviceId = UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString
        
        let url = URL(string: "\(baseURL)/api/v1/users/profile")!
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "PUT"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let updateRequest = [
            "device_id": deviceId,
            "email": email ?? "",
            "keywords": keywords
        ] as [String: Any]
        
        do {
            urlRequest.httpBody = try JSONSerialization.data(withJSONObject: updateRequest)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: urlRequest) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            DispatchQueue.main.async {
                completion(.success(()))
            }
        }.resume()
    }
}
```

### Step 5: Test on Real Device

**IMPORTANT:** Push notifications only work on real devices, not simulators.

1. **Build and run on a real iPhone/iPad**
2. **Grant notification permission when prompted**
3. **Check the Xcode console for log messages:**
   - `✅ Real APNs device token received: [64-character hex string]`
   - `✅ Device token successfully registered with backend`

### Step 6: Test Notifications

1. **Add some keywords in your app** (SQL, iOS, React Native)
2. **Wait for the GitHub Actions to run** (every 40 minutes)
3. **You should receive real push notifications!**

---

## 🔧 Troubleshooting

### If you see "Failed to register for remote notifications":
1. **Check Apple Developer Account:** Ensure push notifications are enabled
2. **Check Bundle ID:** Must match your Apple Developer Console
3. **Check Provisioning Profile:** Must include push notification capability
4. **Check Network:** Device needs internet connection

### If notifications still don't work:
1. **Check device settings:** Settings > [Your App] > Notifications (must be enabled)
2. **Check backend logs:** Look for `✅ MATCH!` messages in your backend
3. **Verify device token:** Should be 64 hex characters, not placeholder

### Production vs Development:
- **Development:** Uses Apple's sandbox push servers
- **Production:** Uses Apple's production push servers
- **Your backend is configured for production** (which is correct for App Store)

---

## ⚡ Quick Summary

1. **Add Push Notifications capability in Xcode**
2. **Replace AppDelegate with the code above**
3. **Add the data models**
4. **Update your API service**
5. **Test on real device**
6. **Check for real APNs token in logs**
7. **Wait for notifications (system finds 18+ matches!)**

The backend is working perfectly - it just needs real device tokens instead of fake ones!