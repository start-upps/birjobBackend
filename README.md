# iOS Job App Backend

A clean, simplified FastAPI backend for the iOS job application with proper RDBMS relationships.

## 🚀 Features

- **Clean Architecture**: Simple, focused codebase without unnecessary complexity
- **RDBMS Design**: Proper foreign key relationships and data integrity
- **RESTful API**: Well-designed endpoints for mobile app integration
- **User Management**: Email and device-based user management
- **Job Management**: Save, view, and search job listings
- **Push Notifications**: Device token management for notifications
- **Simple Analytics**: Basic job viewing analytics without overcomplicated tables

## 📊 Database Schema

### Core Tables

1. **users** - Core user information
   - `id` (UUID, Primary Key)
   - `email` (Unique)
   - `keywords` (JSONB) - Job search preferences
   - `preferred_sources` (JSONB) - Preferred job sources
   - `notifications_enabled` (Boolean)
   - `created_at`, `updated_at` (Timestamps)

2. **device_tokens** - Device registration for push notifications
   - `id` (UUID, Primary Key)
   - `user_id` (UUID, Foreign Key → users.id)
   - `device_id` (String, Unique) - Device identifier
   - `device_token` (String) - Push notification token
   - `device_info` (JSONB) - Device metadata
   - `is_active` (Boolean)
   - `registered_at`, `updated_at` (Timestamps)

3. **saved_jobs** - User bookmarked jobs
   - `id` (UUID, Primary Key)
   - `user_id` (UUID, Foreign Key → users.id)
   - `job_id` (Integer) - Reference to scraper.jobs_jobpost
   - `job_title`, `job_company`, `job_source` (Cached data)
   - `created_at` (Timestamp)

4. **job_views** - Simple job viewing analytics
   - `id` (UUID, Primary Key)
   - `user_id` (UUID, Foreign Key → users.id)
   - `job_id` (Integer) - Reference to scraper.jobs_jobpost
   - `job_title`, `job_company`, `job_source` (Cached data)
   - `view_duration_seconds` (Integer)
   - `viewed_at` (Timestamp)

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- Redis (optional)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost/birjob_ios
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
API_KEY=your-api-key
```

### Database Setup
The database has been cleaned up and simplified. The schema includes:

**✅ Current Schema Status:**
- ✅ 5 core tables with proper RDBMS relationships
- ✅ All foreign key constraints in place
- ✅ Unique constraints applied
- ✅ Performance indexes created
- ✅ 10 unnecessary analytics tables removed

**Tables:**
1. `users` - Core user information
2. `device_tokens` - Device registration (linked to users)
3. `saved_jobs` - User bookmarks (linked to users)
4. `job_views` - Job viewing history (linked to users)
5. `user_analytics` - Simple user analytics (linked to users)

**Foreign Key Relationships:**
- `device_tokens.user_id → users.id`
- `saved_jobs.user_id → users.id` 
- `job_views.user_id → users.id`
- `user_analytics.user_id → users.id`

### Run the Application
```bash
# Development
python main.py

# Production
python run.py
```

## 📡 API Endpoints

### Health & Info
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/health/status` - Detailed health status

### User Management
- `POST /api/v1/users/register` - Register new user with device
- `GET /api/v1/users/profile/{device_id}` - Get user profile
- `PUT /api/v1/users/profile` - Create/update user profile
- `PUT /api/v1/users/{device_id}` - Update user by device ID

### Email-based User Management (Website)
- `GET /api/v1/users/by-email?email=...` - Get/create user by email
- `POST /api/v1/users/keywords/email` - Add keyword by email
- `DELETE /api/v1/users/keywords/email?email=...&keyword=...` - Remove keyword

### Job Management
- `GET /api/v1/jobs/` - List jobs with filters
- `GET /api/v1/jobs/{job_id}` - Get job details
- `GET /api/v1/jobs/stats/summary` - Job statistics
- `POST /api/v1/jobs/save` - Save job for user
- `DELETE /api/v1/jobs/unsave` - Remove saved job
- `GET /api/v1/jobs/saved/{device_id}` - Get user's saved jobs
- `POST /api/v1/jobs/view` - Record job view

