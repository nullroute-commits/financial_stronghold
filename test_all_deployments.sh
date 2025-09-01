#!/bin/bash
# Comprehensive Docker Stack Deployment Test
# Tests deployment for all pipeline stages
# Last updated: 2025-09-01 18:40:00 UTC by copilot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ $1${NC}"
}

# Cleanup function
cleanup() {
    log "Cleaning up all environments..."
    docker compose -f docker-compose.development.yml down --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.testing.yml down --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.staging.yml down --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.production.yml down --remove-orphans 2>/dev/null || true
    docker system prune -f --volumes 2>/dev/null || true
    log_success "Cleanup completed"
}

# Test function for each environment
test_deployment() {
    local env=$1
    local port=$2
    
    log "Testing $env environment deployment..."
    
    # Deploy environment
    if ./ci/deploy.sh $env; then
        log_success "$env deployment completed"
        
        # Test health endpoint
        log "Testing health endpoint for $env environment..."
        sleep 20
        
        if curl -f -s http://localhost:$port/health/ > /dev/null 2>&1; then
            log_success "$env health check passed"
            
            # Get health response
            health_response=$(curl -s http://localhost:$port/health/)
            echo "Health response: $health_response"
            
            return 0
        else
            log_error "$env health check failed"
            return 1
        fi
    else
        log_error "$env deployment failed"
        return 1
    fi
}

# Simplified test without complex dependencies
test_deployment_simple() {
    local env=$1
    local port=$2
    local compose_file="docker-compose.$env.yml"
    
    log "Testing $env environment (simple mode)..."
    
    # Build and start essential services
    log "Building $env environment..."
    if ! docker compose -f $compose_file build web; then
        log_error "Failed to build $env environment"
        return 1
    fi
    
    # Start database first
    log "Starting database for $env..."
    docker compose -f $compose_file up -d db
    sleep 10
    
    # Run migrations
    log "Running migrations for $env..."
    if docker compose -f $compose_file run --rm --no-deps web python manage.py migrate --noinput; then
        log_success "Migrations completed for $env"
    else
        log_warning "Migrations failed for $env, continuing..."
    fi
    
    # Start other services
    log "Starting all services for $env..."
    docker compose -f $compose_file up -d
    sleep 20
    
    # Test health endpoint
    log "Testing health endpoint for $env..."
    local max_attempts=10
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:$port/health/ > /dev/null 2>&1; then
            log_success "$env health check passed on attempt $attempt"
            
            # Get health response
            health_response=$(curl -s http://localhost:$port/health/)
            echo "Health response: $health_response"
            
            # Clean up
            docker compose -f $compose_file down
            return 0
        else
            log_warning "$env health check failed (attempt $attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    log_error "$env health check failed after $max_attempts attempts"
    
    # Show logs for debugging
    log "Showing web service logs for debugging..."
    docker compose -f $compose_file logs web --tail=20
    
    # Clean up
    docker compose -f $compose_file down
    return 1
}

# Main execution
main() {
    log "Starting comprehensive Docker stack deployment tests..."
    
    # Clean up before starting
    cleanup
    
    local results=()
    
    # Test each environment
    environments=(
        "development:8000"
        "testing:8001"
        "staging:8003"
        "production:8002"
    )
    
    for env_config in "${environments[@]}"; do
        env=${env_config%:*}
        port=${env_config#*:}
        
        log "=== Testing $env Environment ==="
        
        if test_deployment_simple $env $port; then
            results+=("$env:PASS")
            log_success "$env environment test completed successfully"
        else
            results+=("$env:FAIL")
            log_error "$env environment test failed"
        fi
        
        # Clean up between tests
        sleep 5
        cleanup
        sleep 5
        
        echo ""
    done
    
    # Summary
    log "=== Test Results Summary ==="
    echo ""
    
    local total=0
    local passed=0
    
    for result in "${results[@]}"; do
        env=${result%:*}
        status=${result#*:}
        ((total++))
        
        if [ "$status" = "PASS" ]; then
            log_success "$env: PASSED"
            ((passed++))
        else
            log_error "$env: FAILED"
        fi
    done
    
    echo ""
    log "Test Results: $passed/$total environments passed"
    
    if [ $passed -eq $total ]; then
        log_success "All environments deployed successfully!"
        exit 0
    else
        log_error "Some environments failed deployment"
        exit 1
    fi
}

# Execute main function
main "$@"