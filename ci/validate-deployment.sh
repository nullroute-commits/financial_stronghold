#!/bin/bash
# Comprehensive deployment validation script
# Deploys and validates each Docker stage to confirm all services, configuration, 
# and codebase are functional and performing as expected
# Last updated: 2025-08-31 by automation

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
VALIDATION_LOG="$PROJECT_ROOT/validation-results.log"
VALIDATION_RESULTS=()

# Logging functions
log() {
    echo -e "$1" | tee -a "$VALIDATION_LOG"
}

log_section() {
    echo "" | tee -a "$VALIDATION_LOG"
    log "${BLUE}=== $1 ===${NC}"
}

log_success() {
    local message="✅ $1"
    log "${GREEN}$message${NC}"
    VALIDATION_RESULTS+=("$message")
}

log_warning() {
    local message="⚠️  $1"
    log "${YELLOW}$message${NC}"
    VALIDATION_RESULTS+=("$message")
}

log_error() {
    local message="❌ $1"
    log "${RED}$message${NC}"
    VALIDATION_RESULTS+=("$message")
}

# Cleanup function
cleanup() {
    log_section "Cleaning up test deployments"
    
    for env in development testing production; do
        if docker compose -f "docker-compose.$env.yml" ps -q >/dev/null 2>&1; then
            log "Stopping $env environment..."
            docker compose -f "docker-compose.$env.yml" down -v --remove-orphans >/dev/null 2>&1 || true
        fi
    done
    
    # Clean up any test containers
    docker container prune -f >/dev/null 2>&1 || true
    docker volume prune -f >/dev/null 2>&1 || true
    
    log_success "Cleanup completed"
}

# Trap cleanup on exit
trap cleanup EXIT

# Validation functions
validate_docker_environment() {
    log_section "Validating Docker Environment"
    
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    if ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not available"
        return 1
    fi
    
    log_success "Docker environment is ready"
    return 0
}

validate_files_exist() {
    local env=$1
    log_section "Validating Files for $env Environment"
    
    local compose_file="docker-compose.$env.yml"
    local env_file="environments/.env.$env.example"
    
    if [[ ! -f "$compose_file" ]]; then
        log_error "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi
    
    log_success "Required files exist for $env environment"
    return 0
}

wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local timeout=${4:-60}
    local interval=${5:-2}
    
    log "Waiting for $service_name at $host:$port (timeout: ${timeout}s)..."
    
    local elapsed=0
    while ! nc -z "$host" "$port" >/dev/null 2>&1; do
        sleep "$interval"
        elapsed=$((elapsed + interval))
        
        if [[ $elapsed -ge $timeout ]]; then
            log_error "$service_name is not responding after ${timeout}s"
            return 1
        fi
        
        if [[ $((elapsed % 10)) -eq 0 ]]; then
            log "Still waiting for $service_name... (${elapsed}s elapsed)"
        fi
    done
    
    log_success "$service_name is responding"
    return 0
}

validate_service_health() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Service Health for $env Environment"
    
    # Get running services
    local services
    services=$(docker compose -f "$compose_file" ps --services --filter "status=running")
    
    if [[ -z "$services" ]]; then
        log_error "No running services found"
        return 1
    fi
    
    local all_healthy=true
    
    # Check each service
    while IFS= read -r service; do
        log "Checking health of service: $service"
        
        # Get container ID
        local container_id
        container_id=$(docker compose -f "$compose_file" ps -q "$service")
        
        if [[ -z "$container_id" ]]; then
            log_error "Container not found for service: $service"
            all_healthy=false
            continue
        fi
        
        # Check if container is running
        local container_status
        container_status=$(docker inspect --format='{{.State.Status}}' "$container_id")
        
        if [[ "$container_status" != "running" ]]; then
            log_error "Service $service is not running (status: $container_status)"
            all_healthy=false
            continue
        fi
        
        # Check health status if available
        local health_status
        health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "none")
        
        if [[ "$health_status" == "unhealthy" ]]; then
            log_error "Service $service is unhealthy"
            all_healthy=false
        elif [[ "$health_status" == "healthy" ]]; then
            log_success "Service $service is healthy"
        else
            log_warning "Service $service has no health check defined"
        fi
        
    done <<< "$services"
    
    if [[ "$all_healthy" == true ]]; then
        log_success "All services are healthy"
        return 0
    else
        log_error "Some services are not healthy"
        return 1
    fi
}

