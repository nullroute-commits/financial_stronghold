#!/bin/bash
# Service-Specific Deployment Validation
# Tests individual services and their dependencies in isolation
# Last updated: 2025-09-01 by copilot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICE_LOG="$PROJECT_ROOT/service-validation.log"

# Initialize log
echo "Service Validation Started: $(date)" > "$SERVICE_LOG"

# Logging functions
log() {
    echo -e "$1" | tee -a "$SERVICE_LOG"
}

log_section() {
    echo "" | tee -a "$SERVICE_LOG"
    log "${BLUE}=== $1 ===${NC}"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

# Service validation functions
validate_database_service() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Database Service for $env"
    
    # Start only database service
    log "Starting database service..."
    if docker compose -f "$compose_file" up -d db 2>&1 | tee -a "$SERVICE_LOG"; then
        log_success "Database service started"
    else
        log_error "Failed to start database service"
        return 1
    fi
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    local retries=0
    local max_retries=30
    
    while [[ $retries -lt $max_retries ]]; do
        if docker compose -f "$compose_file" exec -T db pg_isready -U postgres >/dev/null 2>&1; then
            log_success "Database is ready"
            break
        else
            log "Database not ready yet (attempt $((retries + 1))/$max_retries)..."
            sleep 2
            ((retries++))
        fi
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "Database failed to become ready"
        docker compose -f "$compose_file" logs db --tail=10 | tee -a "$SERVICE_LOG"
        return 1
    fi
    
    # Test database connection
    log "Testing database connection..."
    if docker compose -f "$compose_file" exec -T db psql -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
        log_success "Database connection test passed"
    else
        log_error "Database connection test failed"
        return 1
    fi
    
    return 0
}

validate_cache_service() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Cache Service for $env"
    
    # Start only cache service
    log "Starting cache service..."
    if docker compose -f "$compose_file" up -d memcached 2>&1 | tee -a "$SERVICE_LOG"; then
        log_success "Cache service started"
    else
        log_error "Failed to start cache service"
        return 1
    fi
    
    # Wait for cache to be ready
    log "Waiting for cache to be ready..."
    local retries=0
    local max_retries=20
    
    while [[ $retries -lt $max_retries ]]; do
        if echo "stats" | nc -w 1 localhost 11211 >/dev/null 2>&1; then
            log_success "Cache is ready"
            break
        else
            log "Cache not ready yet (attempt $((retries + 1))/$max_retries)..."
            sleep 1
            ((retries++))
        fi
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "Cache failed to become ready"
        docker compose -f "$compose_file" logs memcached --tail=10 | tee -a "$SERVICE_LOG"
        return 1
    fi
    
    # Test cache functionality
    log "Testing cache functionality..."
    if echo -e "set test_key 0 10 5\r\nhello\r\nget test_key\r\nquit\r\n" | nc localhost 11211 | grep -q "hello"; then
        log_success "Cache functionality test passed"
    else
        log_error "Cache functionality test failed"
        return 1
    fi
    
    return 0
}

validate_queue_service() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Queue Service for $env"
    
    # Start only queue service
    log "Starting queue service..."
    if docker compose -f "$compose_file" up -d rabbitmq 2>&1 | tee -a "$SERVICE_LOG"; then
        log_success "Queue service started"
    else
        log_error "Failed to start queue service"
        return 1
    fi
    
    # Wait for queue to be ready
    log "Waiting for queue to be ready..."
    local retries=0
    local max_retries=30
    
    while [[ $retries -lt $max_retries ]]; do
        if docker compose -f "$compose_file" exec -T rabbitmq rabbitmqctl status >/dev/null 2>&1; then
            log_success "Queue is ready"
            break
        else
            log "Queue not ready yet (attempt $((retries + 1))/$max_retries)..."
            sleep 2
            ((retries++))
        fi
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "Queue failed to become ready"
        docker compose -f "$compose_file" logs rabbitmq --tail=10 | tee -a "$SERVICE_LOG"
        return 1
    fi
    
    return 0
}

