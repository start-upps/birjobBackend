# Job Notification System

## Overview

The job notification system automatically matches new jobs with user keywords and sends push notifications to prevent users from missing relevant opportunities. The system implements Change Data Capture (CDC) logic to handle the hourly job scraper data updates.

## Key Features

### 1. Keyword Matching
- **Flexible Matching**: Supports both exact word boundary matching and substring matching
- **Multi-field Search**: Matches against job title, company, description, location, category, type, and skills
- **Case Insensitive**: All matching is case-insensitive
- **Multiple Keywords**: Users can have multiple keywords, any match triggers a notification

### 2. Duplicate Prevention
- **Unique Job Keys**: Uses MD5 hash of normalized company + title to identify duplicate jobs
- **Database Constraints**: Unique constraint on `user_id + job_unique_key` prevents duplicate notifications
- **Normalization**: Removes special characters and normalizes text for consistent duplicate detection

### 3. Notification Throttling
- **Rate Limiting**: Prevents spam with configurable hourly/daily limits
- **Quiet Hours**: Respects user timezone for quiet hours (configurable)
- **Smart Scheduling**: Runs notifications during business hours (8 AM - 10 PM)

### 4. Change Data Capture (CDC)
- **Hourly Processing**: Automatically processes new jobs every hour
- **Recent Job Detection**: Only processes jobs from the last 2 hours
- **Batch Processing**: Configurable batch size for performance
- **Background Processing**: Non-blocking background task execution

## Database Schema

### job_notification_history
```sql
CREATE TABLE iosapp.job_notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES iosapp.users(id) ON DELETE CASCADE,
    job_unique_key VARCHAR(255) NOT NULL,  -- MD5 hash of company + title
    job_id INTEGER NOT NULL,
    job_title VARCHAR(500) NOT NULL,
    job_company VARCHAR(255) NOT NULL,
    job_source VARCHAR(100),
    matched_keywords JSONB DEFAULT '[]'::jsonb,
    notification_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_user_job_notification UNIQUE (user_id, job_unique_key)
);
```

## API Endpoints

### POST /api/v1/notifications/job-match
Send a job match notification to a specific user.

**Request Body:**
```json
{
  "device_id": "string",
  "job_id": 123,
  "job_title": "iOS Developer",
  "job_company": "Apple Inc.",
  "job_source": "apple.com",
  "matched_keywords": ["iOS", "Swift"]
}
```

### GET /api/v1/notifications/history/{device_id}
Get notification history for a user.

**Query Parameters:**
- `limit` (optional): Max number of records to return (default: 50, max: 100)

### PUT /api/v1/notifications/settings
Update notification settings for a user.

**Request Body:**
```json
{
  "device_id": "string",
  "notifications_enabled": true,
  "keywords": ["iOS", "Swift", "React Native"]
}
```

### POST /api/v1/notifications/trigger
Trigger job matching notifications for all users.

**Request Body:**
```json
{
  "source_filter": "indeed.com",  // optional
  "limit": 100,                   // optional
  "dry_run": true                 // optional
}
```

### POST /api/v1/notifications/test-run
Test run notifications immediately (for testing).

**Query Parameters:**
- `dry_run` (optional): Run in test mode without sending notifications (default: true)

### GET /api/v1/notifications/stats
Get notification statistics.

### DELETE /api/v1/notifications/cleanup
Clean up old notification history records.

**Query Parameters:**
- `days_old` (optional): Delete records older than this many days (default: 30)

## Configuration

### Environment Variables
```bash
# Notification settings
MAX_NOTIFICATIONS_PER_HOUR=10
MAX_NOTIFICATIONS_PER_DAY=50
QUIET_HOURS_START=22  # 10 PM
QUIET_HOURS_END=8     # 8 AM
NOTIFICATION_BATCH_SIZE=200
NOTIFICATION_CLEANUP_DAYS=30

# APNs settings (for push notifications)
APNS_PRIVATE_KEY=your_private_key_content
APNS_KEY_ID=your_key_id
APNS_TEAM_ID=your_team_id
APNS_BUNDLE_ID=your_bundle_id
APNS_SANDBOX=true
```

## Usage Examples

