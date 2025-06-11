# 🚀 Deployment Guide - iOS Backend to Render.com

## Prerequisites

1. **Git Repository**: Your code must be in a Git repository (GitHub, GitLab, etc.)
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **APNs Credentials**: Apple Push Notification service .p8 key file

## 📦 Pre-Deployment Setup

### 1. Database Migrations

First, set up your database schema using Alembic:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the migration helper
python migrate.py

# Choose option 1 to run migrations
```

### 2. Environment Configuration

Copy the production environment template:

```bash
cp .env.render .env.production
# Edit .env.production with your specific values
```

### 3. Git Setup

Ensure your code is committed and pushed:

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

## 🚀 Render.com Deployment

### Method 1: Using render.yaml (Recommended)

1. **Connect Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub/GitLab repository
   - Render will detect `render.yaml` automatically

2. **Configure Services**
   The `render.yaml` will create:
   - `birjob-ios-api` - Main API service
   - `birjob-match-engine` - Background job processor
   - `birjob-redis` - Redis cache
   - `birjob-postgres` - PostgreSQL database

### Method 2: Manual Deployment Helper

```bash
python deploy.py
```

This script will guide you through the deployment process.

## ⚙️ Environment Variables Setup

### Auto-Configured Variables
These are set automatically by Render:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Auto-generated JWT secret
- `API_KEY` - Auto-generated API key

### Required Manual Configuration

#### Apple Push Notifications
```bash
APNS_KEY_PATH=/opt/render/project/src/secrets/apns.p8
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apple-team-id  
APNS_BUNDLE_ID=com.yourcompany.birjob
APNS_SANDBOX=false
```

#### CORS Origins
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 📁 APNs Key File Setup

1. **Upload .p8 file**:
   - In Render dashboard, go to your service
   - Environment → Files
   - Upload your APNs .p8 key file
   - Note the file path (usually `/opt/render/project/src/secrets/apns.p8`)

2. **Set APNS_KEY_PATH**:
   - Update environment variable with the uploaded file path

## 🔄 Database Migration on Render

Migrations run automatically on deployment via the start command:

```bash
alembic upgrade head && uvicorn app:app --host 0.0.0.0 --port $PORT
```

To run migrations manually:
1. Open Render service shell
2. Run: `alembic upgrade head`

## 🏗️ Service Architecture on Render

```
┌─────────────────────────────────────────────────────────┐
│                    Render.com                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  Web Service    │    │  Worker Service │            │
│  │  (API Server)   │    │ (Match Engine)  │            │
│  │                 │    │                 │            │
│  │ Port: $PORT     │    │ Background Jobs │            │
│  │ Health: /health │    │ Every 5min      │            │
│  └─────────────────┘    └─────────────────┘            │
│           │                       │                    │
│           └───────────┬───────────┘                    │
│                       │                                │
│  ┌─────────────────┐  │  ┌─────────────────┐          │
│  │ PostgreSQL      │  │  │     Redis       │          │
│  │ (Database)      │  │  │    (Cache)      │          │
│  │                 │  │  │                 │          │
│  │ iosapp schema   │  │  │ Device tokens   │          │
│  │ Auto backups    │  │  │ Job processing  │          │
│  └─────────────────┘  │  └─────────────────┘          │
│                       │                                │
└───────────────────────┼────────────────────────────────┘
                        │
                ┌───────▼────────┐
                │  External APNs │
                │  (Push Notifs) │
                └────────────────┘
```

## 🔍 Health Checks & Monitoring

### Health Check Endpoints
- Primary: `https://your-app.onrender.com/api/v1/health`
- Scraper Status: `https://your-app.onrender.com/api/v1/health/status/scraper`

### Monitoring URLs
- **API Documentation**: `https://your-app.onrender.com/docs`
- **Metrics**: `https://your-app.onrender.com/metrics`
- **Logs**: Available in Render dashboard

### Key Metrics to Monitor
- Active devices count
- Job matches per hour
- Push notification delivery rate
- API response times
- Background job processing

## 🐛 Troubleshooting

### Common Deployment Issues

#### 1. Service Won't Start
**Check logs for:**
- Missing environment variables
- Database connection errors
- Python dependency issues

**Solutions:**
```bash
# Verify environment variables are set
# Check DATABASE_URL format
# Ensure requirements.txt includes all dependencies
```

#### 2. Database Connection Failed
**Check:**
- DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`
- PostgreSQL service is running
- Network connectivity

#### 3. Push Notifications Not Working
**Check:**
- APNS .p8 file uploaded correctly
- APNS_KEY_PATH points to uploaded file
- APNS_KEY_ID and APNS_TEAM_ID are correct
- APNS_SANDBOX setting (false for production)

#### 4. Background Jobs Not Processing
**Check:**
- Worker service is running
- Redis connection is working
- Match engine logs for errors

### Useful Commands

```bash
# Check service status
curl https://your-app.onrender.com/api/v1/health

# View recent logs
# (Available in Render dashboard)

# Run migration manually
# (Use Render shell access)
alembic upgrade head

# Test API endpoints
curl -X POST https://your-app.onrender.com/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_token":"test","device_info":{"os_version":"17.0"}}'
```

## 📊 Performance Optimization

### Render Plan Recommendations

#### Starter Plan (Development)
- Web Service: Starter ($7/month)
- PostgreSQL: Starter ($7/month)  
- Redis: Starter ($7/month)
- **Total: ~$21/month**

#### Production Plan
- Web Service: Standard ($25/month)
- Worker Service: Standard ($25/month)
- PostgreSQL: Standard ($20/month)
- Redis: Standard ($20/month)
- **Total: ~$90/month**

### Scaling Configuration

```yaml
# In render.yaml
services:
  - type: web
    name: birjob-ios-api
    plan: standard  # or starter
    autoDeploy: true
    envVars:
      - key: INSTANCE_COUNT
        value: "2"  # Scale horizontally
```

## 🔒 Security Best Practices

### Environment Variables
- Never commit secrets to Git
- Use Render's secret management
- Rotate API keys regularly

### Database Security
- Enable SSL (automatic on Render)
- Regular backups (automatic on Render)
- Monitor access logs

### API Security
- Rate limiting enabled
- HTTPS only (automatic on Render)
- Input validation active
- CORS properly configured

## 📈 Post-Deployment Checklist

- [ ] All services are healthy
- [ ] Database schema is up to date
- [ ] Health check endpoints respond
- [ ] Push notifications working
- [ ] Background jobs processing
- [ ] Monitoring alerts configured
- [ ] Domain name configured (optional)
- [ ] SSL certificate active
- [ ] API documentation accessible

## 🔄 Continuous Deployment

Enable auto-deployment in render.yaml:

```yaml
services:
  - type: web
    autoDeploy: true  # Deploy on git push
```

## 📞 Support

### Render Support
- Documentation: [render.com/docs](https://render.com/docs)
- Community: [community.render.com](https://community.render.com)
- Support: Available in dashboard

### Application Support
- Check application logs in Render dashboard
- Monitor health check endpoints
- Review API documentation at `/docs`

---

🎉 **Your iOS Backend is now deployed and ready for production!**