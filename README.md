# 🚀 BirJob Mobile Backend API

A comprehensive Node.js backend service for the BirJob iOS and Android mobile applications, featuring automated job notifications, real-time analytics, advanced caching, and enterprise-grade monitoring.

![Node.js](https://img.shields.io/badge/Node.js-18.x-green.svg)
![Express](https://img.shields.io/badge/Express-4.x-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.x-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7.x-red.svg)
![Prisma](https://img.shields.io/badge/Prisma-5.x-black.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🌟 Overview

This backend API serves as the central hub for BirJob mobile applications, providing a robust, scalable, and secure foundation for job search and notification services in Azerbaijan.

### Key Capabilities
- **Job Data Management**: Integration with existing job scraping system and 50+ job sources
- **Smart Notifications**: iOS (APNs) and Android (FCM) push notifications with email fallback
- **User Management**: Personalized keywords, source preferences, and notification settings
- **Real-time Analytics**: Advanced user behavior tracking and search analytics
- **High-Performance Caching**: Multi-layer Redis caching with automatic invalidation
- **Enterprise Monitoring**: Comprehensive health checks, metrics, and alerting
- **Mobile-First Design**: Optimized APIs specifically designed for mobile applications

## ✨ Features

### 🔔 Smart Notification System
- **Keyword-based Job Alerts**: Automated notifications for matching jobs using advanced text matching
- **Multi-platform Support**: Native iOS APNs and Android FCM implementations
- **Email Fallback**: Backup email notifications with rich HTML templates
- **Bulk Processing**: Efficient batch notification handling for thousands of users
- **Delivery Tracking**: Complete notification delivery status and retry mechanisms

### 📊 Advanced Analytics & Insights
- **Search Behavior Tracking**: Detailed analysis of user search patterns and preferences
- **User Activity Monitoring**: Comprehensive visitor patterns and engagement metrics
- **Device Intelligence**: Advanced device fingerprinting and location analytics
- **Performance Metrics**: Real-time API response times and system health monitoring
- **Custom Events**: Flexible event tracking for mobile app interactions

### 🚀 High-Performance Architecture
- **Multi-layer Caching**: Redis-powered caching with intelligent invalidation strategies
- **Database Optimization**: Indexed queries, connection pooling, and query optimization
- **Rate Limiting**: Advanced protection against abuse with IP-based and user-based limits
- **Async Processing**: Non-blocking operations for maximum throughput
- **Load Balancing**: Docker-ready horizontal scaling capabilities

### 📱 Mobile-Optimized APIs
- **Minimal Data Transfer**: Optimized response sizes for mobile bandwidth
- **Offline Support**: Cached data strategies for poor connectivity scenarios
- **Platform-specific Features**: iOS and Android tailored functionality and configurations
- **App Configuration**: Dynamic feature flags and A/B testing capabilities
- **Crash Reporting**: Automated crash collection and analysis

### 🔐 Enterprise Security
- **Rate Limiting**: Multi-level protection with customizable thresholds
- **Input Validation**: Comprehensive request validation with sanitization
- **Error Handling**: Secure error responses that don't leak sensitive information
- **Security Headers**: Complete security header implementation
- **CORS Protection**: Configurable cross-origin resource sharing

### 🏥 Health Monitoring & Observability
- **Multi-level Health Checks**: Basic, detailed, database, and service-specific health endpoints
- **Performance Monitoring**: Real-time performance metrics and bottleneck identification
- **Automated Alerting**: Proactive monitoring with configurable thresholds
- **Log Aggregation**: Structured logging with multiple output formats
- **Metrics Collection**: Comprehensive system and application metrics

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Mobile Applications"
        A[iOS App] 
        B[Android App]
    end
    
    subgraph "Load Balancer & CDN"
        C[Nginx/Cloudflare]
    end
    
    subgraph "API Gateway Layer"
        D[Express.js API]
        E[Rate Limiting]
        F[Authentication]
        G[Request Validation]
    end
    
    subgraph "Business Logic Services"
        H[Job Service]
        I[Notification Service]  
        J[Analytics Service]
        K[User Service]
        L[Mobile Service]
    end
    
    subgraph "Data Layer"
        M[(PostgreSQL)]
        N[(Redis Cache)]
    end
    
    subgraph "External Services"
        O[Push Notifications<br/>APNs & FCM]
        P[Email Service<br/>SMTP]
        Q[Job Scraper<br/>Data Pipeline]
    end
    
    subgraph "Monitoring & Observability"
        R[Health Checks]
        S[Metrics Collection]
        T[Log Aggregation]
        U[Performance Monitoring]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    G --> I
    G --> J
    G --> K
    G --> L
    H --> M
    I --> N
    J --> N
    K --> M
    L --> N
    I --> O
    I --> P
    Q --> M
    D --> R
    D --> S
    D --> T
    D --> U
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18.x or higher
- **PostgreSQL** 15.x or higher  
- **Redis** 7.x or higher (optional but recommended)
- **npm** or **yarn**
- **Git**

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/Ismat-Samadov/birjobBackend.git
cd birjobBackend

# Install dependencies
npm install

# Generate Prisma client
npx prisma generate
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration with your values
nano .env
```

**Complete Environment Variables:**
```env
# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/birjob"

# Redis Configuration (Optional but recommended)
REDIS_URL="redis://localhost:6379"
# OR for Upstash (cloud Redis)
UPSTASH_REDIS_REST_URL="https://your-redis-url.upstash.io"
UPSTASH_REDIS_REST_TOKEN="your-token"

# Server Configuration
NODE_ENV="development"
PORT="3000"
JWT_SECRET="your-super-secret-jwt-key-min-32-chars"
LOG_LEVEL="info"

# Feature Flags
ENABLE_CRON_JOBS="true"
ENABLE_PUSH_NOTIFICATIONS="true"
ENABLE_EMAIL_NOTIFICATIONS="true"

# Push Notifications - Firebase (Android)
FIREBASE_PROJECT_ID="your-project-id"
FIREBASE_PRIVATE_KEY="your-private-key"
FIREBASE_CLIENT_EMAIL="your-service-account@project.iam.gserviceaccount.com"

# Push Notifications - Apple (iOS)
APPLE_TEAM_ID="your-team-id"
APPLE_KEY_ID="your-key-id"
APPLE_PRIVATE_KEY="your-private-key"
APPLE_BUNDLE_ID="com.birjob.app"

# Email Service Configuration
EMAIL_SERVICE="gmail"
EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT="587"
EMAIL_SECURE="false"
EMAIL_USER="your-email@gmail.com"
EMAIL_PASSWORD="your-app-password"
EMAIL_FROM="BirJob <noreply@birjob.az>"

# Analytics & Monitoring
LOG_RETENTION_DAYS="90"
TIMEZONE="Asia/Baku"

# Development Tools
DEBUG_SQL_QUERIES="false"
DEBUG_REDIS_OPERATIONS="false"
```

### 3. Database Setup

```bash
# Option 1: Use existing database (recommended)
# Make sure your DATABASE_URL points to existing BirJob database

# Option 2: Create new database and push schema
createdb birjob
npx prisma db push

# Option 3: Run migrations (if you have them)
npx prisma migrate deploy

# Verify database connection
npx prisma studio
```

### 4. Start Development Server

```bash
# Development mode with hot reload and detailed logging
npm run dev

# Production mode
npm start

# With debug logging
DEBUG=* npm run dev
```

**Expected Output:**
```
✅ Database connected successfully
⚠️ Redis not available, continuing without cache (if Redis not configured)
🚀 BirJob Mobile Backend running on port 3000
📱 API Base URL: http://localhost:3000/api/v1
🔍 Health Check: http://localhost:3000/api/health
📊 Environment: development
🕐 Timezone: Asia/Baku
```

### 5. Verify Installation

```bash
# Health check
curl http://localhost:3000/api/health

# Test basic API
curl http://localhost:3000/api/v1/jobs?limit=5

# Run comprehensive tests
./scripts/quick_test.sh
```

## 📚 API Documentation

### Base URLs
```
Development: http://localhost:3000/api/v1
Production:  https://api.birjob.az/api/v1
Staging:     https://birjobbackend.onrender.com/api/v1
```

### Authentication
Currently, the API uses email-based identification. JWT authentication is ready for future implementation.

### Response Format
All API responses follow a consistent structure:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "cached": false,
  "timestamp": "2025-05-28T10:30:00.000Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "name": "ValidationError",
    "message": "Invalid request parameters",
    "statusCode": 400,
    "timestamp": "2025-05-28T10:30:00.000Z",
    "details": [
      {
        "field": "email",
        "message": "Valid email is required"
      }
    ]
  }
}
```

### Core API Endpoints

#### 🏥 Health & Monitoring
```http
# Basic health check
GET /api/health
Response: { status: "healthy", timestamp: "...", uptime: 1234 }

# Detailed system health
GET /api/health/detailed
Response: { status: "healthy", services: {...}, system: {...} }

# Database health
GET /api/health/database
Response: { status: "healthy", connection: {...}, statistics: {...} }

# Redis health
GET /api/health/redis
Response: { status: "healthy", connection: {...} }

# System metrics
GET /api/health/metrics
Response: { uptime: {...}, system: {...}, database: {...} }

# Kubernetes probes
GET /api/health/ready   # Readiness probe
GET /api/health/live    # Liveness probe

# Performance testing
GET /api/health/performance?iterations=100
Response: { totalTime: "...", averageTime: "...", throughput: "..." }
```

#### 💼 Jobs API
```http
# Get job listings with advanced filtering
GET /api/v1/jobs?search=developer&source=LinkedIn&page=1&limit=20
Response: {
  "jobs": [...],
  "metadata": {
    "totalJobs": 1234,
    "currentPage": 1,
    "totalPages": 62,
    "hasNextPage": true
  }
}

# Get specific job with similar jobs
GET /api/v1/jobs/:id
Response: {
  "job": {...},
  "similarJobs": [...],
  "company": { "name": "...", "totalJobs": 15 }
}

# Get all job sources with statistics
GET /api/v1/jobs/meta/sources
Response: {
  "sources": [
    { "name": "LinkedIn", "count": 450, "percentage": 35 }
  ],
  "totalSources": 12,
  "totalJobs": 1284
}

# Get top companies
GET /api/v1/jobs/meta/companies
Response: {
  "companies": [
    { "name": "Google", "jobCount": 25 }
  ]
}

# Get job market trends (last 30 days)
GET /api/v1/jobs/meta/trends
Response: {
  "dailyTrends": [...],
  "sourceBreakdown": [...],
  "topCompanies": [...],
  "summary": {
    "totalJobs": 1500,
    "averagePerDay": 50
  }
}
```

#### 👤 User Management
```http
# Register new user
POST /api/v1/users/register
Body: { "email": "user@example.com" }
Response: { "user": { "id": 1, "email": "...", "memberSince": "..." } }

# Get comprehensive user profile
GET /api/v1/users/profile?email=user@example.com
Response: {
  "user": {...},
  "keywords": [...],
  "sourcePreferences": [...],
  "recentNotifications": [...],
  "stats": {
    "totalKeywords": 5,
    "totalNotifications": 23,
    "unreadNotifications": 3
  }
}

# Manage user keywords
GET /api/v1/users/keywords?email=user@example.com
POST /api/v1/users/keywords
Body: { "email": "user@example.com", "keyword": "javascript" }
DELETE /api/v1/users/keywords
Body: { "email": "user@example.com", "keyword": "javascript" }

# Manage source preferences
GET /api/v1/users/sources?email=user@example.com
POST /api/v1/users/sources
Body: { "email": "user@example.com", "source": "LinkedIn" }
DELETE /api/v1/users/sources
Body: { "email": "user@example.com", "source": "LinkedIn" }
```

#### 🔔 Notifications
```http
# Get user notifications with filtering
GET /api/v1/notifications?email=user@example.com&page=1&limit=20&unreadOnly=false
Response: {
  "notifications": [...],
  "metadata": {
    "totalNotifications": 45,
    "unreadCount": 3,
    "hasNextPage": true
  }
}

# Register device for push notifications
POST /api/v1/notifications/register-device
Body: {
  "email": "user@example.com",
  "deviceToken": "device-token-here",
  "platform": "ios", // or "android"
  "appVersion": "1.0.0",
  "deviceModel": "iPhone 14"
}

# Send immediate notification (admin/testing)
POST /api/v1/notifications/send
Body: {
  "email": "user@example.com",
  "title": "New Job Alert!",
  "body": "Software Engineer at Google",
  "data": { "jobId": "123", "type": "job_alert" }
}

# Mark notification as read
PUT /api/v1/notifications/:id/read

# Unregister device
DELETE /api/v1/notifications/device
Body: { "email": "user@example.com" }
```

#### 📊 Analytics
```http
# Log search activity
POST /api/v1/analytics/search
Body: {
  "query": "software engineer",
  "resultCount": 25,
  "searchDuration": 150,
  "clickedResult": true,
  "deviceType": "mobile",
  "sessionId": "session-123"
}

# Log visitor activity
POST /api/v1/analytics/visitor
Body: {
  "visitorId": "visitor-123",
  "sessionId": "session-123",
  "path": "/api/v1/jobs",
  "referrer": "https://google.com",
  "deviceType": "mobile",
  "screenWidth": 375,
  "screenHeight": 812
}

# Get search analytics
GET /api/v1/analytics/search-stats?period=week&limit=20
Response: {
  "summary": {
    "totalSearches": 1500,
    "uniqueQueries": 450,
    "averageResultsPerSearch": 18.5
  },
  "topQueries": [...],
  "deviceBreakdown": [...],
  "dailyTrends": [...]
}

# Get visitor analytics
GET /api/v1/analytics/visitor-stats?period=month
Response: {
  "summary": {
    "totalVisitors": 5000,
    "uniqueVisitors": 3200,
    "pageViews": 15000
  },
  "topPages": [...],
  "deviceStats": [...],
  "topCountries": [...]
}
```

#### 📱 Mobile-Specific APIs
```http
# Get platform-specific app configuration
GET /api/v1/mobile/config?platform=ios
Response: {
  "app": {
    "currentVersion": "1.0.0",
    "minimumVersion": "1.0.0",
    "updateRequired": false
  },
  "features": {
    "pushNotifications": true,
    "darkMode": true,
    "offlineMode": false
  },
  "api": { "baseUrl": "...", "timeout": 30000 },
  "ios": { "appStoreId": "123456789" }
}

# Track app launch
POST /api/v1/mobile/app-launch
Body: {
  "platform": "ios",
  "appVersion": "1.0.0",
  "deviceModel": "iPhone 14",
  "osVersion": "16.0",
  "isFirstLaunch": false
}

# Get personalized featured jobs
GET /api/v1/mobile/jobs/featured?limit=10&userEmail=user@example.com
Response: {
  "jobs": [...],
  "metadata": {
    "isPersonalized": true,
    "lastUpdated": "..."
  }
}

# Submit app feedback
POST /api/v1/mobile/feedback
Body: {
  "email": "user@example.com",
  "type": "bug", // "bug", "feature", "general", "rating"
  "subject": "App crashes on startup",
  "message": "The app crashes when I try to open it...",
  "rating": 3,
  "appVersion": "1.0.0",
  "deviceInfo": { "model": "iPhone 14", "os": "iOS 16.0" }
}

# Get user mobile statistics
GET /api/v1/mobile/stats/user?email=user@example.com
Response: {
  "activity": {
    "totalKeywords": 5,
    "notificationsLast30Days": 12
  },
  "engagement": {
    "notificationReadRate": 85,
    "averageNotificationsPerWeek": 3
  },
  "recommendations": {
    "addMoreKeywords": true,
    "enableMoreSources": false
  }
}

# Report app crash
POST /api/v1/mobile/crash-report
Body: {
  "platform": "ios",
  "appVersion": "1.0.0",
  "crashLog": "Fatal error in JobsViewController...",
  "stackTrace": "...",
  "deviceInfo": { "model": "iPhone 14", "memory": "6GB" }
}
```

### API Rate Limits
- **General API**: 1000 requests per 15 minutes per IP
- **Sensitive endpoints** (notifications): 100 requests per 15 minutes per IP
- **Health checks**: No rate limiting

### Pagination
All list endpoints support pagination:
```http
GET /api/v1/jobs?page=2&limit=25
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "metadata": {
    "currentPage": 2,
    "totalPages": 50,
    "hasNextPage": true,
    "hasPreviousPage": true,
    "totalItems": 1250,
    "itemsPerPage": 25
  }
}
```

## ⚙️ Configuration

### Environment Variables

The application supports extensive configuration through environment variables:

#### Core Configuration
```env
# Server
NODE_ENV=production|development|staging
PORT=3000
TIMEZONE=Asia/Baku

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (Optional)
REDIS_URL=redis://localhost:6379
# OR Upstash Cloud Redis
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...

# Security
JWT_SECRET=your-secret-min-32-chars
```

#### Feature Toggles
```env
ENABLE_CRON_JOBS=true
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_EMAIL_NOTIFICATIONS=true
```

#### Push Notifications
```env
# Firebase (Android)
FIREBASE_PROJECT_ID=your-project
FIREBASE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
FIREBASE_CLIENT_EMAIL=service-account@project.iam.gserviceaccount.com

# Apple Push (iOS)
APPLE_TEAM_ID=ABC123DEF4
APPLE_KEY_ID=KEY123
APPLE_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----...
APPLE_BUNDLE_ID=com.birjob.app
```

#### Email Configuration
```env
EMAIL_SERVICE=gmail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_SECURE=false
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=BirJob <noreply@birjob.az>
```

#### Monitoring & Logging
```env
LOG_LEVEL=info|debug|warn|error
LOG_RETENTION_DAYS=90
DEBUG_SQL_QUERIES=false
DEBUG_REDIS_OPERATIONS=false
```

### Caching Strategy

The application uses a sophisticated multi-layer caching strategy:

```javascript
const CACHE_DURATIONS = {
  JOBS_LIST: 5 * 60,        // 5 minutes - frequently updated
  JOBS_SEARCH: 3 * 60,      // 3 minutes - user-specific  
  JOBS_METADATA: 15 * 60,   // 15 minutes - stable data
  USER_DATA: 30 * 60,       // 30 minutes - personal data
  ANALYTICS: 60 * 60,       // 1 hour - aggregated data
  SOURCES: 24 * 60 * 60,    // 24 hours - rarely changing
  COMPANIES: 12 * 60 * 60,  // 12 hours - semi-static
  TRENDS: 6 * 60 * 60,      // 6 hours - daily trends
};
```

Cache keys follow a hierarchical pattern:
```
jobs:all:all:all:1:20           # General job listing
jobs:developer:LinkedIn:all:1:10 # Filtered search
user:email@example.com:keywords  # User-specific data
analytics:search:week           # Analytics data
```

### Database Optimization

**Essential Indexes:**
```sql
-- Performance-critical indexes
CREATE INDEX CONCURRENTLY idx_jobs_created_at ON jobs_jobpost(created_at DESC);
CREATE INDEX CONCURRENTLY idx_jobs_company_lower ON jobs_jobpost(LOWER(company));
CREATE INDEX CONCURRENTLY idx_jobs_title_gin ON jobs_jobpost USING gin(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY idx_jobs_source ON jobs_jobpost(source);

-- User and notification indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_keywords_user_id ON keywords(userId);
CREATE INDEX CONCURRENTLY idx_notifications_user_id ON notifications(userId);
CREATE INDEX CONCURRENTLY idx_notifications_read ON notifications(isRead);

-- Analytics indexes
CREATE INDEX CONCURRENTLY idx_search_logs_timestamp ON search_logs(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_search_logs_query ON search_logs(query);
CREATE INDEX CONCURRENTLY idx_visitor_logs_timestamp ON visitor_logs(timestamp DESC);
```

## 🐳 Deployment

### Docker Deployment (Recommended)

#### Option 1: Docker Compose (Full Stack)
```bash
# Production deployment
docker-compose up -d

# With monitoring stack
docker-compose --profile monitoring up -d

# Development with live reload
docker-compose --profile development up api-dev postgres redis
```

#### Option 2: Single Container
```bash
# Build production image
docker build --target runtime -t birjob-backend:latest .

# Run container
docker run -d \
  --name birjob-api \
  -p 3000:3000 \
  -e DATABASE_URL="your-db-url" \
  -e REDIS_URL="your-redis-url" \
  birjob-backend:latest
```

### Cloud Deployment

#### Render (Recommended)
The project includes `render.yaml` for one-click deployment:

```yaml
services:
  - type: web
    name: birjob-backend
    env: node
    plan: starter
    buildCommand: npm install && npx prisma generate
    startCommand: npm start
    healthCheckPath: /api/health
    envVars:
      - key: NODE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: birjob-postgres
          property: connectionString
```

**Deploy to Render:**
1. Fork this repository
2. Connect to Render
3. Deploy from `render.yaml`
4. Add environment variables

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

#### Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

#### AWS/GCP/Azure
Use the provided Dockerfile with your preferred container orchestration:
- **ECS/Fargate** (AWS)
- **Cloud Run** (GCP)
- **Container Instances** (Azure)
- **Kubernetes** (any cloud)

### Environment-Specific Configuration

#### Production
```env
NODE_ENV=production
LOG_LEVEL=warn
ENABLE_CRON_JOBS=true
```

#### Staging
```env
NODE_ENV=staging
LOG_LEVEL=info
ENABLE_CRON_JOBS=false
```

#### Development
```env
NODE_ENV=development
LOG_LEVEL=debug
ENABLE_CRON_JOBS=false
DEBUG_SQL_QUERIES=true
```

## 🛠️ Development

### Project Structure

```
birjobBackend/
├── server.js                  # Main application entry point
├── package.json              # Dependencies and scripts
├── prisma/
│   └── schema.prisma         # Database schema
├── routes/                   # API route handlers
│   ├── health.js            # Health monitoring endpoints
│   ├── jobs.js              # Job-related endpoints
│   ├── users.js             # User management
│   ├── notifications.js     # Push notifications
│   ├── analytics.js         # Analytics tracking
│   └── mobile.js            # Mobile-specific APIs
├── services/                 # Business logic services
│   ├── pushNotifications.js # Push notification service
│   └── emailService.js      # Email service
├── middleware/               # Express middleware
│   └── errorHandler.js      # Error handling
├── utils/                    # Utility functions
│   ├── database.js          # Prisma client and utilities
│   ├── redis.js             # Redis cache utilities
│   ├── logger.js            # Winston logging configuration
│   └── cronJobs.js          # Scheduled tasks
├── logs/                     # Application logs
├── scripts/                  # Utility scripts
│   ├── quick_test.sh        # Quick API testing
│   ├── advance_test.sh      # Comprehensive testing
│   └── test_api.sh          # API validation
├── docker-compose.yml        # Docker orchestration
├── Dockerfile               # Container configuration
├── render.yaml              # Render deployment config
└── README.md                # This file
```

### Development Workflow

#### 1. Setup Development Environment
```bash
# Install dependencies
npm install

# Start services
docker-compose up postgres redis -d

# Run in development mode
npm run dev
```

#### 2. Database Development
```bash
# View database in browser
npm run prisma:studio

# Reset database (development only)
npx prisma migrate reset

# Generate Prisma client after schema changes
npm run prisma:generate

# Push schema changes
npm run prisma:push
```

#### 3. Adding New Features

**Create Route Handler:**
```javascript
// routes/newFeature.js
const express = require('express');
const { asyncHandler } = require('../middleware/errorHandler');
const router = express.Router();

router.get('/', asyncHandler(async (req, res) => {
  // Implementation
  res.json({ success: true, data: {} });
}));

module.exports = router;
```

**Register Route:**
```javascript
// server.js
const newFeatureRoutes = require('./routes/newFeature');
app.use(`${API_VERSION}/new-feature`, newFeatureRoutes);
```

**Add Validation:**
```javascript
const { body, validationResult } = require('express-validator');

const validateInput = [
  body('email').isEmail().normalizeEmail(),
  body('name').trim().isLength({ min: 2, max: 50 })
];

router.post('/', validateInput, asyncHandler(async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    throw new ValidationError('Invalid input', errors.array());
  }
  // Process request
}));
```

#### 4. Testing New Features
```bash
# Test specific endpoint
curl -X GET "http://localhost:3000/api/v1/your-endpoint"

# Run comprehensive tests
./scripts/advance_test.sh

# Test with different data
curl -X POST "http://localhost:3000/api/v1/endpoint" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Development Commands

```bash
# Development server with hot reload
npm run dev

# Production server
npm start

# Database operations
npm run prisma:studio          # Database GUI
npm run prisma:generate        # Regenerate client
npm run prisma:push           # Push schema changes

# Code quality
npm run lint                  # Lint code
npm run format               # Format code
npm test                     # Run tests

# Logging and debugging
DEBUG=* npm run dev          # Enable all debug logs
DEBUG_SQL_QUERIES=true npm run dev  # SQL query logging
DEBUG_REDIS_OPERATIONS=true npm run dev # Redis operation logging
```

### Debugging

#### Enable Debug Logging
```bash
# All debug info
DEBUG=* npm run dev

# Specific modules
DEBUG=express:* npm run dev
DEBUG=prisma:* npm run dev
```

#### View Logs
```bash
# Real-time logs
tail -f logs/combined.log

# Error logs only
tail -f logs/error.log

# Filter specific events
grep "API Request" logs/combined.log
grep "ERROR" logs/combined.log
```

#### Performance Profiling
```bash
# Monitor memory usage
node --inspect server.js

# Profile CPU usage
node --prof server.js
```

## 🧪 Testing

### Automated Testing Scripts

The project includes comprehensive testing scripts:

#### Quick Test
```bash
# Test essential endpoints
./scripts/quick_test.sh

# Example output:
# 🚀 Quick BirJob API Tests
# 1. 🏥 Health Check: ✅
# 2. 💼 Jobs API: ✅
# 3. 👤 User Registration: ✅
```

#### Comprehensive Test Suite
```bash
# Test all endpoints and features
./scripts/advance_test.sh

# Test specific deployment
./scripts/test_api.sh https://your-app.onrender.com
```

### Manual Testing Examples

#### Test Health Endpoints
```bash
# Basic health
curl http://localhost:3000/api/health

# Detailed health with system info
curl http://localhost:3000/api/health/detailed

# Test performance
curl "http://localhost:3000/api/health/performance?iterations=50"
```

#### Test Jobs API
```bash
# Get all jobs
curl "http://localhost:3000/api/v1/jobs?limit=5"

# Search with filters
curl "http://localhost:3000/api/v1/jobs?search=engineer&source=LinkedIn&page=1&limit=10"

# Get job metadata
curl http://localhost:3000/api/v1/jobs/meta/sources
curl http://localhost:3000/api/v1/jobs/meta/trends
```

#### Test User Management
```bash
# Register user
curl -X POST http://localhost:3000/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Add keywords
curl -X POST http://localhost:3000/api/v1/users/keywords \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","keyword":"developer"}'

# Get user profile
curl "http://localhost:3000/api/v1/users/profile?email=test@example.com"
```

#### Test Mobile APIs
```bash
# Get iOS config
curl "http://localhost:3000/api/v1/mobile/config?platform=ios"

# Track app launch
curl -X POST http://localhost:3000/api/v1/mobile/app-launch \
  -H "Content-Type: application/json" \
  -d '{
    "platform":"ios",
    "appVersion":"1.0.0",
    "deviceModel":"iPhone 14"
  }'

# Get featured jobs
curl "http://localhost:3000/api/v1/mobile/jobs/featured?limit=5"
```

#### Test Analytics
```bash
# Log search
curl -X POST http://localhost:3000/api/v1/analytics/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"software engineer",
    "resultCount":25,
    "deviceType":"mobile"
  }'

# Get search stats
curl "http://localhost:3000/api/v1/analytics/search-stats?period=week"
```

### Load Testing

#### Basic Load Test
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with 100 concurrent requests
ab -n 1000 -c 100 http://localhost:3000/api/health

# Test specific endpoint
ab -n 500 -c 50 http://localhost:3000/api/v1/jobs
```

#### Advanced Load Testing with Artillery
```bash
# Install Artillery
npm install -g artillery

# Create test config (artillery.yml)
# Run load test
artillery run artillery.yml
```

### Performance Benchmarks

Expected performance metrics:
- **Health Check**: < 50ms response time
- **Jobs Listing**: < 200ms (with cache), < 1s (without cache)
- **Search Queries**: < 300ms
- **User Operations**: < 100ms

## 📊 Monitoring

### Health Check Endpoints

#### Basic Health Check
```http
GET /api/health
Response: {
  "status": "healthy",
  "timestamp": "2025-05-28T10:30:00Z",
  "uptime": 1234
}
```

#### Comprehensive Health Check
```http
GET /api/health/detailed
Response: {
  "status": "healthy",
  "responseTime": "45ms",
  "services": {
    "database": { "status": "healthy", "responseTime": "12ms" },
    "redis": { "status": "healthy", "responseTime": "3ms" },
    "api": { "status": "healthy", "port": 3000 }
  },
  "system": {
    "nodejs": "v18.17.0",
    "memory": { "used": "256 MB", "total": "512 MB" },
    "cpu": { "loadAverage": [1.2, 1.5, 1.8] }
  }
}
```

#### Service-Specific Health Checks
```http
GET /api/health/database    # Database connectivity and stats
GET /api/health/redis      # Redis connectivity and stats
GET /api/health/ready      # Kubernetes readiness probe
GET /api/health/live       # Kubernetes liveness probe
```

#### Performance Monitoring
```http
GET /api/health/performance?iterations=100
Response: {
  "totalTime": "1500ms",
  "averageTime": "15ms",
  "throughput": "66.67 ops/sec"
}
```

#### System Metrics
```http
GET /api/health/metrics
Response: {
  "uptime": { "seconds": 86400, "formatted": "1d 0h 0m 0s" },
  "system": {
    "memory": { "heapUsed": 128, "heapTotal": 256, "rss": 180 },
    "cpu": { "user": 12345, "system": 6789 }
  },
  "database": {
    "totalRecords": { "jobs": 12500, "users": 850, "notifications": 5200 },
    "latestJob": { "createdAt": "2025-05-28T09:15:00Z" }
  },
  "cache": { "status": "active", "dbSize": 1250 }
}
```

### Logging System

The application uses Winston for structured logging with multiple levels:

#### Log Levels
- **error**: System errors, exceptions, critical issues
- **warn**: Warning conditions, degraded performance
- **info**: General operational messages
- **http**: HTTP request/response logging
- **debug**: Detailed debugging information

#### Log Files
```
logs/
├── error.log        # Error-level logs only
├── combined.log     # All log levels
└── access.log       # HTTP access logs
```

#### Structured Logging Examples
```javascript
// API request logging
logger.context.api('GET', '/api/v1/jobs', 200, 150, userId);

// Database operation logging  
logger.context.db('SELECT', 'jobs_jobpost', 25, 50);

// Cache operation logging
logger.context.cache('GET', 'jobs:all:1:20', true, 300);

// Security event logging
logger.context.security('rate_limit_exceeded', 'medium', '192.168.1.1', {
  path: '/api/v1/jobs',
  attempts: 100
});

// Analytics event logging
logger.context.analytics('search_performed', {
  query: 'developer',
  results: 25,
  duration: 150
});
```

#### Log Analysis
```bash
# View recent errors
tail -n 100 logs/error.log

# Monitor real-time logs
tail -f logs/combined.log

# Search for specific patterns
grep "ERROR\|WARN" logs/combined.log
grep "Database" logs/combined.log | tail -20

# Analyze API performance
grep "API Request" logs/combined.log | grep "responseTime" | tail -50
```

### Performance Monitoring

#### Memory Usage Tracking
```javascript
// Automatic memory logging every 5 minutes
logger.performance.logMemoryUsage();

// Manual performance timing
const timer = logger.performance.startTimer('database_query');
// ... operation
timer.end(); // Logs duration automatically
```

#### Database Performance Monitoring
The application tracks:
- Query execution time
- Connection pool status
- Record counts per table
- Slow query identification

#### Cache Performance Monitoring
Redis operations are monitored for:
- Hit/miss ratios
- Response times
- Memory usage
- Key expiration rates

### Error Tracking

#### Error Classification
- **Operational Errors**: Expected errors (validation, not found, etc.)
- **Programming Errors**: Unexpected errors (bugs, system failures)
- **External Errors**: Third-party service failures

#### Error Response Strategy
```javascript
// User-friendly error responses
{
  "success": false,
  "error": {
    "name": "ValidationError",
    "message": "Invalid email format",
    "statusCode": 400,
    "timestamp": "2025-05-28T10:30:00Z"
  }
}

// Development includes additional details
{
  "error": {
    // ... above fields
    "stack": "Error: ...\n    at ...",
    "path": "/api/v1/users/register",
    "method": "POST"
  }
}
```

### Alerting & Notifications

The application can be configured to send alerts for:
- High error rates
- Database connectivity issues
- Memory usage spikes
- Unusual traffic patterns
- Service downtime

#### Integration with Monitoring Services
- **Uptime Monitoring**: UptimeRobot, Pingdom
- **APM**: New Relic, Datadog
- **Log Analysis**: LogRocket, Loggly
- **Error Tracking**: Sentry, Rollbar

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues

**Issue**: `@prisma/client did not initialize yet`
```bash
# Solution: Generate Prisma client
npx prisma generate

# If still failing, check DATABASE_URL
echo $DATABASE_URL

# Test connection
npx prisma db pull
```

**Issue**: Database connection timeout
```bash
# Check PostgreSQL status
pg_isready -h localhost -p 5432

# Test connection with psql
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool
grep "connection" logs/combined.log
```

#### Redis Connection Problems

**Issue**: `Invalid protocol` error
```env
# Ensure Redis URL format is correct
REDIS_URL=redis://localhost:6379
# NOT: localhost:6379

# For Upstash, use REST URL
UPSTASH_REDIS_REST_URL=https://your-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token
```

**Issue**: Redis connection refused
```bash
# Check if Redis is running
redis-cli ping

# Start Redis server
redis-server

# Check configuration
redis-cli INFO server
```

#### Push Notification Issues

**Issue**: Firebase notifications not sending
```bash
# Verify Firebase configuration
echo $FIREBASE_PROJECT_ID
echo $FIREBASE_PRIVATE_KEY | head -c 50

# Check service account permissions
# Ensure Firebase Cloud Messaging API is enabled
```

**Issue**: Apple Push notifications failing
```bash
# Verify Apple certificates
echo $APPLE_TEAM_ID
echo $APPLE_KEY_ID

# Check if certificates are expired
# Verify bundle ID matches app
```

#### Email Delivery Problems

**Issue**: Gmail SMTP authentication failed
```env
# Use App Password, not regular password
EMAIL_PASSWORD=your-16-character-app-password

# Enable 2FA and generate App Password in Google Account settings
```

**Issue**: Emails not sending
```bash
# Test SMTP connection
telnet smtp.gmail.com 587

# Check email service health
curl http://localhost:3000/api/health/detailed | jq '.services.email'
```

#### Performance Issues

**Issue**: Slow API responses
```bash
# Check database performance
grep "Database Operation" logs/combined.log | tail -20

# Monitor memory usage
grep "Memory Usage" logs/combined.log | tail -10

# Check cache hit rates
grep "Cache" logs/combined.log | grep "HIT\|MISS" | tail -20
```

**Issue**: High memory usage
```bash
# Monitor Node.js memory usage
curl http://localhost:3000/api/health/metrics | jq '.system.memory'

# Restart application if needed
pm2 restart birjob-backend

# Check for memory leaks
node --inspect server.js
```

#### API Errors

**Issue**: 404 errors for valid endpoints
```bash
# Check route registration
grep "app.use" server.js

# Verify API versioning
curl http://localhost:3000/api/v1/jobs
# NOT: http://localhost:3000/jobs
```

**Issue**: CORS errors
```javascript
// Check CORS configuration in server.js
app.use(cors({
  origin: ['http://localhost:3000', 'https://yourdomain.com'],
  credentials: true
}));
```

### Debug Mode

#### Enable Comprehensive Debugging
```bash
# Enable all debug information
DEBUG=* npm run dev

# Enable SQL query logging
DEBUG_SQL_QUERIES=true npm run dev

# Enable Redis operation debugging
DEBUG_REDIS_OPERATIONS=true npm run dev

# Combine multiple debug modes
DEBUG=* DEBUG_SQL_QUERIES=true npm run dev
```

#### Production Debugging

**Safe production debugging:**
```env
# Increase log level temporarily
LOG_LEVEL=debug

# Enable performance monitoring
ENABLE_PERFORMANCE_MONITORING=true

# Monitor specific operations
DEBUG_API_PERFORMANCE=true
```

### Log Analysis Commands

```bash
# Find specific errors
grep -i "error" logs/combined.log | tail -20

# Monitor API performance
grep "API Request" logs/combined.log | grep -E "responseTime.*[5-9][0-9][0-9]ms"

# Check database operations
grep "Database Operation" logs/combined.log | grep -E "duration.*[1-9][0-9][0-9]ms"

# Monitor memory usage
grep "Memory Usage" logs/combined.log | tail -10

# Find slow queries
grep "duration" logs/combined.log | sort -k6 -nr | head -20
```

### Health Check Troubleshooting

```bash
# Basic connectivity test
curl -f http://localhost:3000/api/health || echo "Health check failed"

# Detailed health analysis
curl http://localhost:3000/api/health/detailed | jq '.services'

# Test database connectivity
curl http://localhost:3000/api/health/database | jq '.connection.status'

# Test Redis connectivity
curl http://localhost:3000/api/health/redis | jq '.connection.status'
```

### Recovery Procedures

#### Database Recovery
```bash
# Backup current database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Reset database (development only)
npx prisma migrate reset

# Restore from backup
psql $DATABASE_URL < backup_20250528.sql
```

#### Cache Recovery
```bash
# Clear Redis cache
redis-cli FLUSHALL

# Restart with cache disabled
REDIS_URL="" npm start

# Rebuild cache by making API calls
curl http://localhost:3000/api/v1/jobs?limit=100
```

#### Application Recovery
```bash
# Graceful restart
pm2 restart birjob-backend

# Force restart if needed
pm2 kill
npm start

# Check application health
curl http://localhost:3000/api/health/detailed
```

### Getting Help

If you encounter issues not covered here:

1. **Check Application Logs**: `tail -f logs/combined.log`
2. **Verify Configuration**: Ensure all environment variables are set correctly
3. **Test Components**: Use health check endpoints to identify failing services
4. **Enable Debug Mode**: Run with `DEBUG=* npm run dev` for detailed information
5. **Create Issue**: Submit a GitHub issue with logs and configuration details

## 🤝 Contributing

We welcome contributions to the BirJob Backend API! Here's how to get started:

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/birJobBackend.git
   cd birJobBackend
   ```

2. **Setup Development Environment**
   ```bash
   # Install dependencies
   npm install
   
   # Setup development database
   cp .env.example .env
   # Edit .env with your development settings
   
   # Generate Prisma client
   npx prisma generate
   
   # Start development server
   npm run dev
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-new-feature
   ```

### Development Guidelines

#### Code Style
- Use **ESLint** configuration provided
- Follow existing patterns and conventions
- Add JSDoc comments for all functions
- Use meaningful variable and function names
- Keep functions small and focused

#### API Design Principles
- **RESTful**: Follow REST conventions
- **Consistent**: Use consistent response formats
- **Documented**: Add comprehensive documentation
- **Validated**: Validate all inputs
- **Secure**: Implement proper error handling
- **Cached**: Consider caching implications

#### Example Code Contribution
```javascript
/**
 * Get job recommendations for a user
 * @param {string} email - User email
 * @param {number} limit - Maximum recommendations
 * @returns {Promise<Object>} Recommended jobs
 */
const getJobRecommendations = async (email, limit = 10) => {
  const cacheKey = `recommendations:${email}:${limit}`;
  
  // Try cache first
  let cached = await cache.get(cacheKey);
  if (cached) return cached;
  
  // Get user preferences
  const user = await prisma.users.findUnique({
    where: { email },
    include: { keywords: true }
  });
  
  // Build recommendations logic
  const recommendations = await buildRecommendations(user, limit);
  
  // Cache results
  await cache.set(cacheKey, recommendations, CACHE_DURATIONS.USER_DATA);
  
  return recommendations;
};
```

### Testing Requirements

All contributions must include:

1. **Unit Tests** (when applicable)
   ```javascript
   describe('Job Recommendations', () => {
     test('should return recommendations for valid user', async () => {
       const recommendations = await getJobRecommendations('test@example.com', 5);
       expect(recommendations).toBeDefined();
       expect(recommendations.jobs.length).toBeLessThanOrEqual(5);
     });
   });
   ```

2. **API Testing**
   ```bash
   # Test your endpoints
   curl -X GET "http://localhost:3000/api/v1/your-endpoint"
   
   # Use provided test scripts
   ./scripts/test_api.sh http://localhost:3000
   ```

3. **Integration Testing**
   - Ensure new features work with existing functionality
   - Test error scenarios
   - Verify caching behavior
   - Check performance impact

### Documentation Requirements

#### API Documentation
For new endpoints, add comprehensive documentation:

```javascript
/**
 * @route POST /api/v1/recommendations
 * @description Get personalized job recommendations
 * @access Public
 * @param {string} email - User email address
 * @param {number} [limit=10] - Maximum recommendations (1-50)
 * @returns {Object} Success response with recommendations
 * @example
 * // Request
 * POST /api/v1/recommendations
 * {
 *   "email": "user@example.com",
 *   "limit": 5
 * }
 * 
 * // Response
 * {
 *   "success": true,
 *   "data": {
 *     "jobs": [...],
 *     "metadata": {
 *       "totalRecommendations": 5,
 *       "algorithm": "keyword_match",
 *       "generatedAt": "2025-05-28T10:30:00Z"
 *     }
 *   }
 * }
 */
```

#### README Updates
Update relevant sections:
- Add new endpoints to API documentation
- Update configuration if new environment variables
- Add troubleshooting for new features
- Update feature list

### Pull Request Process

1. **Pre-submission Checklist**
   - [ ] Code follows project style guidelines
   - [ ] All tests pass: `npm test`
   - [ ] Linting passes: `npm run lint`
   - [ ] API tests work: `./scripts/test_api.sh`
   - [ ] Documentation is updated
   - [ ] No sensitive data in code

2. **Create Pull Request**
   ```bash
   git add .
   git commit -m 'feat: add job recommendations endpoint'
   git push origin feature/amazing-new-feature
   ```

3. **PR Description Template**
   ```markdown
   ## Description
   Brief description of changes and motivation.
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests added/updated
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## API Changes
   - [ ] New endpoints documented
   - [ ] Response format unchanged
   - [ ] Backward compatible
   
   ## Screenshots (if applicable)
   Add screenshots for UI changes.
   ```

4. **Review Process**
   - Maintainers will review within 48 hours
   - Address feedback promptly
   - Keep PR scope focused
   - Rebase if requested

### Issue Reporting

#### Bug Reports
Use the bug report template:
```markdown
**Bug Description**
Clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Environment**
- OS: [e.g. macOS, Ubuntu]
- Node.js: [e.g. 18.17.0]
- npm: [e.g. 9.6.7]

**Logs**
```
paste relevant logs here
```
```

#### Feature Requests
```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why is this feature needed?

**Proposed Implementation**
How should this be implemented?

**Additional Context**
Any other context or screenshots.
```

### Recognition

Contributors will be:
- Listed in the contributors section
- Mentioned in release notes
- Given credit in commit messages

### Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 BirJob Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## 🙏 Acknowledgments

### Core Technologies
- **[Express.js](https://expressjs.com/)** - Fast, unopinionated web framework
- **[Prisma](https://www.prisma.io/)** - Next-generation ORM for Node.js and TypeScript
- **[Redis](https://redis.io/)** - In-memory data structure store for caching
- **[Winston](https://github.com/winstonjs/winston)** - Versatile logging library
- **[Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)** - Push notifications for Android
- **[node-apn](https://github.com/node-apn/node-apn)** - Apple Push Notification service

### Infrastructure & Deployment
- **[Docker](https://www.docker.com/)** - Containerization platform
- **[Render](https://render.com/)** - Cloud application hosting
- **[Upstash](https://upstash.com/)** - Serverless Redis provider
- **[PostgreSQL](https://www.postgresql.org/)** - Advanced open source database

### Development Tools
- **[Nodemon](https://nodemon.io/)** - Development server with auto-restart
- **[ESLint](https://eslint.org/)** - Code linting and formatting
- **[Jest](https://jestjs.io/)** - Testing framework
- **[Supertest](https://github.com/visionmedia/supertest)** - HTTP assertions

### Special Thanks
- **Azerbaijan Job Market** - For providing the data foundation
- **Open Source Community** - For the incredible tools and libraries
- **Contributors** - Everyone who has contributed to this project
- **Beta Testers** - Mobile app users who provided valuable feedback

## 📞 Support & Contact

### Documentation & Resources
- **API Documentation**: Available at `/api/health` endpoint
- **GitHub Repository**: [https://github.com/Ismat-Samadov/birjobBackend](https://github.com/Ismat-Samadov/birjobBackend)
- **Wiki**: [Project Wiki](https://github.com/Ismat-Samadov/birjobBackend/wiki)

### Getting Help
- **GitHub Issues**: [Report bugs or request features](https://github.com/Ismat-Samadov/birjobBackend/issues)
- **Email Support**: dev@birjob.az
- **Technical Support**: Create an issue with detailed information

### Community
- **Website**: [https://birjob.az](https://birjob.az)
- **LinkedIn**: [BirJob Official](https://linkedin.com/company/birjob)
- **Twitter**: [@birjob_official](https://twitter.com/birjob_official)

### Commercial Support
For enterprise support, custom features, or consulting:
- **Business Email**: business@birjob.az
- **Partnership Inquiries**: partnerships@birjob.az

---

**Built with ❤️ in Azerbaijan for job seekers everywhere**

🌟 **Star this repository** if you find it useful!
🔄 **Fork and contribute** to make it even better!
📱 **Download BirJob** mobile app for the complete experience!

---

*Last updated: May 28, 2025*
*Version: 1.0.0*
