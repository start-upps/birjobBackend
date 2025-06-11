#!/bin/bash

# iOS Backend API Test Script
# This script demonstrates all the API endpoints

echo "🚀 iOS Backend API Endpoints Demo"
echo "================================="

BASE_URL="http://localhost:8000"

echo ""
echo "📱 1. Device Registration"
echo "POST $BASE_URL/api/v1/devices/register"
echo "Request:"
cat << 'EOF'
{
  "device_token": "a1b2c3d4e5f6789012345678901234567890abcdef",
  "device_info": {
    "os_version": "17.2",
    "app_version": "1.0.0",
    "device_model": "iPhone15,2",
    "timezone": "America/New_York"
  }
}
EOF

echo ""
echo "Expected Response:"
cat << 'EOF'
{
  "success": true,
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "registered_at": "2024-01-15T10:30:00Z"
  }
}
EOF

echo ""
echo "🔍 2. Keyword Subscription"
echo "POST $BASE_URL/api/v1/keywords"
echo "Request:"
cat << 'EOF'
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keywords": ["Python", "Senior Developer", "Remote"],
  "sources": ["linkedin", "indeed"],
  "location_filters": {
    "cities": ["New York", "San Francisco"],
    "remote_only": true
  }
}
EOF

echo ""
echo "💼 3. Get Job Matches"
echo "GET $BASE_URL/api/v1/matches/{device_id}?limit=20&offset=0"
echo "Expected Response:"
cat << 'EOF'
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "770e8400-e29b-41d4-a716-446655440002",
        "job": {
          "id": 12345,
          "title": "Senior Python Developer",
          "company": "TechCorp Inc.",
          "apply_link": "https://example.com/apply/12345",
          "source": "linkedin",
          "posted_at": "2024-01-16T08:00:00Z"
        },
        "matched_keywords": ["Python", "Senior Developer"],
        "relevance_score": 0.85,
        "matched_at": "2024-01-16T08:30:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
EOF

echo ""
echo "🔍 4. Health Check"
echo "GET $BASE_URL/api/v1/health"
echo "Expected Response:"
cat << 'EOF'
{
  "status": "healthy",
  "timestamp": "2024-01-16T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy", 
    "apns": "healthy",
    "scraper": "healthy"
  },
  "metrics": {
    "active_devices": 1250,
    "active_subscriptions": 3400,
    "matches_last_24h": 890,
    "notifications_sent_last_24h": 245
  }
}
EOF

echo ""
echo "📊 5. All Available Endpoints:"
echo ""
echo "Device Management:"
echo "  POST   /api/v1/devices/register"
echo "  DELETE /api/v1/devices/{device_id}"
echo "  GET    /api/v1/devices/{device_id}/status"
echo ""
echo "Keyword Subscriptions:"
echo "  POST   /api/v1/keywords"
echo "  GET    /api/v1/keywords/{device_id}"
echo "  PUT    /api/v1/keywords/{subscription_id}"
echo "  DELETE /api/v1/keywords/{subscription_id}"
echo ""
echo "Job Matches:"
echo "  GET    /api/v1/matches/{device_id}"
echo "  POST   /api/v1/matches/{match_id}/read"
echo "  GET    /api/v1/matches/{device_id}/unread-count"
echo ""
echo "Health & Monitoring:"
echo "  GET    /api/v1/health"
echo "  GET    /api/v1/health/status/scraper"
echo "  GET    /metrics"
echo ""
echo "✨ Backend Features:"
echo "  ✅ Complete REST API with all specified endpoints"
echo "  ✅ PostgreSQL with iosapp schema integration"
echo "  ✅ Redis caching for performance"
echo "  ✅ Background job matching engine (every 5 minutes)"
echo "  ✅ Apple Push Notifications with smart throttling"
echo "  ✅ JWT authentication for devices"
echo "  ✅ Rate limiting and security headers"
echo "  ✅ Prometheus metrics and health monitoring"
echo "  ✅ Docker containerization for easy deployment"
echo "  ✅ Nginx load balancer configuration"
echo "  ✅ Production-ready scaling support"
echo ""
echo "🔗 Integration:"
echo "  • Seamlessly integrates with existing scraper"
echo "  • Reads from scraper.jobs_jobpost table"
echo "  • No changes needed to existing scraper code"
echo "  • Creates matches in iosapp schema"
echo "  • Sends push notifications for matches"

echo ""
echo "🚀 To start the backend:"
echo "  docker-compose up -d"
echo ""
echo "📖 API Documentation will be available at:"
echo "  http://localhost:8000/docs"