#!/bin/bash
# Development Server Runner for BirJob Backend
# Provides easy development environment setup and server management

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
LOGS_DIR="$SCRIPT_DIR/logs"
PID_FILE="$SCRIPT_DIR/dev_server.pid"
DEV_PORT=${DEV_PORT:-8000}
DEV_HOST=${DEV_HOST:-127.0.0.1}

echo -e "${CYAN}🚀 BirJob Backend Development Runner${NC}"
echo -e "${CYAN}====================================${NC}"

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

# Function to check if server is running
is_server_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Function to setup virtual environment
setup_venv() {
    print_status "info" "Setting up virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        print_status "info" "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    print_status "info" "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    print_status "info" "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install pytest pytest-asyncio httpx black flake8 isort
    
    print_status "success" "Virtual environment ready"
}

# Function to check environment variables
check_environment() {
    print_status "info" "Checking environment configuration..."
    
    local env_file="$SCRIPT_DIR/.env"
    if [ ! -f "$env_file" ]; then
        print_status "warning" ".env file not found, creating template..."
        cat > "$env_file" << EOF
# Development Environment Variables
DATABASE_URL=postgresql+asyncpg://user:password@localhost/birjob_dev
REDIS_URL=redis://localhost:6379
APNS_PRIVATE_KEY=your_apns_private_key_here
APNS_KEY_ID=your_key_id_here
APNS_TEAM_ID=your_team_id_here
APNS_BUNDLE_ID=com.yourcompany.birjob
APNS_SANDBOX=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOF
        print_status "info" "Template .env file created. Please update with your values."
    fi
    
    print_status "success" "Environment check completed"
}

# Function to start development server
start_server() {
    if is_server_running; then
        print_status "warning" "Development server is already running"
        return 0
    fi
    
    print_status "info" "Starting development server..."
    
    # Create logs directory
    mkdir -p "$LOGS_DIR"
    
    # Activate virtual environment
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Start server in background
    nohup uvicorn application:app \
        --host "$DEV_HOST" \
        --port "$DEV_PORT" \
        --reload \
        --log-level debug \
        --access-log \
        > "$LOGS_DIR/dev_server.log" 2>&1 &
    
    echo $! > "$PID_FILE"
    
    # Wait a moment and check if server started
    sleep 3
    
    if is_server_running; then
        print_status "success" "Development server started on http://$DEV_HOST:$DEV_PORT"
        print_status "info" "API documentation: http://$DEV_HOST:$DEV_PORT/docs"
        print_status "info" "Logs: $LOGS_DIR/dev_server.log"
        print_status "info" "PID: $(cat "$PID_FILE")"
    else
        print_status "error" "Failed to start development server"
        print_status "info" "Check logs at: $LOGS_DIR/dev_server.log"
        exit 1
    fi
}

# Function to stop development server
stop_server() {
    if is_server_running; then
        local pid=$(cat "$PID_FILE")
        print_status "info" "Stopping development server (PID: $pid)..."
        
        kill "$pid"
        
        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_status "warning" "Force killing server..."
            kill -9 "$pid"
        fi
        
        rm -f "$PID_FILE"
        print_status "success" "Development server stopped"
    else
        print_status "info" "Development server is not running"
    fi
}

# Function to restart development server
restart_server() {
    stop_server
    sleep 2
    start_server
}

# Function to show server status
show_status() {
    print_status "info" "Development server status:"
    
    if is_server_running; then
        local pid=$(cat "$PID_FILE")
        print_status "success" "Server is running (PID: $pid)"
        print_status "info" "URL: http://$DEV_HOST:$DEV_PORT"
        print_status "info" "API Docs: http://$DEV_HOST:$DEV_PORT/docs"
        
        # Show memory usage if possible
        if command -v ps &> /dev/null; then
            local mem_usage=$(ps -o pid,rss,pcpu -p "$pid" | tail -n 1)
            print_status "info" "Memory usage: $mem_usage"
        fi
    else
        print_status "warning" "Server is not running"
    fi
}

# Function to show logs
show_logs() {
    local lines=${1:-50}
    local log_file="$LOGS_DIR/dev_server.log"
    
    if [ -f "$log_file" ]; then
        print_status "info" "Showing last $lines lines from development server logs:"
        echo -e "${CYAN}===========================================${NC}"
        tail -n "$lines" "$log_file"
        echo -e "${CYAN}===========================================${NC}"
    else
        print_status "warning" "Log file not found: $log_file"
    fi
}

