#!/bin/bash

# =============================================================================
# BirJob Mobile Backend - Deployment Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
SKIP_TESTS=false
SKIP_BUILD=false
BACKUP_DB=true
DEPLOY_METHOD="docker"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}  BirJob Mobile Backend Deploy  ${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# =============================================================================
# Validation Functions
# =============================================================================

check_requirements() {
    print_step "Checking requirements..."
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    # Check Node.js version
    NODE_VERSION=$(node --version | cut -d 'v' -f 2 | cut -d '.' -f 1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        exit 1
    fi
    
    # Check if Docker is installed (if using Docker deployment)
    if [ "$DEPLOY_METHOD" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            print_error "docker-compose is not installed"
            exit 1
        fi
    fi
    
    print_success "All requirements satisfied"
}

check_environment() {
    print_step "Checking environment configuration..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        echo "Please copy .env.example to .env and configure it"
        exit 1
    fi
    
    # Check critical environment variables
    source .env
    
    REQUIRED_VARS=(
        "DATABASE_URL"
        "JWT_SECRET"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            print_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    print_success "Environment configuration is valid"
}

# =============================================================================
# Database Functions
# =============================================================================

backup_database() {
    if [ "$BACKUP_DB" = true ]; then
        print_step "Creating database backup..."
        
        BACKUP_DIR="backups"
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        mkdir -p "$BACKUP_DIR"
        
        # Extract database connection details from DATABASE_URL
        DB_URL="${DATABASE_URL}"
        
        if [[ $DB_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASS="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"
            
            export PGPASSWORD="$DB_PASS"
            
            if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
                print_success "Database backup created: $BACKUP_FILE"
            else
                print_warning "Database backup failed, continuing..."
            fi
        else
            print_warning "Could not parse DATABASE_URL for backup"
        fi
    fi
}

migrate_database() {
    print_step "Running database migrations..."
    
    if [ "$DEPLOY_METHOD" = "docker" ]; then
        docker-compose exec -T api npx prisma db push
    else
        npx prisma db push
    fi
    
    print_success "Database migrations completed"
}

# =============================================================================
# Build Functions
# =============================================================================

install_dependencies() {
    print_step "Installing dependencies..."
    
    npm ci --only=production
    
    print_success "Dependencies installed"
}

generate_prisma_client() {
    print_step "Generating Prisma client..."
    
    npx prisma generate
    
    print_success "Prisma client generated"
}

run_tests() {
    if [ "$SKIP_TESTS" = false ]; then
        print_step "Running tests..."
        
        npm test
        
        print_success "All tests passed"
    else
        print_info "Skipping tests"
    fi
}

build_application() {
    if [ "$SKIP_BUILD" = false ]; then
        print_step "Building application..."
        
        # Add any build steps here if needed
        # npm run build
        
        print_success "Application built"
    else
        print_info "Skipping build"
    fi
}

# =============================================================================
# Deployment Functions
# =============================================================================

deploy_docker() {
    print_step "Deploying with Docker..."
    
    # Stop existing containers
    print_info "Stopping existing containers..."
    docker-compose down
    
    # Build new images
    print_info "Building Docker images..."
    docker-compose build --no-cache
    
    # Start services
    print_info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be ready..."
    sleep 30
    
    # Check health
    if curl -f http://localhost:${PORT:-3000}/api/health > /dev/null 2>&1; then
        print_success "Docker deployment completed successfully"
    else
        print_error "Health check failed"
        docker-compose logs api
        exit 1
    fi
}

deploy_pm2() {
    print_step "Deploying with PM2..."
    
    # Install PM2 if not installed
    if ! command -v pm2 &> /dev/null; then
        print_info "Installing PM2..."
        npm install -g pm2
    fi
    
    # Stop existing processes
    print_info "Stopping existing PM2 processes..."
    pm2 delete birjob-backend || true
    
    # Start new process
    print_info "Starting application with PM2..."
    pm2 start server.js --name "birjob-backend" --env production
    
    # Save PM2 configuration
    pm2 save
    pm2 startup
    
    print_success "PM2 deployment completed"
}

deploy_systemd() {
    print_step "Deploying with systemd..."
    
    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/birjob-backend.service"
    
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=BirJob Mobile Backend
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=NODE_ENV=production
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and start service
    sudo systemctl daemon-reload
    sudo systemctl enable birjob-backend
    sudo systemctl restart birjob-backend
    
    # Check status
    if sudo systemctl is-active --quiet birjob-backend; then
        print_success "systemd deployment completed"
    else
        print_error "Service failed to start"
        sudo systemctl status birjob-backend
        exit 1
    fi
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_old_backups() {
    print_step "Cleaning up old backups..."
    
    if [ -d "backups" ]; then
        # Keep only last 10 backups
        ls -t backups/backup_*.sql | tail -n +11 | xargs rm -f
        print_success "Old backups cleaned up"
    fi
}

cleanup_logs() {
    print_step "Rotating logs..."
    
    if [ -d "logs" ]; then
        # Compress logs older than 7 days
        find logs -name "*.log" -mtime +7 -exec gzip {} \;
        
        # Remove compressed logs older than 30 days
        find logs -name "*.log.gz" -mtime +30 -delete
        
        print_success "Log rotation completed"
    fi
}

# =============================================================================
# Health Check Functions
# =============================================================================

health_check() {
    print_step "Performing post-deployment health check..."
    
    # Wait a bit for the service to start
    sleep 10
    
    # Check basic health endpoint
    if curl -f http://localhost:${PORT:-3000}/api/health > /dev/null 2>&1; then
        print_success "✅ Basic health check passed"
    else
        print_error "❌ Basic health check failed"
        return 1
    fi
    
    # Check detailed health endpoint
    if curl -f http://localhost:${PORT:-3000}/api/health/detailed > /dev/null 2>&1; then
        print_success "✅ Detailed health check passed"
    else
        print_warning "⚠️ Detailed health check failed"
    fi
    
    # Test database connectivity
    HEALTH_RESPONSE=$(curl -s http://localhost:${PORT:-3000}/api/health/database)
    if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
        print_success "✅ Database connection healthy"
    else
        print_error "❌ Database connection failed"
        return 1
    fi
    
    # Test Redis connectivity
    REDIS_RESPONSE=$(curl -s http://localhost:${PORT:-3000}/api/health/redis)
    if echo "$REDIS_RESPONSE" | grep -q '"status":"healthy"'; then
        print_success "✅ Redis connection healthy"
    else
        print_warning "⚠️ Redis connection failed"
    fi
    
    print_success "Health checks completed"
}

# =============================================================================
# Main Deployment Function
# =============================================================================

main() {
    print_header
    
    print_info "Starting deployment for environment: $ENVIRONMENT"
    print_info "Deployment method: $DEPLOY_METHOD"
    
    # Pre-deployment checks
    check_requirements
    check_environment
    
    # Create backup
    backup_database
    
    # Build and test
    install_dependencies
    generate_prisma_client
    run_tests
    build_application
    
    # Deploy based on method
    case $DEPLOY_METHOD in
        "docker")
            deploy_docker
            ;;
        "pm2")
            deploy_pm2
            ;;
        "systemd")
            deploy_systemd
            ;;
        *)
            print_error "Unknown deployment method: $DEPLOY_METHOD"
            exit 1
            ;;
    esac
    
    # Post-deployment tasks
    migrate_database
    health_check
    cleanup_old_backups
    cleanup_logs
    
    print_success "🎉 Deployment completed successfully!"
    print_info "API is running at: http://localhost:${PORT:-3000}"
    print_info "Health check: http://localhost:${PORT:-3000}/api/health"
}

# =============================================================================
# Command Line Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -m|--method)
            DEPLOY_METHOD="$2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --no-backup)
            BACKUP_DB=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -e, --environment ENV    Set environment (default: production)"
            echo "  -m, --method METHOD      Deployment method: docker|pm2|systemd (default: docker)"
            echo "  --skip-tests            Skip running tests"
            echo "  --skip-build            Skip build step"
            echo "  --no-backup             Skip database backup"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                  # Deploy with defaults"
            echo "  $0 -m pm2                         # Deploy with PM2"
            echo "  $0 -e staging --skip-tests        # Deploy to staging without tests"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Execute Main Function
# =============================================================================

main