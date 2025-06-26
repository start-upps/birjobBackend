#!/bin/bash

# Production API Endpoint Testing Script
# Tests all endpoints on https://birjobbackend-ir3e.onrender.com

BASE_URL="https://birjobbackend-ir3e.onrender.com"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== Production API Testing Report ==="
echo "Timestamp: $TIMESTAMP"
echo "Base URL: $BASE_URL"
echo "==========================================="
echo

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    
    echo -n "Testing $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$BASE_URL$endpoint")
        status_code="${response: -3}"
        body="${response%???}"
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
        status_code="${response: -3}"
        body="${response%???}"
    fi
    
    if [ "$status_code" = "200" ]; then
        echo "✅ OK ($status_code)"
    elif [ "$status_code" = "404" ]; then
        echo "❌ Not Found ($status_code)"
    elif [ "$status_code" = "500" ]; then
        echo "❌ Server Error ($status_code)"
    elif [ "$status_code" = "307" ]; then
        echo "🔄 Redirect ($status_code)"
    else
        echo "⚠️  Status: $status_code"
    fi
}

echo "=== Root Endpoints ==="
test_endpoint "GET" "/" "Root endpoint"
test_endpoint "GET" "/api" "API root"
test_endpoint "GET" "/favicon.ico" "Favicon"
echo

echo "=== Health Endpoints ==="
test_endpoint "GET" "/api/v1/health" "System health"
test_endpoint "GET" "/api/v1/health/db-debug" "Database debug"
test_endpoint "POST" "/api/v1/health/create-user-tables" "Create user tables"
echo

echo "=== Job Endpoints ==="
test_endpoint "GET" "/api/v1/jobs/" "Job listings"
test_endpoint "GET" "/api/v1/jobs/?limit=5" "Job listings with limit"
test_endpoint "GET" "/api/v1/jobs/572651" "Specific job"
test_endpoint "GET" "/api/v1/jobs/stats/summary" "Job statistics"
echo

echo "=== Analytics Endpoints ==="
test_endpoint "GET" "/api/v1/analytics/jobs/trends" "Job trends"
test_endpoint "GET" "/api/v1/analytics/companies/top" "Top companies"
test_endpoint "GET" "/api/v1/analytics/locations/popular" "Popular locations"
test_endpoint "GET" "/api/v1/analytics/salaries/ranges" "Salary ranges"
echo

echo "=== AI Endpoints ==="
test_endpoint "POST" "/api/v1/ai/job-recommendations" "AI job recommendations" '{"deviceId": "test-device-123"}'
test_endpoint "POST" "/api/v1/ai/job-match-analysis" "AI job match analysis" '{"deviceId": "test-device-123", "jobId": 572651}'
test_endpoint "POST" "/api/v1/ai/resume-review" "AI resume review" '{"deviceId": "test-device-123", "resumeText": "iOS Developer with 5 years experience"}'
test_endpoint "POST" "/api/v1/ai/career-advice" "AI career advice" '{"deviceId": "test-device-123", "question": "How to improve iOS development skills?"}'
echo

echo "=== Device Endpoints ==="
test_endpoint "POST" "/api/v1/devices/register" "Device registration" '{"deviceId": "test-device-123", "apnsToken": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"}'
test_endpoint "GET" "/api/v1/devices/test-device-123/status" "Device status"
echo

echo "=== User Endpoints ==="
test_endpoint "POST" "/api/v1/users/profile" "Create user profile" '{"deviceId": "test-device-123", "personalInfo": {"firstName": "Test", "lastName": "User"}}'
test_endpoint "GET" "/api/v1/users/profile/test-device-123" "Get user profile"
echo

echo "==========================================="
echo "Testing completed at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"