# Function to follow logs
follow_logs() {
    local log_file="$LOGS_DIR/dev_server.log"
    
    if [ -f "$log_file" ]; then
        print_status "info" "Following development server logs (Ctrl+C to stop):"
        tail -f "$log_file"
    else
        print_status "warning" "Log file not found: $log_file"
        print_status "info" "Start the server first to generate logs"
    fi
}

# Function to run development tests
run_dev_tests() {
    print_status "info" "Running development tests..."
    
    # Activate virtual environment
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Check if server is running
    if ! is_server_running; then
        print_status "info" "Starting server for tests..."
        start_server
        sleep 5  # Give server time to start
        local started_for_tests=true
    fi
    
    # Run tests against development server
    python3 -c "
import httpx
import asyncio

async def test_dev_server():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get('http://$DEV_HOST:$DEV_PORT/api/v1/health')
            if response.status_code == 200:
                print('✅ Development server is responding')
                print(f'Response: {response.json()}')
                return True
            else:
                print(f'❌ Server responded with status: {response.status_code}')
                return False
        except Exception as e:
            print(f'❌ Failed to connect to server: {e}')
            return False

success = asyncio.run(test_dev_server())
exit(0 if success else 1)
"
    
    local test_result=$?
    
    # Stop server if we started it
    if [ "${started_for_tests:-}" = "true" ]; then
        stop_server
    fi
    
    if [ $test_result -eq 0 ]; then
        print_status "success" "Development tests passed"
    else
        print_status "error" "Development tests failed"
        exit 1
    fi
}

# Function to format code
format_code() {
    print_status "info" "Formatting code with black and isort..."
    
    # Activate virtual environment
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Format with black
    if command -v black &> /dev/null; then
        black --line-length 88 --target-version py311 .
        print_status "success" "Code formatted with black"
    else
        print_status "warning" "black not installed, skipping formatting"
    fi
    
    # Sort imports with isort
    if command -v isort &> /dev/null; then
        isort --profile black .
        print_status "success" "Imports sorted with isort"
    else
        print_status "warning" "isort not installed, skipping import sorting"
    fi
}

# Function to lint code
lint_code() {
    print_status "info" "Linting code with flake8..."
    
    # Activate virtual environment
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    if command -v flake8 &> /dev/null; then
        flake8 --max-line-length=88 --extend-ignore=E203,W503 .
        print_status "success" "Code linting completed"
    else
        print_status "warning" "flake8 not installed, skipping linting"
    fi
}

# Function to show help
show_help() {
    echo "BirJob Backend Development Runner"
    echo ""
    echo "Usage:"
    echo "  $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  setup          Setup development environment"
    echo "  start          Start development server"
    echo "  stop           Stop development server"
    echo "  restart        Restart development server"
    echo "  status         Show server status"
    echo "  logs [lines]   Show server logs (default: 50 lines)"
    echo "  follow         Follow server logs in real-time"
    echo "  test           Run development tests"
    echo "  format         Format code with black and isort"
    echo "  lint           Lint code with flake8"
    echo "  clean          Clean up logs and temporary files"
    echo ""
    echo "Environment Variables:"
    echo "  DEV_HOST       Development server host (default: 127.0.0.1)"
    echo "  DEV_PORT       Development server port (default: 8000)"
    echo ""
    echo "Examples:"
    echo "  $0 setup       # Setup development environment"
    echo "  $0 start       # Start development server"
    echo "  $0 logs 100    # Show last 100 log lines"
    echo "  DEV_PORT=8080 $0 start  # Start on port 8080"
}

# Function to clean up
clean_up() {
    print_status "info" "Cleaning up development environment..."
    
    # Stop server if running
    stop_server
    
    # Remove logs
    if [ -d "$LOGS_DIR" ]; then
        rm -rf "$LOGS_DIR"
        print_status "info" "Logs directory removed"
    fi
    
    # Remove PID file
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
        print_status "info" "PID file removed"
    fi
    
    print_status "success" "Cleanup completed"
}

# Main script logic
main() {
    case "${1:-}" in
        "setup")
            setup_venv
            check_environment
            ;;
        "start")
            start_server
            ;;
        "stop")
            stop_server
            ;;
        "restart")
            restart_server
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "${2:-50}"
            ;;
        "follow")
            follow_logs
            ;;
        "test")
            run_dev_tests
            ;;
        "format")
            format_code
            ;;
        "lint")
            lint_code
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
    # Don't stop server on normal exit, only on interrupt
    if [ "$?" -eq 130 ]; then  # SIGINT
        print_status "info" "Interrupted, stopping server..."
        stop_server
    fi
}

trap cleanup_on_exit EXIT

# Run main function with all arguments
main "$@"