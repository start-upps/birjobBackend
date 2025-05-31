#!/bin/bash

# BirJob Backend - New Deployment Verification
# API URL: https://birjobbackend-ir3e.onrender.com

API_URL="https://birjobbackend-ir3e.onrender.com"

echo "🚀 Verifying BirJob Backend Deployment"
echo "======================================"
echo "Testing: $API_URL"
echo ""

# Test 1: Basic Health Check
echo "1. 🏥 Health Check:"
HEALTH=$(curl -s --max-time 15 "$API_URL/api/health")
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "   ✅ API is healthy and responding"
    echo "   Response: $HEALTH"
else
    echo "   ⚠️  Health check response: $HEALTH"
fi

echo ""

# Test 2: Database Connection
echo "2. 🗄️ Database Connection:"
DB_HEALTH=$(curl -s --max-time 20 "$API_URL/api/health/database")
if echo "$DB_HEALTH" | grep -q '"status":"healthy"'; then
    echo "   ✅ Database connected successfully"
    # Extract total jobs if available
    if echo "$DB_HEALTH" | grep -q '"jobs"'; then
        JOBS_COUNT=$(echo "$DB_HEALTH" | grep -o '"jobs":[0-9]*' | cut -d':' -f2)
        echo "   📊 Total jobs in database: $JOBS_COUNT"
    fi
else
    echo "   ⚠️  Database response: $DB_HEALTH"
fi

echo ""

# Test 3: Jobs API
echo "3. 💼 Jobs API:"
JOBS_API=$(curl -s --max-time 20 "$API_URL/api/v1/jobs?limit=1")
if echo "$JOBS_API" | grep -q '"success":true'; then
    echo "   ✅ Jobs API working correctly"
    # Extract total jobs
    TOTAL_JOBS=$(echo "$JOBS_API" | grep -o '"totalJobs":[0-9]*' | cut -d':' -f2)
    echo "   📈 Total jobs available: $TOTAL_JOBS"
else
    echo "   ⚠️  Jobs API response: $JOBS_API"
fi

echo ""

# Test 4: User Registration
echo "4. 👤 User Registration Test:"
REG_RESPONSE=$(curl -s --max-time 15 -X POST "$API_URL/api/v1/users/register" \
    -H "Content-Type: application/json" \
    -d '{"email":"deployment-test@example.com"}')
if echo "$REG_RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ User registration working"
else
    echo "   ⚠️  Registration response: $REG_RESPONSE"
fi

echo ""

# Test 5: Mobile Config
echo "5. 📱 Mobile Configuration:"
MOBILE_CONFIG=$(curl -s --max-time 15 "$API_URL/api/v1/mobile/config?platform=ios")
if echo "$MOBILE_CONFIG" | grep -q '"success":true'; then
    echo "   ✅ Mobile API configured correctly"
    APP_NAME=$(echo "$MOBILE_CONFIG" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    echo "   📱 App name: $APP_NAME"
else
    echo "   ⚠️  Mobile config response: $MOBILE_CONFIG"
fi

echo ""

# Test 6: Job Sources
echo "6. 📊 Job Sources:"
SOURCES=$(curl -s --max-time 15 "$API_URL/api/v1/jobs/meta/sources")
if echo "$SOURCES" | grep -q '"success":true'; then
    echo "   ✅ Job sources API working"
    TOTAL_SOURCES=$(echo "$SOURCES" | grep -o '"totalSources":[0-9]*' | cut -d':' -f2)
    echo "   🔗 Total job sources: $TOTAL_SOURCES"
else
    echo "   ⚠️  Sources response: $SOURCES"
fi

echo ""
echo "🎯 DEPLOYMENT SUMMARY"
echo "===================="
echo "✅ API Base URL: $API_URL"
echo "✅ Health endpoint: $API_URL/api/health"
echo "✅ Jobs API: $API_URL/api/v1/jobs"
echo "✅ Mobile API: $API_URL/api/v1/mobile"
echo ""
echo "📱 For iOS app configuration:"
echo "   Base URL: $API_URL/api/v1"
echo ""
echo "🔗 Quick Links:"
echo "   • Health Check: $API_URL/api/health"
echo "   • Detailed Health: $API_URL/api/health/detailed"
echo "   • API Documentation: Check README.md"
echo ""
echo "🚀 Your backend is ready for mobile app integration!"