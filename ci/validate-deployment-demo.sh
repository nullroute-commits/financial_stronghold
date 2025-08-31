#!/bin/bash
# Simple deployment validation demo script
# Validates deployment readiness without full build to work around SSL issues
# Last updated: 2025-08-31 by automation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "$1"
}

log_section() {
    echo ""
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

# Validate Docker Compose configuration
validate_compose_config() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    log_section "Validating Docker Compose Configuration for $env"
    
    if [[ ! -f "$compose_file" ]]; then
        log_error "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    # Validate compose file syntax
    if docker compose -f "$compose_file" config >/dev/null 2>&1; then
        log_success "Docker Compose configuration is valid for $env"
    else
        log_error "Docker Compose configuration is invalid for $env"
        docker compose -f "$compose_file" config
        return 1
    fi
    
    # Check required services exist
    local services
    services=$(docker compose -f "$compose_file" config --services)
    
    local required_services=("web" "db" "memcached" "rabbitmq")
    local missing_services=()
    
    for service in "${required_services[@]}"; do
        if ! echo "$services" | grep -q "^$service$"; then
            missing_services+=("$service")
        fi
    done
    
    if [[ ${#missing_services[@]} -gt 0 ]]; then
        log_error "Missing required services in $env: ${missing_services[*]}"
        return 1
    else
        log_success "All required services are defined in $env"
    fi
    
    return 0
}

# Validate environment files
validate_environment_files() {
    local env=$1
    local env_file="environments/.env.$env.example"
    
    log_section "Validating Environment Configuration for $env"
    
    if [[ ! -f "$env_file" ]]; then
        log_error "Environment file not found: $env_file"
        return 1
    fi
    
    log_success "Environment file exists: $env_file"
    
    # Check for required environment variables
    local required_vars=("DJANGO_SETTINGS_MODULE" "POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_warning "Missing environment variables in $env: ${missing_vars[*]}"
    else
        log_success "All required environment variables are defined in $env"
    fi
    
    return 0
}

# Validate Dockerfile configuration
validate_dockerfile() {
    log_section "Validating Dockerfile Configuration"
    
    if [[ ! -f "Dockerfile" ]]; then
        log_error "Dockerfile not found"
        return 1
    fi
    
    log_success "Dockerfile exists"
    
    # Check for required stages
    local required_stages=("base" "development" "testing" "production")
    local missing_stages=()
    
    for stage in "${required_stages[@]}"; do
        if ! grep -q "FROM .* as $stage" Dockerfile; then
            missing_stages+=("$stage")
        fi
    done
    
    if [[ ${#missing_stages[@]} -gt 0 ]]; then
        log_error "Missing required Docker stages: ${missing_stages[*]}"
        return 1
    else
        log_success "All required Docker stages are defined"
    fi
    
    return 0
}

# Validate health check implementation
validate_health_checks() {
    log_section "Validating Health Check Implementation"
    
    # Check if health check endpoint is implemented
    if grep -q "health_check" config/urls.py; then
        log_success "Health check endpoint is implemented"
    else
        log_error "Health check endpoint is not implemented"
        return 1
    fi
    
    # Check if comprehensive health checks are implemented
    if grep -q "database.*connection" config/urls.py; then
        log_success "Database health check is implemented"
    else
        log_warning "Database health check may not be comprehensive"
    fi
    
    if grep -q "cache" config/urls.py; then
        log_success "Cache health check is implemented"
    else
        log_warning "Cache health check may not be implemented"
    fi
    
    return 0
}

# Validate requirements and dependencies
validate_requirements() {
    log_section "Validating Requirements and Dependencies"
    
    local envs=("development" "test" "production")
    local all_valid=true
    
    for env in "${envs[@]}"; do
        local req_file="requirements/$env.txt"
        
        if [[ ! -f "$req_file" ]]; then
            log_error "Requirements file not found: $req_file"
            all_valid=false
            continue
        fi
        
        log_success "Requirements file exists: $req_file"
        
        # Check for Django
        if grep -q "Django==" "$req_file"; then
            log_success "Django dependency is specified in $req_file"
        else
            log_error "Django dependency is missing in $req_file"
            all_valid=false
        fi
    done
    
    if [[ "$all_valid" == true ]]; then
        log_success "All requirements files are properly configured"
        return 0
    else
        log_error "Some requirements files have issues"
        return 1
    fi
}

# Main validation function
main() {
    local target_env="${1:-all}"
    
    log_section "Deployment Validation Demo"
    log "Target environment: $target_env"
    echo ""
    
    local overall_success=true
    
    # Validate Docker environment
    log_section "Validating Docker Environment"
    if command -v docker >/dev/null 2>&1; then
        log_success "Docker is installed"
    else
        log_error "Docker is not installed"
        overall_success=false
    fi
    
    if docker compose version >/dev/null 2>&1; then
        log_success "Docker Compose is available"
    else
        log_error "Docker Compose is not available"
        overall_success=false
    fi
    
    # Validate Dockerfile
    if ! validate_dockerfile; then
        overall_success=false
    fi
    
    # Validate requirements
    if ! validate_requirements; then
        overall_success=false
    fi
    
    # Validate health checks
    if ! validate_health_checks; then
        overall_success=false
    fi
    
    # Validate specific environment or all environments
    case "$target_env" in
        "development"|"dev")
            if ! validate_compose_config "development" || ! validate_environment_files "development"; then
                overall_success=false
            fi
            ;;
        "testing"|"test")
            if ! validate_compose_config "testing" || ! validate_environment_files "testing"; then
                overall_success=false
            fi
            ;;
        "production"|"prod")
            if ! validate_compose_config "production" || ! validate_environment_files "production"; then
                overall_success=false
            fi
            ;;
        "all")
            for env in development testing production; do
                if ! validate_compose_config "$env" || ! validate_environment_files "$env"; then
                    overall_success=false
                fi
            done
            ;;
        *)
            log_error "Invalid environment: $target_env"
            log "Valid options: development, testing, production, all"
            exit 1
            ;;
    esac
    
    # Final summary
    echo ""
    log_section "Validation Summary"
    
    if [[ "$overall_success" == true ]]; then
        log_success "All deployment validations passed!"
        log "The deployment configuration is ready for:"
        log "  - Development environment deployment"
        log "  - Testing environment deployment"
        log "  - Production environment deployment"
        log "  - Service health monitoring"
        log "  - Configuration validation"
        echo ""
        log "Next steps:"
        log "  1. Run full deployment validation: ./ci/validate-deployment.sh"
        log "  2. Deploy to development: ./ci/deploy.sh development"
        log "  3. Run tests: ./ci/test.sh"
        log "  4. Deploy to production: ./ci/deploy.sh production"
        exit 0
    else
        log_error "Some deployment validations failed!"
        log "Please fix the issues above before deploying."
        exit 1
    fi
}

# Show usage if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  development  - Validate development stage configuration"
    echo "  testing      - Validate testing stage configuration"
    echo "  production   - Validate production stage configuration"
    echo "  all          - Validate all stages (default)"
    echo ""
    echo "Options:"
    echo "  --help, -h   - Show this help message"
    echo ""
    echo "This script validates the deployment configuration readiness"
    echo "for each Docker stage without requiring full builds."
    exit 0
fi

# Execute main function
main "$@"