# **BirJob Backend API**

A comprehensive Node.js backend service for the BirJob mobile and web applications, featuring automated job scraping, real-time notifications, and advanced analytics.

## **🚀 Overview**

BirJob Backend is a scalable REST API that powers both web and mobile job search applications. It provides automated job scraping from multiple sources, intelligent job matching, push notifications, and comprehensive analytics.

### **Key Features**
- 🤖 **Automated Job Scraping** - Multi-source job aggregation
- 🔍 **Advanced Search & Filtering** - Intelligent job discovery
- 🔔 **Smart Notifications** - Keyword-based job alerts
- 📱 **Mobile-First API** - Optimized for iOS/Android apps
- 📊 **Advanced Analytics** - Comprehensive user behavior tracking
- 🎯 **Personalization** - User preferences and recommendations
- 📈 **Real-time Insights** - Job market trends and statistics

## **🏗️ Architecture Overview**

```mermaid
graph TB
    subgraph "Client Applications"
        A[iOS App] 
        B[Web App]
        C[Admin Dashboard]
    end
    
    subgraph "API Layer"
        D[Load Balancer]
        E[Express.js API Server]
        F[Authentication Middleware]
        G[Rate Limiting]
    end
    
    subgraph "Core Services"
        H[Job Scraping Service]
        I[Notification Service]
        J[Analytics Service]
        K[Search Service]
    end
    
    subgraph "Data Layer"
        L[(PostgreSQL)]
        M[(Redis Cache)]
        N[File Storage]
    end
    
    subgraph "External Services"
        O[Push Notification Services]
        P[Email Service]
        Q[Job Sources]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    E --> G
    E --> H
    E --> I
    E --> J
    E --> K
    H --> L
    I --> L
    J --> L
    K --> L
    E --> M
    I --> O
    I --> P
    H --> Q
```

## **📊 Database Schema**

```mermaid
erDiagram
    users ||--o{ keywords : has
    users ||--o{ notifications : receives
    users ||--o{ sourcePreferences : configures
    users ||--o{ search_logs : generates
    
    jobs_jobpost ||--o{ notifications : triggers
    
    users {
        int id PK
        string email UK
        datetime createdAt
        datetime updatedAt
        datetime lastNotifiedAt
    }
    
    jobs_jobpost {
        int id PK
        string title
        string company
        string apply_link
        string source
        datetime created_at
    }
    
    keywords {
        int id PK
        string keyword
        int userId FK
        datetime createdAt
    }
    
    notifications {
        int id PK
        int userId FK
        int jobId FK
        datetime sentAt
        string matchedKeyword
        boolean isRead
    }
    
    search_logs {
        int id PK
        string query
        string searchType
        int resultCount
        string ip
        string deviceType
        string country
        datetime timestamp
    }
    
    visitor_logs {
        int id PK
        string ip
        string visitorId
        string deviceType
        string country
        string referrerSource
        datetime timestamp
    }
```

## **⚙️ Setup & Installation**

### **Prerequisites**
- Node.js 18+ 
- PostgreSQL 14+
- Redis 6+
- npm or yarn

### **Environment Variables**
Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL="postgresql://user:password@localhost:5432/birjob"
REDIS_URL="redis://localhost:6379"

# Authentication
JWT_SECRET="your-super-secret-jwt-key"
JWT_EXPIRES_IN="24h"

# Push Notifications
FIREBASE_PROJECT_ID="your-firebase-project"
FIREBASE_PRIVATE_KEY="your-firebase-key"
APPLE_TEAM_ID="your-apple-team-id"

# External APIs
EMAIL_API_KEY="your-email-service-key"

# App Configuration
NODE_ENV="development"
PORT=3000
API_VERSION="v1"
```

### **Installation Steps**

```bash
# Clone the repository
git clone https://github.com/Ismat-Samadov/birJobBackend.git
cd birJobBackend

# Install dependencies
npm install

# Generate Prisma Client
npx prisma generate

# Run database migrations (if needed)
npx prisma db push

# Seed the database (optional)
npm run seed

# Start development server
npm run dev
```

## **🔌 API Endpoints**

### **Core Job APIs**

#### **Job Listings**
```http
GET /api/v1/jobs
```
**Query Parameters:**
- `search` - Search term for job title/company
- `source` - Filter by job source
- `company` - Filter by specific company
- `page` - Page number (default: 1)
- `limit` - Results per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [...],
    "metadata": {
      "totalJobs": 1250,
      "currentPage": 1,
      "totalPages": 63,
      "sources": ["LinkedIn", "Indeed", "Glassdoor"],
      "companies": ["Google", "Microsoft", "Apple"],
      "latestScrapeDate": "2025-05-26T05:30:00Z"
    }
  }
}
```

#### **Job Trends**
```http
GET /api/v1/trends
```
**Response:**
```json
{
  "success": true,
  "data": {
    "sourceData": [...],
    "companyData": [...],
    "totalJobs": 1250,
    "totalSources": 15,
    "totalCompanies": 245,
    "lastUpdated": "2025-05-26T05:30:00Z"
  }
}
```

### **User Management APIs**

#### **User Keywords**
```http
GET    /api/v1/users/keywords?email={email}
POST   /api/v1/users/keywords
DELETE /api/v1/users/keywords
```

#### **Source Preferences**
```http
GET  /api/v1/users/sources?email={email}
POST /api/v1/users/sources
```

### **Mobile-Specific APIs**

#### **Device Registration**
```http
POST /api/v1/mobile/register-device
```
**Body:**
```json
{
  "email": "user@example.com",
  "deviceToken": "device-push-token",
  "platform": "ios",
  "appVersion": "1.0.0",
  "deviceModel": "iPhone 14 Pro"
}
```

