#!/bin/bash

# Simple test for the new BirJob backend URL
API_URL="https://birjobbackend-ir3e.onrender.com"

echo "🧪 Testing BirJob Backend API"
echo "URL: $API_URL"
echo "=============================="

# Test 1: Basic connectivity
echo "1. 🌐 Basic Connectivity Test:"
if curl -s --max-time 10 "$API_URL/api/health" > /dev/null; then
    echo "   ✅ API is reachable"
else
    echo "   ❌ API is not reachable or timed out"
    exit 1
fi

# Test 2: Health check response
echo "2. 🏥 Health Check:"
HEALTH_RESPONSE=$(curl -s --max-time 10 "$API_URL/api/health")
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "   ✅ API is healthy"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "   ⚠️  API response: $HEALTH_RESPONSE"
fi

# Test 3: Database connection
echo "3. 🗄️ Database Test:"
DB_RESPONSE=$(curl -s --max-time 15 "$API_URL/api/health/database")
if echo "$DB_RESPONSE" | grep -q '"status":"healthy"'; then
    echo "   ✅ Database is connected"
else
    echo "   ⚠️  Database response: $DB_RESPONSE"
fi

# Test 4: Jobs API test
echo "4. 💼 Jobs API Test:"
JOBS_RESPONSE=$(curl -s --max-time 15 "$API_URL/api/v1/jobs?limit=1")
if echo "$JOBS_RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ Jobs API is working"
    JOB_COUNT=$(echo "$JOBS_RESPONSE" | grep -o '"totalJobs":[0-9]*' | cut -d':' -f2)
    echo "   📊 Total jobs in database: $JOB_COUNT"
else
    echo "   ⚠️  Jobs API response: $JOBS_RESPONSE"
fi

# Test 5: Mobile API test
echo "5. 📱 Mobile Config Test:"
MOBILE_RESPONSE=$(curl -s --max-time 10 "$API_URL/api/v1/mobile/config?platform=ios")
if echo "$MOBILE_RESPONSE" | grep -q '"success":true'; then
    echo "   ✅ Mobile API is working"
else
    echo "   ⚠️  Mobile API response: $MOBILE_RESPONSE"
fi

echo ""
echo "🎉 Basic validation completed!"
echo ""
echo "📱 Your mobile app can use this base URL:"
echo "   $API_URL/api/v1"
echo ""
echo "🔍 API Documentation available at:"
echo "   $API_URL/api/health/detailed"
echo ""
echo "⚡ For comprehensive testing, run:"
echo "   ./scripts/quick_test.sh"