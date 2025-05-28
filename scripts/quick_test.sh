#!/bin/bash

# Quick BirJob API Tests - Essential Endpoints Only
# Replace YOUR_URL with your actual Render URL

URL="https://birjobbackend.onrender.com"

echo "🚀 Quick BirJob API Tests"
echo "========================="

# 1. Health Check
echo "1. 🏥 Health Check:"
curl -s "$URL/api/health" | jq '.'

# 2. Jobs API
echo -e "\n2. 💼 Jobs API (first 3 jobs):"
curl -s "$URL/api/v1/jobs?limit=3" | jq '.success, .data.metadata.totalJobs, .data.jobs[0:2] | {title: .title, company: .company}'

# 3. User Registration
echo -e "\n3. 👤 User Registration:"
curl -s -X POST "$URL/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"quicktest@example.com"}' | jq '.success, .message'

# 4. Add User Keyword
echo -e "\n4. 🔑 Add Keyword:"
curl -s -X POST "$URL/api/v1/users/keywords" \
  -H "Content-Type: application/json" \
  -d '{"email":"quicktest@example.com","keyword":"developer"}' | jq '.success, .message'

# 5. Get User Profile
echo -e "\n5. 👥 User Profile:"
curl -s "$URL/api/v1/users/profile?email=quicktest@example.com" | jq '.success, .data.user.email, .data.stats'

# 6. Job Sources
echo -e "\n6. 📊 Job Sources:"
curl -s "$URL/api/v1/jobs/meta/sources" | jq '.success, .data.totalSources, .data.sources[0:3]'

# 7. Mobile Config
echo -e "\n7. 📱 Mobile Config:"
curl -s "$URL/api/v1/mobile/config?platform=ios" | jq '.success, .data.app.name, .data.features | keys'

# 8. Database Health
echo -e "\n8. 🗄️ Database Health:"
curl -s "$URL/api/health/database" | jq '.status, .connection.status'

echo -e "\n✅ Quick tests completed!"
echo "🔧 For full test suite, run the complete version"