validate_web_service() {
    local env=$1
    local port=$2
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Web Service for $env"
    
    # Start web service with dependencies
    log "Starting web service with dependencies..."
    if docker compose -f "$compose_file" up -d web 2>&1 | tee -a "$SERVICE_LOG"; then
        log_success "Web service started"
    else
        log_error "Failed to start web service"
        return 1
    fi
    
    # Wait for web service to be ready
    log "Waiting for web service to be ready..."
    local retries=0
    local max_retries=60
    
    while [[ $retries -lt $max_retries ]]; do
        if nc -z localhost "$port" >/dev/null 2>&1; then
            log_success "Web service is listening on port $port"
            break
        else
            log "Web service not ready yet (attempt $((retries + 1))/$max_retries)..."
            sleep 2
            ((retries++))
        fi
    done
    
    if [[ $retries -eq $max_retries ]]; then
        log_error "Web service failed to become ready"
        docker compose -f "$compose_file" logs web --tail=20 | tee -a "$SERVICE_LOG"
        return 1
    fi
    
    # Test health endpoint
    log "Testing health endpoint..."
    sleep 5  # Give extra time for Django initialization
    
    local health_retries=0
    local max_health_retries=10
    
    while [[ $health_retries -lt $max_health_retries ]]; do
        if curl -f -s "http://localhost:$port/health/" >/dev/null 2>&1; then
            log_success "Health endpoint is responding"
            local health_response
            health_response=$(curl -s "http://localhost:$port/health/")
            log "Health response: $health_response"
            break
        else
            log "Health endpoint not ready yet (attempt $((health_retries + 1))/$max_health_retries)..."
            sleep 3
            ((health_retries++))
        fi
    done
    
    if [[ $health_retries -eq $max_health_retries ]]; then
        log_error "Health endpoint failed to respond"
        return 1
    fi
    
    return 0
}

# Service dependency testing
test_service_dependencies() {
    local env=$1
    local port=$2
    local compose_file="docker-compose.$env.yml"
    
    log_section "Testing Service Dependencies for $env"
    
    # Test database connectivity from web service
    log "Testing database connectivity from web service..."
    if docker compose -f "$compose_file" exec -T web python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.$env')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('Database connection successful')
" 2>&1 | tee -a "$SERVICE_LOG"; then
        log_success "Database connectivity test passed"
    else
        log_error "Database connectivity test failed"
        return 1
    fi
    
    # Test cache connectivity from web service
    log "Testing cache connectivity from web service..."
    if docker compose -f "$compose_file" exec -T web python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.$env')
django.setup()
from django.core.cache import cache
cache.set('test_key', 'test_value', 10)
result = cache.get('test_key')
if result == 'test_value':
    print('Cache connection successful')
else:
    raise Exception('Cache test failed')
" 2>&1 | tee -a "$SERVICE_LOG"; then
        log_success "Cache connectivity test passed"
    else
        log_error "Cache connectivity test failed"
        return 1
    fi
    
    return 0
}

# Cleanup function
cleanup() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Cleaning up $env services"
    docker compose -f "$compose_file" down -v --remove-orphans >/dev/null 2>&1 || true
    log_success "Cleanup completed for $env"
}

# Main validation function
validate_environment_services() {
    local env=$1
    local port=$2
    
    log_section "Service Validation for $env Environment"
    
    local all_services_ok=true
    
    # Validate individual services
    if ! validate_database_service "$env"; then
        all_services_ok=false
    fi
    
    if ! validate_cache_service "$env"; then
        all_services_ok=false
    fi
    
    if ! validate_queue_service "$env"; then
        all_services_ok=false
    fi
    
    if ! validate_web_service "$env" "$port"; then
        all_services_ok=false
    fi
    
    # Test service dependencies
    if [[ "$all_services_ok" == true ]]; then
        if ! test_service_dependencies "$env" "$port"; then
            all_services_ok=false
        fi
    fi
    
    # Cleanup
    cleanup "$env"
    
    if [[ "$all_services_ok" == true ]]; then
        log_success "All services validated successfully for $env"
        return 0
    else
        log_error "Some services failed validation for $env"
        return 1
    fi
}

# Main execution
main() {
    local env="${1:-development}"
    
    case "$env" in
        "development"|"dev")
            validate_environment_services "development" "8000"
            ;;
        "testing"|"test")
            validate_environment_services "testing" "8001"
            ;;
        "staging")
            validate_environment_services "staging" "8003"
            ;;
        "production"|"prod")
            validate_environment_services "production" "8002"
            ;;
        "all")
            local overall_success=true
            
            for env_config in "development:8000" "testing:8001" "staging:8003" "production:8002"; do
                local env_name="${env_config%:*}"
                local env_port="${env_config#*:}"
                
                if ! validate_environment_services "$env_name" "$env_port"; then
                    overall_success=false
                fi
            done
            
            if [[ "$overall_success" == true ]]; then
                log_success "All environments validated successfully"
                exit 0
            else
                log_error "Some environments failed validation"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 [environment]"
            echo ""
            echo "Environments:"
            echo "  development  - Validate development environment"
            echo "  testing      - Validate testing environment"
            echo "  staging      - Validate staging environment"
            echo "  production   - Validate production environment"
            echo "  all          - Validate all environments"
            exit 1
            ;;
    esac
}

# Check dependencies
if ! command -v nc >/dev/null 2>&1; then
    log_error "netcat is required but not installed"
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    log_error "curl is required but not installed"
    exit 1
fi

# Execute main function
main "$@"