#!/bin/bash
# Production Server Management Script for BirJob Backend
# Handles production deployment, monitoring, and maintenance tasks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_URL="https://birjobbackend-ir3e.onrender.com"
API_BASE="$PRODUCTION_URL/api/v1"
LOGS_DIR="$SCRIPT_DIR/production_logs"
BACKUP_DIR="$SCRIPT_DIR/backups"
MONITORING_DIR="$SCRIPT_DIR/monitoring"

echo -e "${PURPLE}🚀 BirJob Backend Production Manager${NC}"
echo -e "${PURPLE}====================================${NC}"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    case $status in
        "info")
            echo -e "${BLUE}ℹ️  [$timestamp] $message${NC}"
            ;;
        "success")
            echo -e "${GREEN}✅ [$timestamp] $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  [$timestamp] $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ [$timestamp] $message${NC}"
            ;;
        "critical")
            echo -e "${RED}🚨 [$timestamp] CRITICAL: $message${NC}"
            ;;
    esac
}

# Function to log to file
log_to_file() {
    local message="$1"
    local log_file="$LOGS_DIR/production_$(date +%Y%m%d).log"
    mkdir -p "$LOGS_DIR"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $message" >> "$log_file"
}

# Function to check production server health
check_health() {
    print_status "info" "Checking production server health..."
    
    local health_response
    local start_time=$(date +%s)
    
    health_response=$(curl -s -f --max-time 30 "$API_BASE/health" 2>/dev/null || echo "failed")
    local end_time=$(date +%s)
    local response_time=$((end_time - start_time))
    
    if [ "$health_response" = "failed" ]; then
        print_status "critical" "Production API health check failed!"
        log_to_file "HEALTH_CHECK_FAILED: API unreachable"
        return 1
    else
        # Parse JSON response to check status
        local status=$(echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'unknown'))
except:
    print('error')
" 2>/dev/null || echo "error")
        
        if [ "$status" = "healthy" ]; then
            print_status "success" "Production API is healthy (${response_time}s response time)"
            log_to_file "HEALTH_CHECK_SUCCESS: Response time ${response_time}s"
            
            # Show detailed health info
            echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    services = data.get('services', {})
    metrics = data.get('metrics', {})
    print('Services Status:')
    for service, status in services.items():
        print(f'  {service}: {status}')
    print('Metrics:')
    for metric, value in metrics.items():
        print(f'  {metric}: {value}')
except Exception as e:
    print(f'Failed to parse health response: {e}')
"
            return 0
        else
            print_status "error" "Production API reports unhealthy status: $status"
            log_to_file "HEALTH_CHECK_DEGRADED: Status $status"
            return 1
        fi
    fi
}

# Function to run comprehensive production tests
run_production_tests() {
    print_status "info" "Running production API tests..."
    
    # Check if test file exists
    if [ ! -f "$SCRIPT_DIR/test_api_comprehensive.py" ]; then
        print_status "error" "Test file not found. Run from project root directory."
        return 1
    fi
    
    # Create logs directory
    mkdir -p "$LOGS_DIR"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local test_log="$LOGS_DIR/production_test_$timestamp.log"
    
    print_status "info" "Running comprehensive test suite against production..."
    
    # Run tests and capture output
    if python3 "$SCRIPT_DIR/test_api_comprehensive.py" 2>&1 | tee "$test_log"; then
        print_status "success" "Production tests completed successfully"
        log_to_file "PRODUCTION_TESTS_SUCCESS: All tests passed"
        
        # Move test results to logs directory
        mv test_results_*.json "$LOGS_DIR/" 2>/dev/null || true
        mv api_test_results_*.* "$LOGS_DIR/" 2>/dev/null || true
        
        return 0
    else
        print_status "error" "Production tests failed"
        log_to_file "PRODUCTION_TESTS_FAILED: Check test log $test_log"
        return 1
    fi
}

