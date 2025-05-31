#!/bin/bash

# BirJob Backend API - Complete Test Suite
# Updated URL for new Render deployment

# Set your updated Render URL here
API_URL="https://birjobbackend-ir3e.onrender.com"

echo "🚀 BirJob Backend API Test Suite"
echo "Testing API at: $API_URL"
echo "=================================="

# =============================================================================
# 1. HEALTH CHECK ENDPOINTS
# =============================================================================
echo ""
echo "🏥 HEALTH CHECK ENDPOINTS"
echo "------------------------"

# Basic health check
echo "1.1 Basic Health Check:"
curl -X GET "$API_URL/api/health" \
  -H "Accept: application/json"

# Detailed health check
echo -e "\n\n1.2 Detailed Health Check:"
curl -X GET "$API_URL/api/health/detailed" \
  -H "Accept: application/json"

# Database health
echo -e "\n\n1.3 Database Health:"
curl -X GET "$API_URL/api/health/database" \
  -H "Accept: application/json"

# Redis health
echo -e "\n\n1.4 Redis Health:"
curl -X GET "$API_URL/api/health/redis" \
  -H "Accept: application/json"

# API metrics
echo -e "\n\n1.5 API Metrics:"
curl -X GET "$API_URL/api/health/metrics" \
  -H "Accept: application/json"

# Readiness probe
echo -e "\n\n1.6 Readiness Probe:"
curl -X GET "$API_URL/api/health/ready" \
  -H "Accept: application/json"

# Liveness probe
echo -e "\n\n1.7 Liveness Probe:"
curl -X GET "$API_URL/api/health/live" \
  -H "Accept: application/json"

# Performance test
echo -e "\n\n1.8 Performance Test (10 iterations):"
curl -X GET "$API_URL/api/health/performance?iterations=10" \
  -H "Accept: application/json"

# =============================================================================
# 2. JOBS ENDPOINTS
# =============================================================================
echo -e "\n\n"
echo "💼 JOBS ENDPOINTS"
echo "----------------"

# Get all jobs (basic)
echo "2.1 Get All Jobs (Basic):"
curl -X GET "$API_URL/api/v1/jobs" \
  -H "Accept: application/json"

# Get jobs with pagination
echo -e "\n\n2.2 Get Jobs with Pagination:"
curl -X GET "$API_URL/api/v1/jobs?page=1&limit=5" \
  -H "Accept: application/json"

# Search jobs by keyword
echo -e "\n\n2.3 Search Jobs by Keyword:"
curl -X GET "$API_URL/api/v1/jobs?search=developer" \
  -H "Accept: application/json"

# Filter by source
echo -e "\n\n2.4 Filter Jobs by Source:"
curl -X GET "$API_URL/api/v1/jobs?source=LinkedIn" \
  -H "Accept: application/json"

# Filter by company
echo -e "\n\n2.5 Filter Jobs by Company:"
curl -X GET "$API_URL/api/v1/jobs?company=Google" \
  -H "Accept: application/json"

# Combined filters
echo -e "\n\n2.6 Combined Filters:"
curl -X GET "$API_URL/api/v1/jobs?search=engineer&page=1&limit=3" \
  -H "Accept: application/json"

# Get specific job (you'll need to replace 1 with actual job ID)
echo -e "\n\n2.7 Get Specific Job:"
curl -X GET "$API_URL/api/v1/jobs/1" \
  -H "Accept: application/json"

# Get job sources
echo -e "\n\n2.8 Get Job Sources:"
curl -X GET "$API_URL/api/v1/jobs/meta/sources" \
  -H "Accept: application/json"

# Get companies
echo -e "\n\n2.9 Get Companies:"
curl -X GET "$API_URL/api/v1/jobs/meta/companies" \
  -H "Accept: application/json"

# Get job trends
echo -e "\n\n2.10 Get Job Trends:"
curl -X GET "$API_URL/api/v1/jobs/meta/trends" \
  -H "Accept: application/json"

# =============================================================================
# 3. USER MANAGEMENT ENDPOINTS
# =============================================================================
echo -e "\n\n"
echo "👤 USER MANAGEMENT ENDPOINTS"
echo "----------------------------"

# User registration
echo "3.1 User Registration:"
curl -X POST "$API_URL/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com"
  }'

# Get user profile
echo -e "\n\n3.2 Get User Profile:"
curl -X GET "$API_URL/api/v1/users/profile?email=test@example.com" \
  -H "Accept: application/json"

