# 🚀 BirJob Mobile Backend API

A comprehensive Node.js backend service for the BirJob iOS and Android mobile applications, featuring automated job notifications, real-time analytics, and advanced caching.

![Node.js](https://img.shields.io/badge/Node.js-18.x-green.svg)
![Express](https://img.shields.io/badge/Express-4.x-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.x-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7.x-red.svg)
![Prisma](https://img.shields.io/badge/Prisma-5.x-black.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Development](#development)
- [Monitoring](#monitoring)
- [Contributing](#contributing)

## 🌟 Overview

This backend API serves as the central hub for BirJob mobile applications, providing:

- **Job Data Management**: Integration with existing job scraping system
- **Push Notifications**: iOS (APNs) and Android (FCM) support  
- **User Management**: Keywords, preferences, and notification settings
- **Real-time Analytics**: User behavior and search tracking
- **Caching Layer**: Redis-powered performance optimization
- **Automated Tasks**: Daily job alerts and system maintenance

## ✨ Features

### 🔔 Smart Notifications
- **Keyword-based Job Alerts**: Automated notifications for matching jobs
- **Multi-platform Support**: iOS APNs and Android FCM
- **Email Fallback**: Backup email notifications
- **Batch Processing**: Efficient bulk notification handling

### 📊 Advanced Analytics  
- **Search Tracking**: Detailed search behavior analysis
- **User Activity**: Visitor patterns and engagement metrics
- **Device Fingerprinting**: Comprehensive device and location data
- **Performance Monitoring**: API response times and system health

### 🚀 High Performance
- **Redis Caching**: Multi-layer caching strategy
- **Database Optimization**: Indexed queries and connection pooling
- **Rate Limiting**: API protection against abuse
- **Async Processing**: Non-blocking operations

### 📱 Mobile-First Design
- **Optimized Responses**: Minimal data transfer
- **Offline Support**: Cached data for poor connectivity
- **Platform-specific Features**: iOS/Android tailored functionality
- **App Configuration**: Dynamic feature flags and settings

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Mobile Apps"
        A[iOS App] 
        B[Android App]
    end
    
    subgraph "API Layer"
        C[Load Balancer]
        D[Express.js API]
        E[Rate Limiting]
        F[Authentication]
    end
    
    subgraph "Services"
        G[Job Service]
        H[Notification Service]  
        I[Analytics Service]
        J[User Service]
    end
    
    subgraph "Data Layer"
        K[(PostgreSQL)]
        L[(Redis Cache)]
    end
    
    subgraph "External Services"
        M[Push Notifications]
        N[Email Service]
        O[Job Scraper]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    F --> H
    F --> I
    F --> J
    G --> K
    H --> L
    I --> L
    J --> K
    H --> M
    H --> N
    O --> K
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18.x or higher
- **PostgreSQL** 15.x or higher  
- **Redis** 7.x or higher (or Upstash account)
- **npm** or **yarn**

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/Ismat-Samadov/birJobBackend.git
cd birJobBackend

# Install dependencies
npm install

# Generate Prisma client
npx prisma generate
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required Environment Variables:**
```env
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/birjob"

# Redis (Upstash recommended)
UPSTASH_REDIS_REST_URL="https://your-redis-url.upstash.io"
UPSTASH_REDIS_REST_TOKEN="your-token"

# Authentication
JWT_SECRET="your-secret-key"

# Push Notifications
FIREBASE_PROJECT_ID="your-project-id"
FIREBASE_PRIVATE_KEY="your-private-key"
APPLE_TEAM_ID="your-team-id"
APPLE_KEY_ID="your-key-id"
APPLE_PRIVATE_KEY="your-private-key"

# Email Service
EMAIL_USER="your-email@gmail.com"
EMAIL_PASSWORD="your-app-password"
```

### 3. Database Setup

```bash
# Push database schema
npx prisma db push

# (Optional) Seed with sample data
npm run seed
```

### 4. Start Development Server

```bash
# Development mode with hot reload
npm run dev

# Production mode
npm start
```

The API will be available at `http://localhost:3000`

### 5. Verify Installation

```bash
# Health check
curl http://localhost:3000/api/health

# API documentation
curl http://localhost:3000/api/v1/jobs
```

## 📚 API Documentation

### Base URL
```
Production: https://api.birjob.az/api/v1
Development: http://localhost:3000/api/v1
```

### Core Endpoints

#### 🔍 Jobs API
```http
# Get job listings
GET /jobs?search=developer&page=1&limit=20

# Get specific job
GET /jobs/:id

# Get job sources
GET /jobs/meta/sources  

# Get job trends
GET /jobs/meta/trends
```

#### 👤 User Management
```http
# User registration
POST /users/register
{
  "email": "user@example.com"
}

# User profile
GET /users/profile?email=user@example.com

# Manage keywords
GET /users/keywords?email=user@example.com
POST /users/keywords
{
  "email": "user@example.com",
  "keyword": "javascript"
}
DELETE /users/keywords
{
  "email": "user@example.com", 
  "keyword": "javascript"
}
```

#### 🔔 Notifications
```http
# Register device for push notifications
POST /notifications/register-device
{
  "email": "user@example.com",
  "deviceToken": "device-token",
  "platform": "ios"
}

# Get user notifications
GET /notifications?email=user@example.com

# Mark as read
PUT /notifications/:id/read
```

#### 📊 Analytics
```http
# Log search activity
POST /analytics/search
{
  "query": "software engineer",
  "resultCount": 25,
  "deviceType": "mobile"
}

# Get search statistics
GET /analytics/search-stats?period=week
```

#### 📱 Mobile-Specific
```http
# Get app configuration
GET /mobile/config?platform=ios

# Track app launch
POST /mobile/app-launch
{
  "platform": "ios",
  "appVersion": "1.0.0"
}

# Get featured jobs
GET /mobile/jobs/featured?limit=10&userEmail=user@example.com
```

### Response Format
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "cached": false,
  "timestamp": "2025-05-27T10:30:00.000Z"
}
```

### Error Responses
```json
{
  "success": false,
  "error": {
    "name": "ValidationError",
    "message": "Invalid request parameters",
    "statusCode": 400,
    "timestamp": "2025-05-27T10:30:00.000Z"
  }
}
```

## ⚙️ Configuration

### Environment Variables

The application uses environment variables for configuration. See `.env.example` for all available options.

**Key Configuration Categories:**

- **Database**: PostgreSQL connection and pool settings
- **Cache**: Redis/Upstash configuration  
- **Security**: JWT secrets, rate limiting, CORS
- **Notifications**: Firebase, Apple Push, Email settings
- **Features**: Enable/disable functionality
- **Performance**: Cache TTL, query limits, timeouts

### Caching Strategy

```javascript
const CACHE_DURATIONS = {
  JOBS_LIST: 5 * 60,        // 5 minutes
  JOBS_SEARCH: 3 * 60,      // 3 minutes  
  JOBS_METADATA: 15 * 60,   // 15 minutes
  USER_DATA: 30 * 60,       // 30 minutes
  ANALYTICS: 60 * 60,       // 1 hour
  SOURCES: 24 * 60 * 60,    // 24 hours
};
```

### Database Indexes

```sql
-- Essential indexes for performance
CREATE INDEX CONCURRENTLY idx_jobs_created_at ON jobs_jobpost(created_at DESC);
CREATE INDEX CONCURRENTLY idx_jobs_company_lower ON jobs_jobpost(LOWER(company));
CREATE INDEX CONCURRENTLY idx_jobs_title_gin ON jobs_jobpost USING gin(to_tsvector('english', title));
```

## 🐳 Deployment

### Docker Deployment

```bash
# Build production image
docker build -t birjob-backend:latest .

# Run with docker-compose
docker-compose up -d

# Scale services
docker-compose up -d --scale api=3
```

### Manual Deployment

```bash
# Build for production
npm run build

# Start with PM2
pm2 start ecosystem.config.js

# Monitor processes
pm2 monit
```

### Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway link
railway up
```

### Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## 🛠️ Development

### Project Structure

```
├── server.js              # Main application entry
├── routes/                 # API route handlers
│   ├── jobs.js            # Job-related endpoints
│   ├── users.js           # User management
│   ├── notifications.js   # Push notifications
│   ├── analytics.js       # Analytics tracking
│   ├── mobile.js          # Mobile-specific APIs
│   └── health.js          # Health checks
├── services/              # Business logic services
│   ├── pushNotifications.js
│   └── emailService.js
├── middleware/            # Express middleware
│   └── errorHandler.js
├── utils/                 # Utility functions
│   ├── database.js        # Prisma client
│   ├── redis.js           # Redis cache
│   ├── logger.js          # Winston logging
│   └── cronJobs.js        # Scheduled tasks
├── prisma/                # Database schema
│   └── schema.prisma
├── logs/                  # Application logs
├── docker-compose.yml     # Docker orchestration
└── Dockerfile            # Container configuration
```

### Development Commands

```bash
# Development server with hot reload
npm run dev

# Run tests (if configured)
npm test

# Database operations
npx prisma studio          # Database GUI
npx prisma db push         # Push schema changes
npx prisma generate        # Regenerate client

# Lint and format code
npm run lint
npm run prettier

# View logs
tail -f logs/combined.log
```

### Adding New Features

1. **Create Route Handler**
```javascript
// routes/newFeature.js
const express = require('express');
const router = express.Router();

router.get('/', async (req, res) => {
  // Implementation
});

module.exports = router;
```

2. **Register Route**
```javascript
// server.js
const newFeatureRoutes = require('./routes/newFeature');
app.use('/api/v1/new-feature', newFeatureRoutes);
```

3. **Add Tests**
```javascript
// tests/newFeature.test.js
describe('New Feature', () => {
  test('should work correctly', async () => {
    // Test implementation
  });
});
```

## 📊 Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:3000/api/health

# Detailed system status
curl http://localhost:3000/api/health/detailed

# Database health
curl http://localhost:3000/api/health/database

# Cache health  
curl http://localhost:3000/api/health/redis
```

### Logging

The application uses structured logging with Winston:

```javascript
// Log levels: error, warn, info, http, debug
logger.info('User action', { userId, action: 'login' });
logger.error('Database error', { error: error.message });

// Context-specific logging
logger.context.api('GET', '/jobs', 200, 150);
logger.context.notification('push_sent', 'user@example.com', true);
```

### Performance Monitoring

```javascript
// Monitor memory usage
logger.performance.logMemoryUsage();

// Time operations
const timer = logger.performance.startTimer('database_query');
// ... operation
timer.end(); // Logs duration
```

### Metrics Collection

```bash
# Get application metrics
curl http://localhost:3000/api/health/metrics

# Get cron job status
curl http://localhost:3000/api/admin/cron-status
```

## 🔧 Troubleshooting

### Common Issues

**Database Connection Issues**
```bash
# Check database connection
npx prisma db pull

# Reset database (development only)
npx prisma migrate reset
```

**Redis Connection Problems**
```bash
# Test Redis connection
redis-cli ping

# Clear Redis cache
redis-cli FLUSHALL
```

**Push Notification Issues**
- Verify Firebase/Apple credentials in `.env`
- Check device token validity
- Ensure certificates are not expired

**Email Delivery Problems**
- Verify SMTP credentials
- Check DNS records (SPF, DKIM)
- Monitor bounce rates

### Debug Mode

```bash
# Enable debug logging
DEBUG=* npm run dev

# Database query debugging
DEBUG_SQL_QUERIES=true npm run dev

# Redis operation debugging  
DEBUG_REDIS_OPERATIONS=true npm run dev
```

### Log Analysis

```bash
# View recent errors
tail -n 100 logs/error.log

# Search for specific issues
grep -i "notification" logs/combined.log

# Monitor real-time logs
tail -f logs/combined.log | grep ERROR
```

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make changes and test**
   ```bash
   npm test
   npm run lint
   ```
4. **Commit changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push and create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

### Code Style

- Use ESLint configuration
- Follow existing patterns
- Add JSDoc comments for functions
- Write tests for new features
- Update documentation

### Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add changeset entry (if applicable)
4. Request review from maintainers
5. Address feedback and iterate

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Express.js** for the robust web framework
- **Prisma** for excellent database tooling  
- **Redis** for high-performance caching
- **Winston** for comprehensive logging
- **Firebase** and **Apple** for push notification services

## 📞 Support

- **Email**: dev@birjob.az
- **Issues**: [GitHub Issues](https://github.com/Ismat-Samadov/birJobBackend/issues)
- **Documentation**: [Wiki](https://github.com/Ismat-Samadov/birJobBackend/wiki)

---

**Built with ❤️ by the BirJob Team**

🌐 [Website](https://birjob.az) • 📧 [Email](mailto:support@birjob.az) • 🐦 [Twitter](https://twitter.com/birjob_official)