# Function to monitor production metrics
monitor_metrics() {
    print_status "info" "Collecting production metrics..."
    
    mkdir -p "$MONITORING_DIR"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local metrics_file="$MONITORING_DIR/metrics_$timestamp.json"
    
    # Collect various metrics
    {
        echo "{"
        echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\","
        
        # Health metrics
        echo "  \"health\": $(curl -s "$API_BASE/health" 2>/dev/null || echo '{"status": "unreachable"}'),"
        
        # Job statistics
        echo "  \"job_stats\": $(curl -s "$API_BASE/jobs/stats/summary" 2>/dev/null || echo '{"error": "unavailable"}'),"
        
        # Analytics overview
        echo "  \"analytics\": $(curl -s "$API_BASE/analytics/jobs/overview" 2>/dev/null || echo '{"error": "unavailable"}'),"
        
        # Response time test
        local start_time=$(date +%s%3N)
        curl -s "$API_BASE/health" > /dev/null 2>&1
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))
        echo "  \"response_time_ms\": $response_time"
        
        echo "}"
    } > "$metrics_file"
    
    print_status "success" "Metrics collected and saved to $metrics_file"
    
    # Display summary
    python3 -c "
import json
try:
    with open('$metrics_file', 'r') as f:
        data = json.load(f)
    
    print('📊 Production Metrics Summary:')
    print(f'  Timestamp: {data.get(\"timestamp\", \"unknown\")}')
    print(f'  Response Time: {data.get(\"response_time_ms\", \"unknown\")}ms')
    
    health = data.get('health', {})
    print(f'  Health Status: {health.get(\"status\", \"unknown\")}')
    
    job_stats = data.get('job_stats', {}).get('data', {})
    if 'total_jobs' in job_stats:
        print(f'  Total Jobs: {job_stats[\"total_jobs\"]}')
        print(f'  Recent Jobs (24h): {job_stats.get(\"recent_jobs_24h\", \"unknown\")}')
    
    analytics = data.get('analytics', {})
    if 'total_jobs' in analytics:
        print(f'  Analytics Total: {analytics[\"total_jobs\"]}')
        print(f'  Unique Companies: {analytics.get(\"unique_companies\", \"unknown\")}')
        
except Exception as e:
    print(f'Failed to parse metrics: {e}')
"
}