# Get user keywords
echo -e "\n\n3.3 Get User Keywords:"
curl -X GET "$API_URL/api/v1/users/keywords?email=test@example.com" \
  -H "Accept: application/json"

# Add keyword
echo -e "\n\n3.4 Add User Keyword:"
curl -X POST "$API_URL/api/v1/users/keywords" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com",
    "keyword": "javascript"
  }'

# Add another keyword
echo -e "\n\n3.5 Add Another Keyword:"
curl -X POST "$API_URL/api/v1/users/keywords" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com",
    "keyword": "react"
  }'

# Remove keyword
echo -e "\n\n3.6 Remove User Keyword:"
curl -X DELETE "$API_URL/api/v1/users/keywords" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com",
    "keyword": "javascript"
  }'

# Get user sources
echo -e "\n\n3.7 Get User Source Preferences:"
curl -X GET "$API_URL/api/v1/users/sources?email=test@example.com" \
  -H "Accept: application/json"

# Add source preference
echo -e "\n\n3.8 Add Source Preference:"
curl -X POST "$API_URL/api/v1/users/sources" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com",
    "source": "LinkedIn"
  }'

# Remove source preference
echo -e "\n\n3.9 Remove Source Preference:"
curl -X DELETE "$API_URL/api/v1/users/sources" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com",
    "source": "LinkedIn"
  }'

# =============================================================================
# 4. MOBILE-SPECIFIC ENDPOINTS
# =============================================================================
echo -e "\n\n"
echo "📱 MOBILE-SPECIFIC ENDPOINTS"
echo "---------------------------"

# Get mobile app configuration (iOS)
echo "4.1 Get Mobile Config (iOS):"
curl -X GET "$API_URL/api/v1/mobile/config?platform=ios" \
  -H "Accept: application/json"

# Get mobile app configuration (Android)
echo -e "\n\n4.2 Get Mobile Config (Android):"
curl -X GET "$API_URL/api/v1/mobile/config?platform=android" \
  -H "Accept: application/json"

# Track app launch
echo -e "\n\n4.3 Track App Launch:"
curl -X POST "$API_URL/api/v1/mobile/app-launch" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "platform": "ios",
    "appVersion": "1.0.0",
    "buildNumber": "100",
    "deviceModel": "iPhone 14",
    "osVersion": "16.0",
    "isFirstLaunch": false,
    "sessionId": "mobile-session-12345"
  }'

# Get featured jobs for mobile
echo -e "\n\n4.4 Get Featured Jobs (Basic):"
curl -X GET "$API_URL/api/v1/mobile/jobs/featured?limit=5" \
  -H "Accept: application/json"

# Get personalized featured jobs
echo -e "\n\n4.5 Get Personalized Featured Jobs:"
curl -X GET "$API_URL/api/v1/mobile/jobs/featured?limit=5&userEmail=test@example.com" \
  -H "Accept: application/json"

# Submit app feedback
echo -e "\n\n4.6 Submit App Feedback:"
curl -X POST "$API_URL/api/v1/mobile/feedback" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@example.com",
    "type": "feature",
    "subject": "Great app!",
    "message": "Love the job search functionality. Could use dark mode.",
    "rating": 5,
    "appVersion": "1.0.0",
    "deviceInfo": {
      "model": "iPhone 14",
      "os": "iOS 16.0"
    }
  }'

# Get user mobile stats
echo -e "\n\n4.7 Get User Mobile Stats:"
curl -X GET "$API_URL/api/v1/mobile/stats/user?email=test@example.com" \
  -H "Accept: application/json"

# =============================================================================
# TEST SUMMARY
# =============================================================================
echo -e "\n\n"
echo "🎯 TEST SUMMARY"
echo "==============="
echo "✅ All curl commands have been executed for: $API_URL"
echo "📊 Check the responses above for:"
echo "   - HTTP status codes (200, 201, 404, 500, etc.)"
echo "   - JSON response structure"
echo "   - Error handling"
echo "   - Data validation"
echo ""
echo "🔧 Common expected results:"
echo "   - Health checks: status 200 with 'healthy' status"
echo "   - Jobs API: status 200 with job listings"
echo "   - User registration: status 201 for new users"
echo "   - Invalid requests: status 400/404 with error messages"
echo ""
echo "🚀 Your API is ready for mobile app integration!"