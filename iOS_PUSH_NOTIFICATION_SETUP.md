# 📱 iOS Push Notification Setup Guide

## ⚠️ **CRITICAL: Your Current Issue**

Your backend has **fake device tokens** like `placeholder_token_64_chars_min...`
You need to implement **real APNs token registration** in your iOS app.

## 🛠️ **Required iOS App Changes**

### 1. **App Delegate Setup**

**If using SwiftUI App (iOS 14+):**
```swift
import SwiftUI
import UserNotifications

@main
struct BirJobApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var delegate
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    
    func application(_ application: UIApplication, 
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        
        // Set notification delegate
        UNUserNotificationCenter.current().delegate = self
        
        // Request notification permissions
        requestNotificationPermissions()
        
        return true
    }
    
    func requestNotificationPermissions() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            if granted {
                print("✅ Notification permission granted")
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            } else {
                print("❌ Notification permission denied: \(error?.localizedDescription ?? "Unknown error")")
            }
        }
    }
    
    // CRITICAL: Handle real device token registration
    func application(_ application: UIApplication, 
                    didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        
        // Convert token to string
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        
        print("📱 Real APNs token received: \(tokenString)")
        
        // Send to backend immediately
        Task {
            await registerDeviceToken(tokenString)
        }
    }
    
    func application(_ application: UIApplication, 
                    didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("❌ Failed to register for remote notifications: \(error)")
    }
    
    // Handle notifications when app is in foreground
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                              willPresent notification: UNNotification,
                              withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        // Show notification even when app is open
        completionHandler([.banner, .badge, .sound])
    }
    
    // Handle notification taps
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                              didReceive response: UNNotificationResponse,
                              withCompletionHandler completionHandler: @escaping () -> Void) {
        
        let userInfo = response.notification.request.content.userInfo
        
        // Handle deep linking
        if let customData = userInfo["custom_data"] as? [String: Any],
           let deepLink = customData["deep_link"] as? String {
            handleDeepLink(deepLink)
        }
        
        completionHandler()
    }
    
    func handleDeepLink(_ urlString: String) {
        // Handle birjob:// URLs
        if let url = URL(string: urlString) {
            // Navigate to specific job or section
            print("🔗 Deep link: \(url)")
        }
    }
}
```

### 2. **API Service for Device Registration**

```swift
import Foundation

class PushNotificationService: ObservableObject {
    static let shared = PushNotificationService()
    
    private let baseURL = "https://birjobbackend-ir3e.onrender.com/api/v1"
    
    func registerDeviceToken(_ deviceToken: String) async {
        print("🚀 Registering device token with backend...")
        
        guard let url = URL(string: "\(baseURL)/devices/register") else {
            print("❌ Invalid URL")
            return
        }
        
        // Create device info
        let deviceInfo = [
            "deviceId": getStableDeviceId(), // Stable device identifier
            "deviceModel": UIDevice.current.model,
            "osVersion": UIDevice.current.systemVersion,
            "appVersion": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0",
            "timezone": TimeZone.current.identifier
        ]
        
        let payload: [String: Any] = [
            "device_token": deviceToken,
            "device_info": deviceInfo
        ]
        
        do {
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                
                if let responseData = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    print("✅ Device registered successfully: \(responseData)")
                    
                    // Store device info locally
                    UserDefaults.standard.set(deviceToken, forKey: "apns_device_token")
                    UserDefaults.standard.set(deviceInfo["deviceId"], forKey: "stable_device_id")
                } else {
                    print("⚠️ Device registered but couldn't parse response")
                }
                
            } else {
                print("❌ Device registration failed: HTTP \((response as? HTTPURLResponse)?.statusCode ?? 0)")
                if let responseString = String(data: data, encoding: .utf8) {
                    print("Response: \(responseString)")
                }
            }
            
        } catch {
            print("❌ Network error during device registration: \(error)")
        }
    }
    
    func updateUserKeywords(_ keywords: [String]) async {
        guard let deviceId = UserDefaults.standard.string(forKey: "stable_device_id"),
              let url = URL(string: "\(baseURL)/users/\(deviceId)") else {
            print("❌ No device ID found or invalid URL")
            return
        }
        
        let payload: [String: Any] = [
            "keywords": keywords,
            "notifications_enabled": true
        ]
        
        do {
            var request = URLRequest(url: url)
            request.httpMethod = "PUT"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
            
            let (_, response) = try await URLSession.shared.data(for: request)
            
            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 {
                print("✅ Keywords updated successfully")
            } else {
                print("❌ Failed to update keywords")
            }
            
        } catch {
            print("❌ Error updating keywords: \(error)")
        }
    }
    
    private func getStableDeviceId() -> String {
        let deviceIdKey = "stable_device_id"
        
        if let existingId = UserDefaults.standard.string(forKey: deviceIdKey) {
            return existingId
        }
        
        // Create new stable device ID
        let newDeviceId = UUID().uuidString
        UserDefaults.standard.set(newDeviceId, forKey: deviceIdKey)
        return newDeviceId
    }
}
```