validate_application_endpoints() {
    local env=$1
    local port=$2
    
    log_section "Validating Application Endpoints for $env Environment"
    
    # Wait for web service to be ready
    if ! wait_for_service "web application" "localhost" "$port" 120; then
        return 1
    fi
    
    # Test health endpoint
    log "Testing health check endpoint..."
    local health_response
    if health_response=$(curl -s -f "http://localhost:$port/health/" 2>/dev/null); then
        log_success "Health endpoint is responding"
        log "Health response: $health_response"
        
        # Validate JSON response
        if echo "$health_response" | jq -e '.status' >/dev/null 2>&1; then
            local status
            status=$(echo "$health_response" | jq -r '.status')
            if [[ "$status" == "healthy" ]]; then
                log_success "Application reports healthy status"
            else
                log_warning "Application status: $status"
            fi
        else
            log_warning "Health endpoint returned non-JSON response"
        fi
    else
        log_error "Health endpoint is not responding"
        return 1
    fi
    
    # Test home endpoint
    log "Testing home endpoint..."
    local home_response
    if home_response=$(curl -s -f "http://localhost:$port/" 2>/dev/null); then
        log_success "Home endpoint is responding"
        
        # Check if it's JSON and contains expected fields
        if echo "$home_response" | jq -e '.message' >/dev/null 2>&1; then
            local message
            message=$(echo "$home_response" | jq -r '.message')
            log_success "Home endpoint returned valid JSON: $message"
        else
            log_warning "Home endpoint returned non-JSON response"
        fi
    else
        log_error "Home endpoint is not responding"
        return 1
    fi
    
    return 0
}

validate_database_connectivity() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Database Connectivity for $env Environment"
    
    # Run database connectivity test through web container
    log "Testing database connection..."
    
    local db_test_result
    if db_test_result=$(docker compose -f "$compose_file" exec -T web python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.$env')
django.setup()
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print('Database connection successful, result:', result)
except Exception as e:
    print('Database connection failed:', str(e))
    exit(1)
" 2>&1); then
        log_success "Database connectivity test passed"
        log "Database test result: $db_test_result"
    else
        log_error "Database connectivity test failed"
        log "Error: $db_test_result"
        return 1
    fi
    
    return 0
}

validate_cache_connectivity() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Cache Connectivity for $env Environment"
    
    # Test cache connectivity through web container
    log "Testing cache connection..."
    
    local cache_test_result
    if cache_test_result=$(docker compose -f "$compose_file" exec -T web python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.$env')
django.setup()
from django.core.cache import cache
try:
    cache.set('test_key', 'test_value', 10)
    result = cache.get('test_key')
    if result == 'test_value':
        print('Cache test successful')
    else:
        print('Cache test failed: unexpected value')
        exit(1)
except Exception as e:
    print('Cache connection failed:', str(e))
    exit(1)
" 2>&1); then
        log_success "Cache connectivity test passed"
        log "Cache test result: $cache_test_result"
    else
        log_error "Cache connectivity test failed"
        log "Error: $cache_test_result"
        return 1
    fi
    
    return 0
}

run_environment_tests() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Running Environment-Specific Tests for $env"
    
    # Run Django tests
    log "Running Django tests..."
    
    local test_result
    if test_result=$(docker compose -f "$compose_file" exec -T web python manage.py test --verbosity=1 --keepdb 2>&1); then
        log_success "Django tests passed"
        local test_count
        test_count=$(echo "$test_result" | grep -o "Ran [0-9]* test" | head -1 || echo "Ran unknown tests")
        log "Test summary: $test_count"
    else
        log_error "Django tests failed"
        log "Test output: $test_result"
        return 1
    fi
    
    return 0
}

