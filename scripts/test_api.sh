#!/bin/bash

# Simple BirJob API Validator
# Usage: ./test_api.sh https://your-app-name.onrender.com

if [ -z "$1" ]; then
    echo "❌ Please provide your Render URL:"
    echo "Usage: $0 https://your-app-name.onrender.com"
    exit 1
fi

API_URL="$1"
PASSED=0
FAILED=0

echo "🧪 Testing BirJob API: $API_URL"
echo "================================"

# Test function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_code="$5"
    
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ]; then
        response_code=$(curl -s -w "%{http_code}" -X POST "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" -o /dev/null)
    else
        response_code=$(curl -s -w "%{http_code}" "$API_URL$endpoint" -o /dev/null)
    fi
    
    if [ "$response_code" = "$expected_code" ]; then
        echo "✅ PASS ($response_code)"
        ((PASSED++))
    else
        echo "❌ FAIL (got $response_code, expected $expected_code)"
        ((FAILED++))
    fi
}

# Run tests
test_endpoint "Health Check" "GET" "/api/health" "" "200"
test_endpoint "Jobs API" "GET" "/api/v1/jobs" "" "200"
test_endpoint "Job Sources" "GET" "/api/v1/jobs/meta/sources" "" "200"
test_endpoint "User Registration" "POST" "/api/v1/users/register" '{"email":"test-'$(date +%s)'@example.com"}' "201"
test_endpoint "Mobile Config" "GET" "/api/v1/mobile/config?platform=ios" "" "200"
test_endpoint "Database Health" "GET" "/api/health/database" "" "200"
test_endpoint "Invalid Endpoint" "GET" "/api/v1/nonexistent" "" "404"

# Summary
echo ""
echo "📊 Test Summary:"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed! Your API is working correctly."
    exit 0
else
    echo "⚠️  Some tests failed. Check your API configuration."
    exit 1
fi