#### **Push Notifications**
```http
GET /api/v1/mobile/notifications?email={email}
PUT /api/v1/mobile/notifications/{id}/read
```

### **Analytics APIs**

#### **Search Analytics**
```http
POST /api/v1/analytics/search
```
**Body:**
```json
{
  "query": "software engineer",
  "resultCount": 25,
  "deviceType": "mobile",
  "sessionId": "session-123",
  "searchDuration": 250
}
```

#### **Visitor Tracking**
```http
POST /api/v1/analytics/visitor
```

## **🔄 Core Services**

### **Job Scraping Service**

```mermaid
graph LR
    A[Scheduler] --> B[Job Sources]
    B --> C[Scraper Service]
    C --> D[Data Validation]
    D --> E[Database Storage]
    E --> F[Notification Trigger]
    F --> G[Push Notifications]
    
    subgraph "Job Sources"
        B1[LinkedIn API]
        B2[Indeed RSS]
        B3[Company Sites]
        B4[Job Boards]
    end
```

**Features:**
- Multi-source job aggregation
- Duplicate detection and removal
- Data validation and sanitization
- Automatic scheduling with cron jobs
- Error handling and retry logic

### **Notification Service**

```mermaid
sequenceDiagram
    participant Scraper as Job Scraper
    participant NS as Notification Service
    participant DB as Database
    participant FCM as Push Service
    participant User as Mobile App
    
    Scraper->>NS: New jobs found
    NS->>DB: Query user keywords
    DB->>NS: Matching users
    NS->>DB: Create notifications
    NS->>FCM: Send push notifications
    FCM->>User: Job alert received
    User->>NS: Mark as read
    NS->>DB: Update notification status
```

**Features:**
- Keyword-based job matching
- Real-time push notifications
- Email notifications
- Notification preferences
- Read/unread status tracking

### **Analytics Service**

**Tracked Metrics:**
- Search queries and patterns
- User engagement metrics
- Device and browser analytics
- Geographic distribution
- Traffic sources and campaigns
- Job application funnel

## **📱 Mobile Integration**

### **Push Notification Setup**

#### **iOS (Apple Push Notification)**
```javascript
const apn = require('apn');

const options = {
  token: {
    key: process.env.APPLE_PRIVATE_KEY,
    keyId: process.env.APPLE_KEY_ID,
    teamId: process.env.APPLE_TEAM_ID
  },
  production: process.env.NODE_ENV === 'production'
};

const apnProvider = new apn.Provider(options);
```

#### **Android (Firebase Cloud Messaging)**
```javascript
const admin = require('firebase-admin');

const serviceAccount = {
  projectId: process.env.FIREBASE_PROJECT_ID,
  privateKey: process.env.FIREBASE_PRIVATE_KEY,
  clientEmail: process.env.FIREBASE_CLIENT_EMAIL
};

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});
```

### **Mobile API Response Format**
```json
{
  "success": true,
  "data": { ... },
  "message": "Request successful",
  "timestamp": "2025-05-26T05:42:32Z",
  "version": "1.0.0",
  "meta": {
    "pagination": { ... },
    "filters": { ... }
  }
}
```

## **🔧 Configuration**

### **Scraping Configuration**
```javascript
const SCRAPING_CONFIG = {
  sources: [
    {
      name: 'LinkedIn',
      url: 'https://linkedin.com/jobs',
      interval: '*/15 * * * *', // Every 15 minutes
      enabled: true
    },
    {
      name: 'Indeed',
      url: 'https://indeed.com/rss',
      interval: '*/10 * * * *', // Every 10 minutes
      enabled: true
    }
  ],
  rateLimiting: {
    requestsPerMinute: 30,
    concurrentRequests: 5
  }
};
```

### **Notification Configuration**
```javascript
const NOTIFICATION_CONFIG = {
  pushNotifications: {
    batchSize: 1000,
    retryAttempts: 3,
    timeToLive: 86400 // 24 hours
  },
  emailNotifications: {
    dailyDigestTime: '09:00',
    weeklyDigestDay: 'monday'
  }
};
```

## **🚀 Deployment**

### **Docker Setup**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY prisma ./prisma/
RUN npx prisma generate

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### **Docker Compose**
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: birjob
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### **Production Deployment**
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:3000/api/v1/health
```

## **📊 Monitoring & Analytics**

### **Health Check Endpoint**
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-05-26T05:42:32Z",
  "uptime": 86400,
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### **Performance Metrics**
- API response times
- Database query performance
- Scraping success rates
- Notification delivery rates
- Error rates and exceptions

## **🔒 Security**

### **Authentication & Authorization**
- JWT-based authentication
- API key validation
- Rate limiting per endpoint
- Request validation and sanitization

### **Data Protection**
- Input validation with Joi
- SQL injection prevention
- XSS protection
- CORS configuration
- Environment variable security

## **🧪 Testing**

```bash
# Run all tests
npm test

# Run unit tests
npm run test:unit

# Run integration tests
npm run test:integration

# Run with coverage
npm run test:coverage
```

## **📚 API Documentation**

Interactive API documentation is available at:
- **Development:** http://localhost:3000/api-docs
- **Production:** https://api.birjob.com/api-docs

## **🤝 Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## **📄 License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## **📞 Support**

For support and questions:
- **Email:** support@birjob.com
- **GitHub Issues:** [Create an issue](https://github.com/Ismat-Samadov/birJobBackend/issues)
- **Documentation:** [Wiki](https://github.com/Ismat-Samadov/birJobBackend/wiki)

---

**Built with ❤️ by the BirJob Team**