deploy_and_validate_environment() {
    local env=$1
    local port=$2
    
    log_section "Deploying and Validating $env Environment"
    
    cd "$PROJECT_ROOT"
    
    # Validate files exist
    if ! validate_files_exist "$env"; then
        return 1
    fi
    
    local compose_file="docker-compose.$env.yml"
    
    # Copy environment file
    local env_file="environments/.env.$env.example"
    if [[ -f "$env_file" ]]; then
        cp "$env_file" ".env.$env" || {
            log_error "Failed to copy environment file"
            return 1
        }
    fi
    
    # Build and start services
    log "Building and starting $env environment..."
    
    if docker compose -f "$compose_file" up -d --build 2>&1 | tee -a "$VALIDATION_LOG"; then
        log_success "Services started for $env environment"
    else
        log_error "Failed to start services for $env environment"
        return 1
    fi
    
    # Wait for services to be ready
    sleep 10
    
    # Validate service health
    if ! validate_service_health "$env"; then
        return 1
    fi
    
    # Validate application endpoints (only if port is provided)
    if [[ -n "$port" ]]; then
        if ! validate_application_endpoints "$env" "$port"; then
            return 1
        fi
    fi
    
    # Validate database connectivity
    if ! validate_database_connectivity "$env"; then
        return 1
    fi
    
    # Validate cache connectivity
    if ! validate_cache_connectivity "$env"; then
        return 1
    fi
    
    # Run environment-specific tests
    if ! run_environment_tests "$env"; then
        return 1
    fi
    
    log_success "$env environment validation completed successfully"
    
    # Stop services
    log "Stopping $env environment..."
    docker compose -f "$compose_file" down -v >/dev/null 2>&1 || true
    
    return 0
}

generate_validation_report() {
    log_section "Validation Report Summary"
    
    local total_checks=${#VALIDATION_RESULTS[@]}
    local successful_checks=0
    local warnings=0
    local errors=0
    
    for result in "${VALIDATION_RESULTS[@]}"; do
        if [[ "$result" == ✅* ]]; then
            ((successful_checks++))
        elif [[ "$result" == ⚠️* ]]; then
            ((warnings++))
        elif [[ "$result" == ❌* ]]; then
            ((errors++))
        fi
    done
    
    log ""
    log "📊 VALIDATION SUMMARY:"
    log "   Total checks: $total_checks"
    log "   Successful: $successful_checks"
    log "   Warnings: $warnings"
    log "   Errors: $errors"
    log ""
    
    if [[ $errors -eq 0 ]]; then
        log_success "All deployment stages validated successfully!"
        if [[ $warnings -gt 0 ]]; then
            log_warning "There were $warnings warnings to review"
        fi
        return 0
    else
        log_error "Validation failed with $errors error(s)"
        return 1
    fi
}

# Main execution
main() {
    local target_env="${1:-all}"
    
    # Initialize log
    echo "Deployment Validation Started: $(date)" > "$VALIDATION_LOG"
    log_section "Docker Stage Deployment Validation"
    log "Target environment: $target_env"
    log "Log file: $VALIDATION_LOG"
    
    # Validate Docker environment
    if ! validate_docker_environment; then
        log_error "Docker environment validation failed"
        exit 1
    fi
    
    local overall_success=true
    
    # Validate specific environment or all environments
    case "$target_env" in
        "development"|"dev")
            if ! deploy_and_validate_environment "development" "8000"; then
                overall_success=false
            fi
            ;;
        "testing"|"test")
            if ! deploy_and_validate_environment "testing" "8001"; then
                overall_success=false
            fi
            ;;
        "production"|"prod")
            if ! deploy_and_validate_environment "production" "8002"; then
                overall_success=false
            fi
            ;;
        "all")
            log_section "Validating All Environments"
            
            if ! deploy_and_validate_environment "development" "8000"; then
                overall_success=false
            fi
            
            if ! deploy_and_validate_environment "testing" "8001"; then
                overall_success=false
            fi
            
            if ! deploy_and_validate_environment "production" "8002"; then
                overall_success=false
            fi
            ;;
        *)
            log_error "Invalid environment: $target_env"
            log "Valid options: development, testing, production, all"
            exit 1
            ;;
    esac
    
    # Generate final report
    generate_validation_report
    
    if [[ "$overall_success" == true ]]; then
        exit 0
    else
        exit 1
    fi
}

# Show usage if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  development  - Deploy and validate development stage"
    echo "  testing      - Deploy and validate testing stage"
    echo "  production   - Deploy and validate production stage"
    echo "  all          - Deploy and validate all stages (default)"
    echo ""
    echo "Options:"
    echo "  --help, -h   - Show this help message"
    echo ""
    echo "This script deploys each Docker stage and validates that all services,"
    echo "configuration, and codebase are functional and performing as expected."
    exit 0
fi

# Execute main function
main "$@"