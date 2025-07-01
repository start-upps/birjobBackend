#!/bin/bash
# Test Runner Script for BirJob Backend API
# Runs comprehensive API tests with different configurations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/test_logs"
RESULTS_DIR="$SCRIPT_DIR/test_results"

echo -e "${BLUE}🚀 BirJob API Test Runner${NC}"
echo -e "${BLUE}==============================${NC}"

# Create directories
mkdir -p "$LOGS_DIR"
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "info" "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_status "error" "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check httpx package
    if ! python3 -c "import httpx" 2>/dev/null; then
        print_status "warning" "httpx package not found. Installing..."
        pip3 install httpx
    fi
    
    # Check if test file exists
    if [ ! -f "$SCRIPT_DIR/test_api_comprehensive.py" ]; then
        print_status "error" "test_api_comprehensive.py not found"
        exit 1
    fi
    
    print_status "success" "Prerequisites check passed"
}

# Function to run quick health check
quick_health_check() {
    print_status "info" "Running quick health check..."
    
    local health_response=$(curl -s -f "https://birjobbackend-ir3e.onrender.com/api/v1/health" || echo "failed")
    
    if [ "$health_response" = "failed" ]; then
        print_status "error" "API health check failed - API may be down"
        exit 1
    fi
    
    print_status "success" "API is responding"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_status "info" "Running comprehensive API tests..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file="$LOGS_DIR/comprehensive_test_$timestamp.log"
    
    # Run the comprehensive test suite
    if python3 "$SCRIPT_DIR/test_api_comprehensive.py" 2>&1 | tee "$log_file"; then
        print_status "success" "Comprehensive tests completed"
        
        # Move results to results directory
        mv test_results_*.json "$RESULTS_DIR/" 2>/dev/null || true
        mv api_test_results_*.json "$RESULTS_DIR/" 2>/dev/null || true
        mv api_test_results_*.csv "$RESULTS_DIR/" 2>/dev/null || true
        
    else
        print_status "error" "Comprehensive tests failed"
        print_status "info" "Check log file: $log_file"
        exit 1
    fi
}

# Function to run specific endpoint tests
run_endpoint_tests() {
    local endpoint=$1
    print_status "info" "Testing specific endpoint: $endpoint"
    
    case $endpoint in
        "health")
            curl -s -f "https://birjobbackend-ir3e.onrender.com/api/v1/health" | jq .
            ;;
        "jobs")
            curl -s -f "https://birjobbackend-ir3e.onrender.com/api/v1/jobs?limit=5" | jq .
            ;;
        "analytics")
            curl -s -f "https://birjobbackend-ir3e.onrender.com/api/v1/analytics/jobs/overview" | jq .
            ;;
        *)
            print_status "error" "Unknown endpoint: $endpoint"
            print_status "info" "Available endpoints: health, jobs, analytics"
            exit 1
            ;;
    esac
}

# Function to run load tests
run_load_tests() {
    print_status "info" "Running load tests..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local log_file="$LOGS_DIR/load_test_$timestamp.log"
    
    # Simple load test with curl
    print_status "info" "Testing with 10 concurrent requests..."
    
    for i in {1..10}; do
        {
            curl -s -f "https://birjobbackend-ir3e.onrender.com/api/v1/health" > /dev/null
            echo "Request $i completed"
        } &
    done
    
    wait
    print_status "success" "Load test completed"
}

# Function to generate test report
generate_report() {
    print_status "info" "Generating test report..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="$RESULTS_DIR/test_report_$timestamp.html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>BirJob API Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #007acc; color: white; padding: 20px; border-radius: 5px; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .info { color: #17a2b8; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 BirJob API Test Report</h1>
        <p>Generated: $(date)</p>
    </div>
    
    <div class="section">
        <h2>📊 Test Summary</h2>
        <p>Test execution completed at $(date)</p>
        <p>API Base URL: https://birjobbackend-ir3e.onrender.com/api/v1</p>
    </div>
    
    <div class="section">
        <h2>📁 Test Files</h2>
        <ul>
EOF

    # Add test files to report
    for file in "$RESULTS_DIR"/*.json; do
        if [ -f "$file" ]; then
            echo "            <li><a href=\"$(basename "$file")\">$(basename "$file")</a></li>" >> "$report_file"
        fi
    done

    cat >> "$report_file" << EOF
        </ul>
    </div>
    
    <div class="section">
        <h2>🔧 Available Commands</h2>
        <pre>
./run_tests.sh                    # Run all tests
./run_tests.sh --endpoint health  # Test specific endpoint
./run_tests.sh --load            # Run load tests
./run_tests.sh --report          # Generate this report
        </pre>
    </div>
</body>
</html>
EOF

    print_status "success" "Report generated: $report_file"
}

# Main script logic
main() {
    case "${1:-}" in
        "--endpoint")
            check_prerequisites
            quick_health_check
            run_endpoint_tests "$2"
            ;;
        "--load")
            check_prerequisites
            quick_health_check
            run_load_tests
            ;;
        "--report")
            generate_report
            ;;
        "--help"|"-h")
            echo "BirJob API Test Runner"
            echo ""
            echo "Usage:"
            echo "  $0                     Run comprehensive tests"
            echo "  $0 --endpoint <name>   Test specific endpoint (health, jobs, analytics)"
            echo "  $0 --load             Run load tests"
            echo "  $0 --report           Generate HTML report"
            echo "  $0 --help             Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                     # Run all tests"
            echo "  $0 --endpoint health   # Test health endpoint"
            echo "  $0 --load             # Run load tests"
            ;;
        "")
            # Default: run comprehensive tests
            check_prerequisites
            quick_health_check
            run_comprehensive_tests
            generate_report
            ;;
        *)
            print_status "error" "Unknown option: $1"
            print_status "info" "Use --help for usage information"
            exit 1
            ;;
    esac
}

# Trap for cleanup
cleanup() {
    print_status "info" "Cleaning up..."
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
}

trap cleanup EXIT

# Run main function with all arguments
main "$@"

print_status "success" "Test runner completed!"
print_status "info" "Logs available in: $LOGS_DIR"
print_status "info" "Results available in: $RESULTS_DIR"