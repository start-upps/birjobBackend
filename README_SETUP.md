# iOS Native App Backend - Setup Guide

This backend provides REST APIs for iOS job matching app with push notifications, built according to the specifications in `README.md`.

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Environment Setup

1. **Clone and setup environment:**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configurations
nano .env
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Database setup:**
```bash
# Create database and run schema
psql -U postgres -c "CREATE DATABASE birjob_ios;"
psql -U postgres -d birjob_ios -f database_schema.sql
```

4. **APNs Setup (for push notifications):**
```bash
# Create secrets directory
mkdir secrets

# Add your APNs .p8 key file
cp /path/to/your/AuthKey_XXXXXXXXXX.p8 secrets/apns.p8

# Update .env with APNs credentials
APNS_KEY_ID=your-key-id
APNS_TEAM_ID=your-team-id
APNS_BUNDLE_ID=com.yourcompany.birjob
```

5. **Start the application:**
```bash
# Start the API server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the match engine
python -c "import asyncio; from app.services.match_engine import job_scheduler; asyncio.run(job_scheduler.start())"
```

## Docker Setup (Recommended)

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production
```bash
# Create production environment file
cp .env.example .env.production

# Edit production settings
nano .env.production

# Start production stack
docker-compose -f docker-compose.production.yml up -d
```

## API Endpoints

The API will be available at `http://localhost:8000`

### Core Endpoints

#### Device Management
- `POST /api/v1/devices/register` - Register device
- `DELETE /api/v1/devices/{device_id}` - Unregister device
- `GET /api/v1/devices/{device_id}/status` - Get device status

#### Keyword Subscriptions
- `POST /api/v1/keywords` - Create subscription
- `GET /api/v1/keywords/{device_id}` - Get subscriptions
- `PUT /api/v1/keywords/{subscription_id}` - Update subscription
- `DELETE /api/v1/keywords/{subscription_id}` - Delete subscription

#### Job Matches
- `GET /api/v1/matches/{device_id}` - Get matches
- `POST /api/v1/matches/{match_id}/read` - Mark as read
- `GET /api/v1/matches/{device_id}/unread-count` - Get unread count

#### Health & Monitoring
- `GET /api/v1/health` - System health
- `GET /api/v1/health/status/scraper` - Scraper status
- `GET /metrics` - Prometheus metrics

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT secret key | - |
| `API_KEY` | Admin API key | - |
| `APNS_KEY_PATH` | Path to APNs .p8 file | `/secrets/apns.p8` |
| `APNS_KEY_ID` | APNs Key ID | - |
| `APNS_TEAM_ID` | APNs Team ID | - |
| `APNS_BUNDLE_ID` | iOS app bundle ID | - |
| `APNS_SANDBOX` | Use APNs sandbox | `true` |
| `MATCH_ENGINE_INTERVAL_MINUTES` | Job matching interval | `5` |
| `MAX_NOTIFICATIONS_PER_HOUR` | Hourly notification limit | `5` |
| `MAX_NOTIFICATIONS_PER_DAY` | Daily notification limit | `20` |

### Database Schema

The application uses the `iosapp` schema with the following tables:
- `device_tokens` - Device registrations
- `keyword_subscriptions` - User keyword preferences
- `job_matches` - Matched jobs for devices
- `push_notifications` - Notification delivery tracking
- `processed_jobs` - Prevents duplicate processing

### Background Services

The match engine runs as a separate process that:
1. Checks for new jobs every 5 minutes
2. Matches jobs against active subscriptions
3. Sends push notifications for matches
4. Implements smart throttling and quiet hours

## Integration with Existing Scraper

This backend integrates with your existing scraper by:
1. Reading jobs from `scraper.jobs_jobpost` table
2. Matching new jobs against iOS device subscriptions
3. Creating entries in `iosapp.job_matches` for matches
4. Sending push notifications via APNs

No changes are required to your existing scraper code.

## Production Deployment

### Load Balancing

The API is stateless and can be horizontally scaled:

```yaml
# docker-compose.production.yml
api:
  deploy:
    replicas: 3
```

### Security

Production security features included:
- Rate limiting via Nginx
- Security headers
- JWT-based device authentication
- API key authentication for admin endpoints
- Input validation and sanitization

### Monitoring

Built-in monitoring includes:
- Prometheus metrics at `/metrics`
- Structured JSON logging
- Health check endpoints
- APNs delivery tracking

### SSL/TLS

Configure SSL in production:
1. Update `nginx.conf` with your SSL certificates
2. Set `APNS_SANDBOX=false` for production APNs
3. Update `ALLOWED_ORIGINS` for CORS

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Troubleshooting

### Common Issues

1. **Database connection errors:**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` format
   - Ensure `iosapp` schema exists

2. **Push notifications not working:**
   - Verify APNs credentials in `.env`
   - Check `secrets/apns.p8` file exists
   - Ensure device tokens are valid

3. **No job matches:**
   - Verify scraper is populating `scraper.jobs_jobpost`
   - Check match engine is running
   - Review keyword subscriptions

### Logs

Check application logs:
```bash
# Docker logs
docker-compose logs -f api
docker-compose logs -f match-engine

# System logs
tail -f /var/log/birjob-backend.log
```

### Health Checks

Monitor system health:
```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Detailed scraper status
curl http://localhost:8000/api/v1/health/status/scraper
```

## Support

For issues and feature requests, please refer to the main `README.md` file which contains the complete specification and architecture details.