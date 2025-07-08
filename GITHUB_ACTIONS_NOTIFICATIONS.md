# 🚀 GitHub Actions Notification System

## Overview
Use GitHub Actions to automatically send push notifications based on various triggers like deployments, schedules, or webhook events.

## 🔧 Setup Instructions

### 1. Configure Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
```
BACKEND_URL=https://birjobbackend-ir3e.onrender.com
SLACK_WEBHOOK=https://hooks.slack.com/... (optional)
```

### 2. Available Workflows

#### 📅 **Scheduled Notifications** (`scheduled-job-check.yml`)
- **Trigger**: Every 5 minutes during business hours (9 AM - 6 PM UTC, Mon-Fri)
- **Purpose**: Regular job notification processing
- **What it does**:
  - Gets active devices
  - Processes job notifications
  - Sends summary to Slack (optional)
  - Performs health checks

#### 📨 **Manual Notifications** (`send-notifications.yml`)
- **Trigger**: Manual trigger from GitHub UI or every 30 minutes
- **Purpose**: On-demand notification sending
- **Parameters**:
  - `dry_run`: Test mode (true/false)
  - `limit`: Number of jobs to process

#### 🚀 **Deployment Notifications** (`deployment-notifications.yml`)
- **Trigger**: Code push to main branch
- **Purpose**: Notify users of updates and trigger fresh job checks
- **What it does**:
  - Waits for deployment
  - Verifies backend health
  - Sends system notifications
  - Triggers fresh job processing

#### 🔗 **Webhook Notifications** (`webhook-notifications.yml`)
- **Trigger**: External webhooks or manual dispatch
- **Purpose**: External system integration
- **Supported events**:
  - `send-notification`: General notifications
  - `job-scraper-complete`: After job scraping
  - `user-registration`: Welcome new users
  - `emergency-notification`: Critical alerts

## 📱 How to Use

### Manual Trigger (GitHub UI)
1. Go to Actions tab in GitHub
2. Select workflow (e.g., "Send Job Notifications")
3. Click "Run workflow"
4. Set parameters and run

### Webhook Trigger (External Systems)
```bash
# Send system notification
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/birjobBackend/dispatches \
  -d '{
    "event_type": "send-notification",
    "client_payload": {
      "device_id": "optional-specific-device",
      "message": "Custom notification message"
    }
  }'
```

### Schedule-based (Automatic)
- Runs automatically based on cron schedules
- No manual intervention needed
- Monitors and processes jobs continuously

## 🎯 Use Cases

### 1. **Job Scraper Integration**
When your job scraper completes:
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/birjobBackend/dispatches \
  -d '{"event_type": "job-scraper-complete"}'
```

### 2. **New User Welcome**
When a user registers:
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/birjobBackend/dispatches \
  -d '{
    "event_type": "user-registration",
    "client_payload": {"device_id": "new-user-device-id"}
  }'
```

### 3. **Emergency Alerts**
For critical system notifications:
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/birjobBackend/dispatches \
  -d '{
    "event_type": "emergency-notification",
    "client_payload": {"message": "System maintenance in 10 minutes"}
  }'
```

### 4. **Deployment Automation**
Automatically triggers when you push code:
- Verifies deployment health
- Sends "app updated" notifications
- Triggers fresh job processing

## 📊 Monitoring

### View Results
1. Go to GitHub Actions tab
2. Click on any workflow run
3. Expand steps to see detailed logs
4. Monitor success/failure rates

### Slack Integration (Optional)
If you set `SLACK_WEBHOOK` secret:
- Get summaries of notification runs
- Monitor system health
- Track notification counts

## 🔒 Security

### GitHub Token Requirements
For webhook triggers, create a GitHub Personal Access Token with:
- `repo` scope (for private repos)
- `public_repo` scope (for public repos)

### API Access
- Uses your existing backend API endpoints
- No additional authentication needed
- Respects existing rate limits

## ⚡ Performance

### Efficiency
- Runs only when needed
- Processes multiple devices in parallel
- Includes error handling and retries
- Automatic health checks

### Cost
- GitHub Actions provides 2,000 free minutes/month
- Each workflow run takes ~1-3 minutes
- Very cost-effective for notification automation

## 🛠️ Customization

### Modify Schedules
Edit cron expressions in workflow files:
```yaml
schedule:
  - cron: '*/10 * * * *'  # Every 10 minutes
  - cron: '0 9 * * 1-5'   # 9 AM Monday-Friday
  - cron: '0 */2 * * *'   # Every 2 hours
```

### Add Custom Triggers
Add new event types to webhook workflow:
```yaml
repository_dispatch:
  types: 
    - send-notification
    - your-custom-event
```

### Environment-specific Configs
Use different secrets for staging/production:
```yaml
BACKEND_URL_STAGING=https://staging-backend.com
BACKEND_URL_PRODUCTION=https://production-backend.com
```

## 🎉 Benefits

✅ **Automated**: No manual intervention needed
✅ **Reliable**: GitHub's infrastructure handles execution
✅ **Scalable**: Works with any number of devices
✅ **Flexible**: Multiple trigger types and customization
✅ **Free**: Uses GitHub's free tier effectively
✅ **Integrated**: Part of your existing development workflow
✅ **Monitored**: Built-in logging and error tracking

Your notification system can now be triggered by deployments, schedules, external systems, or manual triggers - all through GitHub Actions! 🚀