# Function to check database connectivity
check_database() {
    print_status "info" "Checking database connectivity..."
    
    # Test database through API endpoints
    local job_count_response=$(curl -s "$API_BASE/jobs/stats/summary" 2>/dev/null || echo "failed")
    
    if [ "$job_count_response" = "failed" ]; then
        print_status "error" "Database connectivity check failed"
        log_to_file "DATABASE_CHECK_FAILED: Could not retrieve job stats"
        return 1
    else
        local total_jobs=$(echo "$job_count_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('data', {}).get('total_jobs', 'unknown'))
except:
    print('error')
" 2>/dev/null)
        
        if [ "$total_jobs" != "error" ] && [ "$total_jobs" != "unknown" ]; then
            print_status "success" "Database is accessible (Total jobs: $total_jobs)"
            log_to_file "DATABASE_CHECK_SUCCESS: $total_jobs jobs available"
            return 0
        else
            print_status "error" "Database response format error"
            log_to_file "DATABASE_CHECK_ERROR: Invalid response format"
            return 1
        fi
    fi
}

# Function to check external dependencies
check_dependencies() {
    print_status "info" "Checking external dependencies..."
    
    local all_good=true
    
    # Check Redis (through health endpoint)
    local health_response=$(curl -s "$API_BASE/health" 2>/dev/null)
    local redis_status=$(echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('services', {}).get('redis', 'unknown'))
except:
    print('error')
" 2>/dev/null)
    
    if [ "$redis_status" = "healthy" ]; then
        print_status "success" "Redis is healthy"
    else
        print_status "error" "Redis status: $redis_status"
        all_good=false
    fi
    
    # Check APNS (through health endpoint)
    local apns_status=$(echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('services', {}).get('apns', 'unknown'))
except:
    print('error')
" 2>/dev/null)
    
    if [ "$apns_status" = "healthy" ]; then
        print_status "success" "APNS is healthy"
    else
        print_status "warning" "APNS status: $apns_status"
    fi
    
    # Check scraper (through health endpoint)
    local scraper_status=$(echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('services', {}).get('scraper', 'unknown'))
except:
    print('error')
" 2>/dev/null)
    
    if [ "$scraper_status" = "healthy" ]; then
        print_status "success" "Scraper is healthy"
    else
        print_status "warning" "Scraper status: $scraper_status"
    fi
    
    if [ "$all_good" = true ]; then
        log_to_file "DEPENDENCIES_CHECK_SUCCESS: All dependencies healthy"
        return 0
    else
        log_to_file "DEPENDENCIES_CHECK_WARNING: Some dependencies degraded"
        return 1
    fi
}

# Function to perform load testing
run_load_test() {
    local concurrent_requests=${1:-10}
    local total_requests=${2:-100}
    
    print_status "info" "Running load test: $concurrent_requests concurrent, $total_requests total requests"
    
    mkdir -p "$MONITORING_DIR"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local load_test_log="$MONITORING_DIR/load_test_$timestamp.log"
    
    # Simple load test using curl
    {
        echo "Load Test Report"
        echo "================"
        echo "Start Time: $(date)"
        echo "Concurrent Requests: $concurrent_requests"
        echo "Total Requests: $total_requests"
        echo "Target: $API_BASE/health"
        echo ""
        
        local start_time=$(date +%s)
        local success_count=0
        local failure_count=0
        
        # Run requests in parallel batches
        for ((batch=0; batch<total_requests; batch+=concurrent_requests)); do
            local batch_pids=()
            
            for ((i=0; i<concurrent_requests && (batch+i)<total_requests; i++)); do
                {
                    if curl -s -f --max-time 10 "$API_BASE/health" > /dev/null 2>&1; then
                        echo "SUCCESS"
                    else
                        echo "FAILURE"
                    fi
                } &
                batch_pids+=($!)
            done
            
            # Wait for batch to complete
            for pid in "${batch_pids[@]}"; do
                if wait "$pid"; then
                    ((success_count++))
                else
                    ((failure_count++))
                fi
            done
            
            print_status "info" "Completed batch $((batch/concurrent_requests + 1))"
        done
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo ""
        echo "Results:"
        echo "========"
        echo "Total Duration: ${duration}s"
        echo "Successful Requests: $success_count"
        echo "Failed Requests: $failure_count"
        echo "Success Rate: $(( success_count * 100 / total_requests ))%"
        echo "Requests per Second: $(( total_requests / duration ))"
        echo "End Time: $(date)"
        
        if [ $failure_count -eq 0 ]; then
            print_status "success" "Load test completed successfully"
            log_to_file "LOAD_TEST_SUCCESS: $success_count/$total_requests successful"
        else
            print_status "warning" "Load test completed with $failure_count failures"
            log_to_file "LOAD_TEST_PARTIAL: $success_count/$total_requests successful, $failure_count failed"
        fi
        
    } | tee "$load_test_log"
}

# Function to backup production data
backup_data() {
    print_status "info" "Creating production data backup..."
    
    mkdir -p "$BACKUP_DIR"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/production_backup_$timestamp.json"
    
    # Collect data from various endpoints
    {
        echo "{"
        echo "  \"backup_timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\","
        echo "  \"api_base\": \"$API_BASE\","
        
        # Job statistics
        echo "  \"job_stats\": $(curl -s "$API_BASE/jobs/stats/summary" 2>/dev/null || echo 'null'),"
        
        # Analytics data
        echo "  \"analytics_overview\": $(curl -s "$API_BASE/analytics/jobs/overview" 2>/dev/null || echo 'null'),"
        echo "  \"analytics_by_source\": $(curl -s "$API_BASE/analytics/jobs/by-source" 2>/dev/null || echo 'null'),"
        echo "  \"analytics_by_company\": $(curl -s "$API_BASE/analytics/jobs/by-company" 2>/dev/null || echo 'null'),"
        echo "  \"popular_keywords\": $(curl -s "$API_BASE/analytics/jobs/keywords" 2>/dev/null || echo 'null'),"
        
        # System health
        echo "  \"health_status\": $(curl -s "$API_BASE/health" 2>/dev/null || echo 'null'),"
        echo "  \"scraper_status\": $(curl -s "$API_BASE/health/status/scraper" 2>/dev/null || echo 'null')"
        
        echo "}"
    } > "$backup_file"
    
    # Compress the backup
    gzip "$backup_file"
    local compressed_backup="${backup_file}.gz"
    
    print_status "success" "Backup created: $compressed_backup"
    log_to_file "BACKUP_CREATED: $compressed_backup"
    
    # Clean up old backups (keep last 30 days)
    find "$BACKUP_DIR" -name "production_backup_*.json.gz" -mtime +30 -delete 2>/dev/null || true
    
    print_status "info" "Old backups cleaned up (kept last 30 days)"
}

# Function to generate production report
generate_report() {
    print_status "info" "Generating production status report..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="$LOGS_DIR/production_report_$timestamp.html"
    
    mkdir -p "$LOGS_DIR"
    
    # Create HTML report
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>BirJob Production Status Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; padding: 20px; background: #f5f5f5; 
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .section { padding: 25px; border-bottom: 1px solid #eee; }
        .section:last-child { border-bottom: none; }
        .section h2 { margin-top: 0; color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .status-card { background: #f8f9fa; border-radius: 6px; padding: 20px; border-left: 4px solid #28a745; }
        .status-card.warning { border-left-color: #ffc107; }
        .status-card.error { border-left-color: #dc3545; }
        .status-card h3 { margin: 0 0 10px 0; color: #333; }
        .status-card p { margin: 5px 0; color: #666; }
        .metric { background: #e9ecef; border-radius: 4px; padding: 15px; margin: 10px 0; }
        .metric strong { color: #495057; }
        pre { background: #f8f9fa; border-radius: 4px; padding: 15px; overflow-x: auto; border: 1px solid #dee2e6; }
        .timestamp { color: #6c757d; font-size: 0.9em; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 BirJob Production Status</h1>
            <p>Generated on $(date '+%Y-%m-%d at %H:%M:%S %Z')</p>
        </div>
EOF

    # Add health status section
    echo '        <div class="section">' >> "$report_file"
    echo '            <h2>🏥 System Health</h2>' >> "$report_file"
    
    local health_response=$(curl -s "$API_BASE/health" 2>/dev/null || echo '{"status": "unreachable"}')
    echo "            <pre>$health_response</pre>" >> "$report_file"
    
    # Add metrics section
    echo '        </div>' >> "$report_file"
    echo '        <div class="section">' >> "$report_file"
    echo '            <h2>📊 Current Metrics</h2>' >> "$report_file"
    
    local job_stats=$(curl -s "$API_BASE/jobs/stats/summary" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "            <div class=\"metric\">" >> "$report_file"
        echo "                <strong>Job Statistics:</strong>" >> "$report_file"
        echo "                <pre>$job_stats</pre>" >> "$report_file"
        echo "            </div>" >> "$report_file"
    fi
    
    local analytics=$(curl -s "$API_BASE/analytics/jobs/overview" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "            <div class=\"metric\">" >> "$report_file"
        echo "                <strong>Analytics Overview:</strong>" >> "$report_file"
        echo "                <pre>$analytics</pre>" >> "$report_file"
        echo "            </div>" >> "$report_file"
    fi
    
    # Add recent logs section
    echo '        </div>' >> "$report_file"
    echo '        <div class="section">' >> "$report_file"
    echo '            <h2>📋 Recent Activity</h2>' >> "$report_file"
    
    local today_log="$LOGS_DIR/production_$(date +%Y%m%d).log"
    if [ -f "$today_log" ]; then
        echo "            <pre>" >> "$report_file"
        tail -n 20 "$today_log" >> "$report_file"
        echo "            </pre>" >> "$report_file"
    else
        echo "            <p>No recent activity logs found.</p>" >> "$report_file"
    fi
    
    # Close HTML
    cat >> "$report_file" << EOF
        </div>
        <div class="footer">
            <p>BirJob Backend Production Monitoring System</p>
            <p class="timestamp">Report generated at $(date)</p>
        </div>
    </div>
</body>
</html>
EOF

    print_status "success" "Production report generated: $report_file"
    
    # Also create a simple text summary
    local summary_file="$LOGS_DIR/production_summary_$timestamp.txt"
    {
        echo "BirJob Production Summary - $(date)"
        echo "=================================="
        echo ""
        echo "API Base URL: $API_BASE"
        echo ""
        
        # Quick health check
        if check_health > /dev/null 2>&1; then
            echo "✅ Health Check: PASSED"
        else
            echo "❌ Health Check: FAILED"
        fi
        
        # Quick database check
        if check_database > /dev/null 2>&1; then
            echo "✅ Database Check: PASSED"
        else
            echo "❌ Database Check: FAILED"
        fi
        
        echo ""
        echo "Full report available at: $report_file"
        
    } > "$summary_file"
    
    print_status "info" "Summary report: $summary_file"
    log_to_file "REPORT_GENERATED: $report_file"
}

# Function to show help
show_help() {
    echo "BirJob Backend Production Manager"
    echo ""
    echo "Usage:"
    echo "  $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  health                 Check production server health"
    echo "  test                   Run comprehensive production tests"
    echo "  monitor                Collect and display production metrics"
    echo "  database               Check database connectivity"
    echo "  dependencies           Check external dependencies"
    echo "  load-test [conc] [tot] Run load test (default: 10 concurrent, 100 total)"
    echo "  backup                 Create production data backup"
    echo "  report                 Generate comprehensive status report"
    echo "  watch                  Continuous monitoring (every 5 minutes)"
    echo "  logs [lines]           Show recent production logs"
    echo "  clean                  Clean up old logs and backups"
    echo ""
    echo "Examples:"
    echo "  $0 health              # Check if production is healthy"
    echo "  $0 test                # Run full test suite"
    echo "  $0 load-test 20 200    # Load test with 20 concurrent, 200 total requests"
    echo "  $0 watch               # Start continuous monitoring"
}

# Function for continuous monitoring
continuous_monitoring() {
    print_status "info" "Starting continuous production monitoring (Ctrl+C to stop)"
    
    local iteration=1
    while true; do
        print_status "info" "Monitoring iteration #$iteration ($(date))"
        
        # Quick health check
        if check_health; then
            monitor_metrics
        else
            print_status "critical" "Health check failed in monitoring iteration #$iteration"
        fi
        
        print_status "info" "Waiting 5 minutes before next check..."
        sleep 300  # 5 minutes
        
        ((iteration++))
    done
}

# Function to clean up old files
clean_up() {
    print_status "info" "Cleaning up old logs and backups..."
    
    # Clean old logs (keep last 7 days)
    if [ -d "$LOGS_DIR" ]; then
        find "$LOGS_DIR" -name "*.log" -mtime +7 -delete 2>/dev/null || true
        find "$LOGS_DIR" -name "*.json" -mtime +7 -delete 2>/dev/null || true
        print_status "success" "Old logs cleaned (kept last 7 days)"
    fi
    
    # Clean old backups (keep last 30 days)
    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete 2>/dev/null || true
        print_status "success" "Old backups cleaned (kept last 30 days)"
    fi
    
    # Clean old monitoring data (keep last 14 days)
    if [ -d "$MONITORING_DIR" ]; then
        find "$MONITORING_DIR" -name "*.json" -mtime +14 -delete 2>/dev/null || true
        find "$MONITORING_DIR" -name "*.log" -mtime +14 -delete 2>/dev/null || true
        print_status "success" "Old monitoring data cleaned (kept last 14 days)"
    fi
    
    log_to_file "CLEANUP_COMPLETED: Old files removed"
}

# Function to show recent logs
show_logs() {
    local lines=${1:-50}
    local today_log="$LOGS_DIR/production_$(date +%Y%m%d).log"
    
    if [ -f "$today_log" ]; then
        print_status "info" "Showing last $lines lines from today's production log:"
        echo -e "${CYAN}===========================================${NC}"
        tail -n "$lines" "$today_log"
        echo -e "${CYAN}===========================================${NC}"
    else
        print_status "warning" "No production log found for today"
        print_status "info" "Available logs:"
        ls -la "$LOGS_DIR"/*.log 2>/dev/null || print_status "info" "No logs found"
    fi
}

# Main script logic
main() {
    case "${1:-}" in
        "health")
            check_health
            ;;
        "test")
            run_production_tests
            ;;
        "monitor")
            monitor_metrics
            ;;
        "database")
            check_database
            ;;
        "dependencies")
            check_dependencies
            ;;
        "load-test")
            run_load_test "${2:-10}" "${3:-100}"
            ;;
        "backup")
            backup_data
            ;;
        "report")
            generate_report
            ;;
        "watch")
            continuous_monitoring
            ;;
        "logs")
            show_logs "${2:-50}"
            ;;
        "clean")
            clean_up
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            print_status "error" "Unknown command: $1"
            print_status "info" "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap for cleanup on exit
cleanup_on_exit() {
    if [ "$?" -eq 130 ]; then  # SIGINT
        print_status "info" "Monitoring interrupted by user"
    fi
}

trap cleanup_on_exit EXIT

# Run main function with all arguments
main "$@"