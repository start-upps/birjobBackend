#!/bin/bash

# Comprehensive notification system testing script
# Run this after applying the database migration

BASE_URL="https://birjobbackend-ir3e.onrender.com"
DEVICE_ID="TEST-DEVICE-123"

echo "🧪 Testing Push Notification System"
echo "=================================="

# Function to make API calls and show results
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo ""
    echo "📡 Testing: $description"
    echo "   Endpoint: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        curl -s "$BASE_URL$endpoint" | jq .
    else
        curl -s -X "$method" "$BASE_URL$endpoint" \
             -H "Content-Type: application/json" \
             -d "$data" | jq .
    fi
    
    echo "   Status: ✅ Complete"
}

# 1. Test Health Check
test_api "GET" "/health" "" "Health Check"

# 2. Test User Registration (if needed)
echo ""
echo "👤 Setting up test user..."
test_api "POST" "/api/v1/users/register" '{
    "device_id": "'$DEVICE_ID'",
    "device_token": "test_token_123",
    "email": "test@notifications.com",
    "keywords": ["iOS", "Swift", "React Native"],
    "preferred_sources": ["apple.com", "indeed.com"],
    "device_info": {"platform": "iOS", "version": "17.0"}
}' "User Registration"

# 3. Test Notification Settings
test_api "PUT" "/api/v1/notifications/settings" '{
    "device_id": "'$DEVICE_ID'",
    "notifications_enabled": true,
    "keywords": ["iOS Developer", "Swift", "React Native", "Mobile App", "Apple"]
}' "Update Notification Settings"

# 4. Test User Profile (verify keywords)
test_api "GET" "/api/v1/users/profile/$DEVICE_ID" "" "Get User Profile"

# 5. Test Job Match Notification #1
test_api "POST" "/api/v1/notifications/job-match" '{
    "device_id": "'$DEVICE_ID'",
    "job_id": 2001,
    "job_title": "Senior iOS Developer",
    "job_company": "Apple Inc.",
    "job_source": "apple.com",
    "matched_keywords": ["iOS Developer", "Swift"]
}' "Job Match Notification #1"

# 6. Test Duplicate Prevention (same job)
test_api "POST" "/api/v1/notifications/job-match" '{
    "device_id": "'$DEVICE_ID'",
    "job_id": 2001,
    "job_title": "Senior iOS Developer", 
    "job_company": "Apple Inc.",
    "job_source": "apple.com",
    "matched_keywords": ["iOS Developer", "Swift"]
}' "Duplicate Prevention Test"

# 7. Test Different Job Notification
test_api "POST" "/api/v1/notifications/job-match" '{
    "device_id": "'$DEVICE_ID'",
    "job_id": 2002,
    "job_title": "React Native Developer",
    "job_company": "Meta",
    "job_source": "meta.com",
    "matched_keywords": ["React Native", "Mobile App"]
}' "Job Match Notification #2"

# 8. Test Another Different Job
test_api "POST" "/api/v1/notifications/job-match" '{
    "device_id": "'$DEVICE_ID'",
    "job_id": 2003,
    "job_title": "Swift Engineer",
    "job_company": "Uber",
    "job_source": "uber.com",
    "matched_keywords": ["Swift"]
}' "Job Match Notification #3"

# 9. Test Notification History
test_api "GET" "/api/v1/notifications/history/$DEVICE_ID?limit=10" "" "Get Notification History"

# 10. Test Notification Statistics
test_api "GET" "/api/v1/notifications/stats" "" "Get Notification Statistics"

# 11. Test Bulk Processing (Dry Run)
test_api "POST" "/api/v1/notifications/test-run?dry_run=true" "" "Test Bulk Processing (Dry Run)"

# 12. Test Bulk Processing with Real Jobs
test_api "POST" "/api/v1/notifications/trigger" '{
    "limit": 50,
    "dry_run": true
}' "Test Bulk Processing (Real Jobs)"

echo ""
echo "🎉 Testing Complete!"
echo "==================="
echo ""
echo "📊 Summary:"
echo "- User registration and keyword setup"
echo "- Job match notifications with duplicate prevention"
echo "- Notification history tracking"
echo "- Statistics and bulk processing"
echo ""
echo "📋 Next Steps:"
echo "1. Check logs for any errors"
echo "2. Verify database tables are populated"
echo "3. Test with real APNs certificates for actual push notifications"
echo "4. Monitor scheduled notifications (runs every hour)"
echo ""
echo "🔍 Database Verification Queries:"
echo "SELECT COUNT(*) FROM iosapp.job_notification_history;"
echo "SELECT COUNT(*) FROM iosapp.push_notifications;"
echo "SELECT COUNT(*) FROM iosapp.notification_settings;"
echo ""