### 3. **Keywords Setup View**

```swift
import SwiftUI

struct KeywordsSetupView: View {
    @State private var keywords: [String] = ["iOS", "Swift", "Mobile", "Developer"]
    @State private var newKeyword = ""
    @State private var isLoading = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                Text("Set Your Job Keywords")
                    .font(.title2)
                    .fontWeight(.bold)
                
                Text("We'll notify you when jobs match these keywords")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                
                // Current keywords
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 100))], spacing: 10) {
                    ForEach(keywords, id: \.self) { keyword in
                        HStack {
                            Text(keyword)
                                .font(.caption)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color.blue.opacity(0.1))
                                .foregroundColor(.blue)
                                .cornerRadius(16)
                            
                            Button("×") {
                                keywords.removeAll { $0 == keyword }
                            }
                            .foregroundColor(.red)
                            .font(.caption)
                        }
                    }
                }
                .padding()
                
                // Add new keyword
                HStack {
                    TextField("Add keyword", text: $newKeyword)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    
                    Button("Add") {
                        if !newKeyword.isEmpty && !keywords.contains(newKeyword) {
                            keywords.append(newKeyword)
                            newKeyword = ""
                        }
                    }
                    .disabled(newKeyword.isEmpty)
                }
                .padding()
                
                Spacer()
                
                Button(action: saveKeywords) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                    } else {
                        Text("Save Keywords & Enable Notifications")
                    }
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
                .disabled(isLoading || keywords.isEmpty)
                .padding()
            }
            .navigationTitle("Job Notifications")
        }
    }
    
    private func saveKeywords() {
        isLoading = true
        
        Task {
            await PushNotificationService.shared.updateUserKeywords(keywords)
            
            DispatchQueue.main.async {
                isLoading = false
                // Show success message or navigate
            }
        }
    }
}
```

### 4. **Main ContentView Integration**

```swift
import SwiftUI

struct ContentView: View {
    @State private var showingKeywordsSetup = false
    
    var body: some View {
        TabView {
            JobListView()
                .tabItem {
                    Image(systemName: "briefcase")
                    Text("Jobs")
                }
            
            SavedJobsView()
                .tabItem {
                    Image(systemName: "bookmark")
                    Text("Saved")
                }
            
            KeywordsSetupView()
                .tabItem {
                    Image(systemName: "bell")
                    Text("Notifications")
                }
        }
        .onAppear {
            // Request notifications on first launch
            if UserDefaults.standard.string(forKey: "stable_device_id") == nil {
                showingKeywordsSetup = true
            }
        }
        .sheet(isPresented: $showingKeywordsSetup) {
            KeywordsSetupView()
        }
    }
}
```

## 🔧 **Testing Steps**

### 1. **Build and Run iOS App**
1. Open your iOS project in Xcode
2. Add the code above to your app
3. Build and run on a **real device** (not simulator)
4. Grant notification permissions when prompted

### 2. **Verify Registration**
```bash
# Check if real device token was registered
curl "https://birjobbackend-ir3e.onrender.com/api/v1/notifications/devices"

# Look for device token that's NOT placeholder
```

### 3. **Set Keywords**
1. Open the "Notifications" tab in your app
2. Add keywords like: "iOS", "Swift", "Developer", "Mobile"
3. Tap "Save Keywords & Enable Notifications"

### 4. **Test GitHub Actions**
1. Go to GitHub → Actions → "Job Notifications"
2. Click "Run workflow"
3. Watch logs to see if notifications are sent

### 5. **Manual Test**
```bash
# Send test notification to your device
curl -X POST "https://birjobbackend-ir3e.onrender.com/api/v1/notifications/test-simple-push/YOUR_DEVICE_ID"
```

## 🎯 **Expected Result**

After implementing these changes:
1. ✅ **Real device token** registered (64+ hex characters)
2. ✅ **Keywords saved** in backend
3. ✅ **GitHub Actions** finds matching jobs every 40 minutes
4. ✅ **Push notifications** sent to your iPhone
5. ✅ **Notifications appear** on lock screen and notification center

## ⚠️ **Important Notes**

- **Real Device Required**: Push notifications only work on physical devices, not simulator
- **APNs Environment**: Make sure backend uses production APNs (not sandbox)
- **Bundle ID**: Must match your Apple Developer certificate
- **Permissions**: User must grant notification permissions

Once you implement these changes, your GitHub Actions will automatically send you job notifications every 40 minutes! 🎉