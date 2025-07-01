# Test and Run Guide for BirJob Backend

This guide covers how to test, develop, and manage the BirJob Backend API using the provided scripts and tools.

## 📁 Files Overview

### Test Files
- **`test_api_comprehensive.py`** - Comprehensive Python test suite for all API endpoints
- **`run_tests.sh`** - Bash script for running various test scenarios
- **`TEST_AND_RUN_GUIDE.md`** - This documentation file

### Development & Production Scripts
- **`run_development.sh`** - Development server management script
- **`run_production.sh`** - Production monitoring and management script

## 🧪 Testing the API

### Quick Health Check
```bash
# Test if the API is responding
curl -s "https://birjobbackend-ir3e.onrender.com/api/v1/health"
```

### Comprehensive Test Suite

#### 1. Install Dependencies (if needed)
```bash
# Create virtual environment
python3 -m venv test_env
source test_env/bin/activate
pip install httpx

# Or use system packages (if allowed)
pip3 install httpx --user
```

#### 2. Run Full Test Suite
```bash
# Run comprehensive tests against production
python3 test_api_comprehensive.py

# Or use the test runner script
./run_tests.sh
```

#### 3. Test Runner Script Options
```bash
# Run all tests
./run_tests.sh

# Test specific endpoint
./run_tests.sh --endpoint health
./run_tests.sh --endpoint jobs
./run_tests.sh --endpoint analytics

# Run load tests
./run_tests.sh --load

# Generate HTML report
./run_tests.sh --report

# Show help
./run_tests.sh --help
```

### Test Results
Tests generate detailed results in multiple formats:
- **JSON results**: `test_results_TIMESTAMP.json`
- **CSV export**: `api_test_results_TIMESTAMP.csv`
- **Console output**: Real-time test progress
- **HTML reports**: `test_results/test_report_TIMESTAMP.html`

## 🚀 Development Environment

### Setup Development Environment
```bash
# Setup virtual environment and dependencies
./run_development.sh setup

# Start development server
./run_development.sh start

# Check server status
./run_development.sh status

# View logs
./run_development.sh logs

# Follow logs in real-time
./run_development.sh follow
```

### Development Server Management
```bash
# Start server on custom port
DEV_PORT=8080 ./run_development.sh start

# Start server on custom host
DEV_HOST=0.0.0.0 ./run_development.sh start

# Restart server
./run_development.sh restart

# Stop server
./run_development.sh stop

# Run development tests
./run_development.sh test
```

### Code Quality Tools
```bash
# Format code with black and isort
./run_development.sh format

# Lint code with flake8
./run_development.sh lint

# Clean up logs and temporary files
./run_development.sh clean
```

## 🏭 Production Management

### Production Health Monitoring
```bash
# Check production health
./run_production.sh health

# Monitor metrics
./run_production.sh monitor

# Check database connectivity
./run_production.sh database

# Check external dependencies
./run_production.sh dependencies
```

### Production Testing
```bash
# Run comprehensive production tests
./run_production.sh test

# Run load tests (10 concurrent, 100 total requests)
./run_production.sh load-test

# Custom load test (20 concurrent, 200 total)
./run_production.sh load-test 20 200
```

### Production Maintenance
```bash
# Create data backup
./run_production.sh backup

# Generate status report
./run_production.sh report

# View recent logs
./run_production.sh logs

# Clean up old files
./run_production.sh clean
```

### Continuous Monitoring
```bash
# Start continuous monitoring (checks every 5 minutes)
./run_production.sh watch

# Stop with Ctrl+C
```

## 📊 Test Coverage

The comprehensive test suite covers:

### ✅ Tested Endpoints

#### Device Management
- `POST /devices/register` - Device registration
- `GET /devices/{device_id}/status` - Device status check
- `DELETE /devices/{device_id}` - Device unregistration

#### User Profile Management
- `POST /users/profile` - Create/update user profile
- `GET /users/profile/{device_id}` - Get user profile

#### Job Management
- `GET /jobs` - Job listing with filters and pagination
- `GET /jobs/{job_id}` - Specific job details
- `GET /jobs/stats/summary` - Job statistics

#### AI Features
- `POST /ai/analyze` - General AI analysis
- `POST /ai/job-advice` - Job search advice

#### Keyword Management
- `POST /keywords` - Subscribe to keywords
- `GET /keywords/{device_id}` - Get keyword subscriptions

#### Analytics
- `GET /analytics/jobs/overview` - Job analytics overview
- `GET /analytics/jobs/by-source` - Jobs by source
- `GET /analytics/jobs/keywords` - Popular keywords

#### Health & Monitoring
- `GET /health` - System health check
- `GET /health/status/scraper` - Scraper status

