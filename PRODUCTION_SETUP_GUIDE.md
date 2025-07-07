# 🚀 Production Push Notifications Setup Guide

## 📱 Getting Production Device Tokens

### Current Status
- ✅ **Sandbox**: Working with development device token
- 🔄 **Production**: Needs App Store build for production tokens

### Step 1: Build Production App

#### In Xcode:
1. **Set Build Configuration to Release**
   ```
   Product → Scheme → Edit Scheme → Build Configuration → Release
   ```

2. **Configure App Store Provisioning**
   - Go to Project Settings → Signing & Capabilities
   - Ensure "Automatically manage signing" is checked
   - Team: Select your Apple Developer Team
   - Bundle Identifier: `com.ismats.birjob` ✅ (confirmed)

3. **Push Notifications Capability**
   ```
   Signing & Capabilities → + Capability → Push Notifications
   ```

4. **Archive for App Store**
   ```
   Product → Archive
   ```

### Step 2: App Store Connect Setup

#### Upload to App Store Connect:
1. **Xcode Organizer**
   - Select your archive
   - Click "Distribute App"
   - Choose "App Store Connect"
   - Upload binary

2. **App Store Connect Configuration**
   - Go to https://appstoreconnect.apple.com
   - Select your app (`com.ismats.birjob`)
   - Verify push notifications are enabled

### Step 3: TestFlight Distribution

#### For Production Token Testing:
1. **Add TestFlight Internal Users**
   - App Store Connect → TestFlight → Internal Testing
   - Add your email as internal tester

2. **Install TestFlight Build**
   - Install app via TestFlight (not Xcode)
   - This generates **production device tokens**

### Step 4: Update Server Environment

#### Current APNs Configuration:
```bash
# ✅ Already configured with new key
APNS_KEY_ID=834XDMQ3QB
APNS_BUNDLE_ID=com.ismats.birjob
APNS_SANDBOX=false  # Production mode
```

### Step 5: Test Production Push

#### When you have production device token:
```python
# Test with production token
PRODUCTION_DEVICE_TOKEN = "your_production_token_here"

# Test endpoint
curl -X POST "https://birjobbackend-ir3e.onrender.com/api/v1/devices/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "your_production_token",
    "device_info": {
      "device_id": "production-device-id",
      "os_version": "18.6",
      "app_version": "1.0",
      "device_model": "iPhone",
      "timezone": "Asia/Baku"
    }
  }'
```

## 🔍 Current Device Information

### Development Environment:
- **Device Token**: `328b1bcf9414e941a07f5d102260b4e48245f83cc07291e62ff2eb16c478a442`
- **Device ID**: `8443ED74-4856-44E9-9FFC-94776AF69EF9`
- **User ID**: `649992aa-c4e0-42d3-9c85-1e6ec3c3a6a7`
- **Status**: ✅ Working in sandbox

### Production Environment:
- **Device Token**: *Will be generated after TestFlight install*
- **Environment**: Production APNs
- **Status**: 🔄 Pending App Store build

## 📋 Next Steps Checklist

### For Developer (You):
- [ ] Build app in Release mode
- [ ] Archive and upload to App Store Connect
- [ ] Configure TestFlight internal testing
- [ ] Install via TestFlight to get production token
- [ ] Update server with production device token

### For Users (After App Store):
- [ ] Users install from App Store
- [ ] App registers production device tokens automatically
- [ ] Push notifications work in production

## 🚀 Quick Production Test

Once you have a production device token from TestFlight:

```bash
# Test production push notification
python test_new_device_token.py
```

This will test both sandbox and production environments with your token.

## 📱 iOS App Configuration Verification

### Required Capabilities:
- ✅ Push Notifications capability
- ✅ Background App Refresh
- ✅ Bundle ID matches: `com.ismats.birjob`

### Required Code (already implemented):
- ✅ Request notification permissions
- ✅ Register for remote notifications
- ✅ Handle device token registration
- ✅ Send token to backend

## 🎯 Current Status Summary

1. **✅ APNs Key**: New key working (834XDMQ3QB)
2. **✅ Backend**: Production server operational
3. **✅ Sandbox**: Push notifications working
4. **🔄 Production**: Needs App Store build for production tokens
5. **✅ iOS App**: Properly configured for notifications

**Next:** Build and upload to App Store Connect for production device tokens! 🚀