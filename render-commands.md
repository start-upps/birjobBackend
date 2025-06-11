# Render.com Configuration Guide

## 🚀 Service Configuration

### 1. Main API Service (Web Service)

**Service Name:** `birjob-ios-api`

**Runtime:** `Python 3`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
alembic upgrade head && uvicorn app:app --host 0.0.0.0 --port $PORT
```

**Health Check Path:** `/api/v1/health`

**Auto Deploy:** `Yes`

---

### 2. Background Worker (Worker Service)

**Service Name:** `birjob-match-engine`

**Runtime:** `Python 3`

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
python -c "import asyncio; from app.services.match_engine import job_scheduler; asyncio.run(job_scheduler.start())"
```

**Auto Deploy:** `Yes`

---

### 3. PostgreSQL Database

**Service Name:** `birjob-postgres`

**Plan:** `Starter` (for development) or `Standard` (for production)

**Database Name:** `birjob_ios`

---

### 4. Redis Cache

**Service Name:** `birjob-redis`

**Plan:** `Starter`

**Max Memory Policy:** `allkeys-lru`

---

## 🔧 Environment Variables

### API Service Environment Variables

| Variable | Value | Source |
|----------|-------|---------|
| `DATABASE_URL` | Auto-configured | From PostgreSQL service |
| `REDIS_URL` | Auto-configured | From Redis service |
| `SECRET_KEY` | Auto-generated | Generate value |
| `API_KEY` | Auto-generated | Generate value |
| `ALLOWED_ORIGINS` | `*` | Manual |
| `LOG_LEVEL` | `INFO` | Manual |
| `APNS_SANDBOX` | `false` | Manual (true for dev) |
| `APNS_KEY_PATH` | `/opt/render/project/src/secrets/apns.p8` | Manual |
| `APNS_KEY_ID` | `your-key-id` | Manual |
| `APNS_TEAM_ID` | `your-team-id` | Manual |
| `APNS_BUNDLE_ID` | `com.yourcompany.birjob` | Manual |

### Worker Service Environment Variables

| Variable | Value | Source |
|----------|-------|---------|
| `DATABASE_URL` | Auto-configured | From PostgreSQL service |
| `REDIS_URL` | Auto-configured | From Redis service |
| `SECRET_KEY` | Sync from API service | Sync |
| `MATCH_ENGINE_INTERVAL_MINUTES` | `5` | Manual |
| `LOG_LEVEL` | `INFO` | Manual |

---

## 📦 Deployment Steps

### Step 1: Prepare Repository
```bash
# Ensure code is committed
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Services on Render

#### Option A: Using Blueprint (render.yaml)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically create all services from `render.yaml`

#### Option B: Manual Creation
1. Create PostgreSQL database first
2. Create Redis service
3. Create Web Service (API)
4. Create Worker Service (Match Engine)
5. Configure environment variables

### Step 3: Configure Environment Variables
1. Set auto-generated variables (SECRET_KEY, API_KEY)
2. Upload APNs .p8 file
3. Set APNs configuration variables
4. Verify database and Redis connections

### Step 4: Deploy and Monitor
1. Services will auto-deploy on code push
2. Check logs for any errors
3. Verify health check endpoints
4. Test API functionality

---

## 🔍 Health Check Endpoints

After deployment, verify these endpoints:

- **Health Check:** `https://your-service.onrender.com/api/v1/health`
- **API Docs:** `https://your-service.onrender.com/docs`
- **Metrics:** `https://your-service.onrender.com/metrics`

---

## 🐛 Troubleshooting

### Build Failures
- Check `requirements.txt` is correct
- Verify Python version compatibility
- Check for dependency conflicts

### Start Command Failures
- Verify database connection string
- Check migration status
- Review environment variables

### Migration Issues
- Database schema permissions
- Connection timeout
- Missing environment variables

### Worker Service Issues
- Redis connection problems
- Import path errors
- Background job scheduling

---

## 📊 Expected Resource Usage

### Starter Plan
- **Memory:** ~256MB per service
- **CPU:** Light usage
- **Cost:** ~$7/service/month

### Standard Plan
- **Memory:** ~512MB per service
- **CPU:** Moderate usage
- **Cost:** ~$25/service/month

### Total Monthly Cost
- **Development:** ~$28/month (4 services on Starter)
- **Production:** ~$97/month (mix of Starter/Standard)