#### Job Matching
- `GET /matches/{device_id}` - Get job matches
- `GET /matches/{device_id}/unread-count` - Unread matches count

### 🔍 Test Features

#### Automated Testing
- **Response Validation**: Status codes, JSON structure, required fields
- **Data Integrity**: UUID format validation, timestamp verification
- **Error Handling**: Invalid requests, missing parameters
- **Performance**: Response time measurement
- **End-to-End Flows**: Complete user registration → profile → matching workflow

#### Load Testing
- **Concurrent Requests**: Configurable concurrent request testing
- **Response Time Analysis**: Average, min, max response times
- **Success Rate Monitoring**: Failed vs successful request ratios
- **Resource Usage**: Basic performance metrics

#### Reporting
- **JSON Export**: Detailed test results for automation
- **CSV Export**: Spreadsheet-compatible format
- **HTML Reports**: User-friendly visual reports
- **Console Output**: Real-time test progress

## 🛠 Configuration

### Environment Variables
```bash
# Development
export DEV_HOST=127.0.0.1
export DEV_PORT=8000

# Testing
export API_BASE_URL=https://birjobbackend-ir3e.onrender.com/api/v1
export API_KEY=birjob-ios-api-key-2024
export TEST_TIMEOUT=30

# Production monitoring
export MONITOR_INTERVAL=300  # 5 minutes
export BACKUP_RETENTION=30   # 30 days
export LOG_RETENTION=7       # 7 days
```

### Script Configuration
All scripts support configuration through:
- **Environment variables**: Set behavior globally
- **Command line arguments**: Override specific options
- **Configuration files**: `.env` files for persistent settings

## 📈 Performance Benchmarks

### Current Production Metrics (as of testing)
- **Health Check Response**: ~1-2 seconds
- **Job Listing (20 items)**: ~2-3 seconds
- **Job Statistics**: ~1-2 seconds
- **Analytics Overview**: ~1-2 seconds
- **Total Jobs**: 4,360 active listings
- **Job Sources**: 37 different sources
- **Companies**: 1,714 unique companies

### Load Test Results
- **Concurrent Users**: Up to 20 tested successfully
- **Success Rate**: 100% under normal load
- **Response Time**: Average 1.5-2.5 seconds
- **Throughput**: ~10-15 requests per second

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Make scripts executable
chmod +x run_tests.sh run_development.sh run_production.sh test_api_comprehensive.py
```

#### 2. Missing Dependencies
```bash
# Install required packages
pip3 install httpx --user
# or
python3 -m pip install httpx --break-system-packages
```

#### 3. API Unreachable
```bash
# Check API status
curl -I https://birjobbackend-ir3e.onrender.com/api/v1/health

# Check internet connectivity
ping google.com
```

#### 4. Test Failures
- **Check API status**: Ensure production API is running
- **Verify credentials**: Check API key configuration
- **Review logs**: Look at test output for specific errors
- **Check timeouts**: Increase timeout for slow networks

### Debug Mode
```bash
# Run tests with verbose output
python3 test_api_comprehensive.py --verbose

# Enable debug logging in scripts
DEBUG=1 ./run_tests.sh

# Check specific endpoint manually
curl -v "https://birjobbackend-ir3e.onrender.com/api/v1/health"
```

## 📞 Support and Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor production health: `./run_production.sh health`
- Check recent logs: `./run_production.sh logs`

#### Weekly
- Run comprehensive tests: `./run_production.sh test`
- Generate status report: `./run_production.sh report`
- Create backup: `./run_production.sh backup`

#### Monthly
- Run load tests: `./run_production.sh load-test 50 500`
- Clean up old files: `./run_production.sh clean`
- Review performance metrics

### Monitoring Setup
For continuous monitoring, consider setting up:
- **Cron jobs**: Schedule regular health checks
- **Log aggregation**: Centralize log collection
- **Alerting**: Set up notifications for failures
- **Dashboard**: Create visual monitoring dashboard

### Example Cron Jobs
```bash
# Check health every 5 minutes
*/5 * * * * /path/to/run_production.sh health >> /var/log/birjob_health.log 2>&1

# Generate daily report
0 9 * * * /path/to/run_production.sh report

# Weekly comprehensive test
0 2 * * 1 /path/to/run_production.sh test

# Monthly cleanup
0 3 1 * * /path/to/run_production.sh clean
```

---

**Last Updated**: July 1, 2025  
**Version**: 1.0  
**Compatibility**: BirJob Backend API v1.0

This guide provides comprehensive instructions for testing and managing the BirJob Backend API. For additional support or questions, refer to the API documentation or contact the development team.