### Device Management
- `POST /api/v1/devices/register` - Register device for notifications
- `DELETE /api/v1/devices/{device_id}` - Unregister device
- `GET /api/v1/devices/{device_id}/status` - Get device status

### Analytics
- `POST /api/v1/analytics/event` - Record user analytics event
- `GET /api/v1/analytics/user/{device_id}` - Get user analytics summary
- `GET /api/v1/analytics/stats` - Get overall analytics statistics
- `DELETE /api/v1/analytics/user/{device_id}` - Clear user analytics (GDPR)

### Gemini AI Chatbot
- `POST /api/v1/chatbot/chat` - Chat with AI job search assistant
- `POST /api/v1/chatbot/recommendations` - Get personalized job recommendations
- `POST /api/v1/chatbot/analyze-job` - Analyze job posting with AI insights
- `GET /api/v1/chatbot/stats` - Get chatbot usage statistics

## 🏗 Project Structure

```
birjobBackend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── devices.py     # Device management
│   │   │   ├── health.py      # Health checks
│   │   │   ├── jobs.py        # Job operations
│   │   │   └── users.py       # User management
│   │   └── router.py          # API router
│   ├── core/
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # Database connection
│   │   └── redis_client.py    # Redis client
│   ├── models/
│   │   ├── device.py          # Device model
│   │   └── user.py            # User models
│   ├── schemas/
│   │   ├── device.py          # Device schemas
│   │   └── user.py            # User schemas
│   └── services/
│       └── push_notifications.py
├── main.py                    # FastAPI app
├── run.py                     # Production runner
├── simple_schema.sql          # Database schema
└── requirements.txt           # Dependencies
```

## 🔧 What Was Cleaned Up

### Removed Files
- `analytics_schema.sql` - Overcomplicated analytics schema
- `app/models/analytics.py` - Complex analytics models
- `app/schemas/analytics.py` - Analytics schemas
- `app/api/v1/endpoints/analytics.py` - Analytics endpoints
- Various SQL fix files and documentation files
- Deployment test files

### Simplified Features
- **Analytics**: Reduced from 6 complex tables to simple `job_views` table
- **User Model**: Removed analytics relationships, kept core functionality
- **Database Schema**: Clean 4-table design with proper foreign keys
- **API**: Focused on essential endpoints for mobile app

### Improved Architecture
- **RDBMS Compliance**: Proper foreign key relationships
- **Data Integrity**: Cascade deletes and constraints
- **Performance**: Optimized indexes
- **Maintainability**: Simple, focused codebase

## 📝 Usage Examples

### Register User
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-123",
    "email": "user@example.com",
    "keywords": ["python", "backend"],
    "notifications_enabled": true
  }'
```

### Get Jobs
```bash
curl "http://localhost:8000/api/v1/jobs/?search=python&limit=10"
```

### Save Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/save" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-123",
    "job_id": 12345
  }'
```

### Record Analytics Event
```bash
curl -X POST "http://localhost:8000/api/v1/analytics/event" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-123",
    "action_type": "job_view",
    "action_data": {"job_id": 12345, "duration": 30},
    "session_id": "session-456"
  }'
```

### Chat with AI Assistant
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-123",
    "message": "How can I improve my resume for backend developer roles?",
    "include_user_context": true
  }'
```

### Get Job Recommendations
```bash
curl -X POST "http://localhost:8000/api/v1/chatbot/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device-123",
    "keywords": ["python", "fastapi"],
    "location": "Baku"
  }'
```

## 🚦 Development

### Running Tests
```bash
# No test framework currently installed
# Add pytest for testing: pip install pytest
```

### Database Migration
```bash
# Apply the simple schema
psql -d birjob_ios -f simple_schema.sql
```

## 📄 License

This project is licensed under the MIT License.