### 1. Setting Up User Keywords
```bash
curl -X PUT "http://localhost:8000/api/v1/notifications/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "user-device-123",
    "notifications_enabled": true,
    "keywords": ["iOS Developer", "Swift", "React Native", "Mobile"]
  }'
```

### 2. Manual Job Notification
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/job-match" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "user-device-123",
    "job_id": 456,
    "job_title": "Senior iOS Developer",
    "job_company": "Apple Inc.",
    "job_source": "apple.com",
    "matched_keywords": ["iOS", "Swift"]
  }'
```

### 3. Test Run (Dry Run)
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/test-run?dry_run=true"
```

### 4. Get Notification History
```bash
curl "http://localhost:8000/api/v1/notifications/history/user-device-123?limit=20"
```

### 5. Get Statistics
```bash
curl "http://localhost:8000/api/v1/notifications/stats"
```

## Keyword Matching Logic

The system uses intelligent keyword matching:

1. **Normalization**: Removes special characters, converts to lowercase
2. **Word Boundary Matching**: Prefers exact word matches
3. **Substring Matching**: Falls back to substring for keywords ≥3 characters
4. **Multi-field Search**: Searches across all relevant job fields

**Example:**
- Keyword: "iOS"
- Matches: "iOS Developer", "Senior iOS Engineer", "iOS/Android Developer"
- Doesn't match: "iOS12" (word boundary), "IoS" (case sensitive)

## Scheduling

The notification scheduler runs automatically:

- **Startup**: Starts with the FastAPI application
- **Frequency**: Checks every 5 minutes
- **Active Hours**: Only runs notifications 8 AM - 10 PM
- **Timing**: Processes at :05 and :35 past each hour
- **Cleanup**: Runs weekly cleanup on Sundays at 3 AM

## Monitoring

### Logs
- All notification activities are logged with appropriate levels
- Errors are captured with full stack traces
- Statistics are logged after each processing run

### Metrics
- Track notification success/failure rates
- Monitor keyword match frequencies
- Watch for duplicate prevention effectiveness

## Performance Considerations

1. **Batch Processing**: Process jobs in configurable batches
2. **Database Indexes**: Optimized indexes for fast lookups
3. **Async Processing**: Non-blocking background tasks
4. **Connection Pooling**: Efficient database connection management
5. **Caching**: Redis for notification throttling

## Security

1. **Input Validation**: All inputs are validated using Pydantic schemas
2. **SQL Injection Prevention**: Parameterized queries only
3. **Rate Limiting**: Prevents notification spam
4. **Device Validation**: Ensures notifications only go to valid devices

## Troubleshooting

### Common Issues

1. **No Notifications Received**
   - Check user has notifications enabled
   - Verify keywords are set correctly
   - Check device token is active
   - Review notification throttling limits

2. **Duplicate Notifications**
   - Verify unique constraint is working
   - Check job_unique_key generation
   - Review notification history table

3. **Performance Issues**
   - Monitor batch size settings
   - Check database query performance
   - Review notification frequency settings

### Debug Commands

```bash
# Check notification history
psql -c "SELECT * FROM iosapp.job_notification_history ORDER BY notification_sent_at DESC LIMIT 10;"

# Check active users with keywords
psql -c "SELECT u.id, u.email, u.keywords FROM iosapp.users u WHERE u.notifications_enabled = true AND u.keywords IS NOT NULL;"

# Check recent jobs
psql -c "SELECT id, title, company, source, posted_date FROM scraper.jobs_jobpost WHERE posted_date >= NOW() - INTERVAL '2 hours' ORDER BY posted_date DESC LIMIT 10;"
```

## Testing

### Unit Tests
Run individual component tests:
```bash
python -c "from app.services.job_notification_service import JobNotificationService; service = JobNotificationService(); print('Service OK')"
```

### Integration Tests
Test the full notification flow:
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/test-run?dry_run=true"
```

### Load Testing
Test with multiple users and jobs:
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/trigger" \
  -H "Content-Type: application/json" \
  -d '{"limit": 500, "dry_run": true}'
```

## Future Enhancements

1. **Advanced Matching**: ML-based job recommendations
2. **User Preferences**: Customizable notification timing
3. **Rich Notifications**: Include job details in notification payload
4. **Analytics**: Detailed user engagement metrics
5. **A/B Testing**: Test different notification strategies