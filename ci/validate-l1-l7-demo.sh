#!/bin/bash
# L1-L7 Configuration Demo Script
# Quick validation demo without full Docker deployment
# Last updated: 2025-09-01 by automation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEMO_LOG="$PROJECT_ROOT/l1-l7-demo-results.log"

# Logging functions
log() {
    echo -e "$1" | tee -a "$DEMO_LOG"
}

log_section() {
    echo "" | tee -a "$DEMO_LOG"
    log "${BLUE}=== $1 ===${NC}"
}

log_level() {
    local level=$1
    local message=$2
    echo "" | tee -a "$DEMO_LOG"
    log "${PURPLE}=== L$level - $message ===${NC}"
}

log_success() {
    local message="✅ $1"
    log "${GREEN}$message${NC}"
}

log_warning() {
    local message="⚠️  $1"
    log "${YELLOW}$message${NC}"
}

log_error() {
    local message="❌ $1"
    log "${RED}$message${NC}"
}

log_info() {
    local message="ℹ️  $1"
    log "${CYAN}$message${NC}"
}

# Initialize demo log
echo "L1-L7 Deployment Validation Demo Started: $(date)" > "$DEMO_LOG"

# L1 Demo - Configuration Validation
demo_l1_configuration() {
    local env=$1
    log_level "1" "Configuration Validation Demo for $env"
    
    # Docker Compose file syntax validation
    log_info "Validating Docker Compose configuration..."
    if docker compose -f "docker-compose.$env.yml" config >/dev/null 2>&1; then
        log_success "Docker Compose configuration syntax valid for $env"
    else
        log_error "Docker Compose configuration syntax invalid for $env"
    fi
    
    # Environment file completeness
    local env_file="environments/.env.$env.example"
    if [[ -f "$env_file" ]]; then
        log_success "Environment file exists: $env_file"
        
        # Check for required variables
        local required_vars=("DJANGO_SETTINGS_MODULE" "SECRET_KEY")
        for var in "${required_vars[@]}"; do
            if grep -q "^$var=" "$env_file" || grep -q "^#.*$var=" "$env_file"; then
                log_success "Required variable $var defined in $env_file"
            else
                log_warning "Variable $var may be missing in $env_file"
            fi
        done
    else
        log_error "Environment file missing: $env_file"
    fi
    
    # Dockerfile validation
    if [[ -f "Dockerfile" ]]; then
        log_success "Dockerfile exists"
        if grep -q "development\|testing\|production" Dockerfile; then
            log_success "Dockerfile contains build stages"
        else
            log_info "Dockerfile may use single stage"
        fi
    else
        log_error "Dockerfile not found"
    fi
    
    # Requirements file validation
    local req_file="requirements/development.txt"
    if [[ -f "$req_file" ]]; then
        log_success "Requirements file exists: $req_file"
        if grep -q "Django" "$req_file"; then
            log_success "Django dependency found in requirements"
        else
            log_error "Django dependency missing in requirements"
        fi
    else
        log_error "Requirements file not found"
    fi
}

# L2 Demo - Service Configuration Check
demo_l2_startup() {
    local env=$1
    log_level "2" "Service Startup Configuration Demo for $env"
    
    # Check Docker Compose services
    log_info "Checking service definitions..."
    local services
    services=$(docker compose -f "docker-compose.$env.yml" config --services 2>/dev/null || echo "")
    
    if [[ -n "$services" ]]; then
        log_success "Service definitions found:"
        echo "$services" | while read -r service; do
            log_success "  - Service: $service"
        done
    else
        log_error "No services found in Docker Compose file"
    fi
    
    # Check port mappings
    log_info "Checking port configurations..."
    local ports
    ports=$(docker compose -f "docker-compose.$env.yml" config | grep -A1 "ports:" | grep -E "^\s*-\s*[0-9]+:" || echo "")
    
    if [[ -n "$ports" ]]; then
        log_success "Port mappings configured"
    else
        log_info "No explicit port mappings found"
    fi
}

# L3 Demo - Network Configuration Check
demo_l3_connectivity() {
    local env=$1
    log_level "3" "Connectivity Configuration Demo for $env"
    
    # Check for database service
    if docker compose -f "docker-compose.$env.yml" config | grep -q "db:"; then
        log_success "Database service configured"
    else
        log_warning "Database service not found"
    fi
    
    # Check for cache service
    if docker compose -f "docker-compose.$env.yml" config | grep -q "memcached\|redis"; then
        log_success "Cache service configured"
    else
        log_info "Cache service not explicitly configured"
    fi
    
    # Check for message queue
    if docker compose -f "docker-compose.$env.yml" config | grep -q "rabbitmq\|celery"; then
        log_success "Message queue service configured"
    else
        log_info "Message queue service not explicitly configured"
    fi
    
    # Check network configuration
    if docker compose -f "docker-compose.$env.yml" config | grep -q "networks:"; then
        log_success "Custom network configuration found"
    else
        log_info "Using default Docker network"
    fi
}

# L4 Demo - Application Configuration Check
demo_l4_functionality() {
    local env=$1
    log_level "4" "Functionality Configuration Demo for $env"
    
    # Check for health check configuration
    if docker compose -f "docker-compose.$env.yml" config | grep -q "healthcheck:"; then
        log_success "Health check configuration found"
    else
        log_info "Health check not explicitly configured"
    fi
    
    # Check for environment variables
    log_info "Checking Django configuration..."
    if docker compose -f "docker-compose.$env.yml" config | grep -q "DJANGO_SETTINGS_MODULE"; then
        log_success "Django settings module configured"
    else
        log_warning "Django settings module not found"
    fi
    
    # Check for static files handling
    if docker compose -f "docker-compose.$env.yml" config | grep -q "collectstatic\|static"; then
        log_success "Static files configuration found"
    else
        log_info "Static files handling not explicitly configured"
    fi
}

# L5 Demo - Integration Configuration Check
demo_l5_integration() {
    local env=$1
    log_level "5" "Integration Configuration Demo for $env"
    
    # Check for depends_on configuration
    if docker compose -f "docker-compose.$env.yml" config | grep -q "depends_on:"; then
        log_success "Service dependencies configured"
    else
        log_info "Service dependencies not explicitly configured"
    fi
    
    # Check for volume mounts
    if docker compose -f "docker-compose.$env.yml" config | grep -q "volumes:"; then
        log_success "Volume mounts configured"
    else
        log_info "Volume mounts not found"
    fi
    
    # Check for environment file usage
    if docker compose -f "docker-compose.$env.yml" config | grep -q "env_file:"; then
        log_success "Environment file integration configured"
    else
        log_info "Environment file not explicitly configured"
    fi
}

# L6 Demo - Performance Configuration Check
demo_l6_performance() {
    local env=$1
    log_level "6" "Performance Configuration Demo for $env"
    
    # Check for resource limits
    if docker compose -f "docker-compose.$env.yml" config | grep -q "resources:\|memory:\|cpus:"; then
        log_success "Resource limits configured"
    else
        log_info "Resource limits not explicitly configured"
    fi
    
    # Check for restart policies
    if docker compose -f "docker-compose.$env.yml" config | grep -q "restart:"; then
        log_success "Restart policy configured"
    else
        log_info "Restart policy not explicitly configured"
    fi
    
    # Check for scaling configuration
    if docker compose -f "docker-compose.$env.yml" config | grep -q "replicas:\|scale:"; then
        log_success "Scaling configuration found"
    else
        log_info "Scaling not explicitly configured"
    fi
}

# L7 Demo - Testing Configuration Check
demo_l7_regression() {
    local env=$1
    log_level "7" "Regression Configuration Demo for $env"
    
    # Check for test files
    if [[ -d "tests" ]]; then
        log_success "Test directory exists"
        local test_files
        test_files=$(find tests -name "*.py" -type f | wc -l)
        log_success "Found $test_files test files"
    else
        log_warning "Test directory not found"
    fi
    
    # Check for pytest configuration
    if [[ -f "pytest.ini" ]] || [[ -f "pyproject.toml" ]] || [[ -f "setup.cfg" ]]; then
        log_success "Test configuration file found"
    else
        log_info "Test configuration file not found"
    fi
    
    # Check for coverage configuration
    if [[ -f ".coveragerc" ]] || grep -q "coverage" "pyproject.toml" 2>/dev/null; then
        log_success "Coverage configuration found"
    else
        log_info "Coverage configuration not found"
    fi
    
    # Check for CI configuration
    if [[ -d ".github/workflows" ]]; then
        log_success "CI/CD workflows configured"
    else
        log_info "CI/CD workflows not found"
    fi
}

# Main demo function for single environment
demo_environment_l1_l7() {
    local env=$1
    
    log_section "L1-L7 Configuration Demo for $env Environment"
    
    # Run each demo level
    demo_l1_configuration "$env"
    demo_l2_startup "$env"
    demo_l3_connectivity "$env"
    demo_l4_functionality "$env"
    demo_l5_integration "$env"
    demo_l6_performance "$env"
    demo_l7_regression "$env"
    
    log_success "L1-L7 configuration demo completed for $env"
}

# Main execution
main() {
    local target_env="${1:-all}"
    
    log_section "L1-L7 Deployment Validation Configuration Demo"
    log_info "Target environment: $target_env"
    log_info "Following FEATURE_DEPLOYMENT_GUIDE.md specifications"
    
    cd "$PROJECT_ROOT"
    
    case "$target_env" in
        "development")
            demo_environment_l1_l7 "development"
            ;;
        "testing")
            demo_environment_l1_l7 "testing"
            ;;
        "production")
            demo_environment_l1_l7 "production"
            ;;
        "all")
            demo_environment_l1_l7 "development"
            demo_environment_l1_l7 "testing"
            demo_environment_l1_l7 "production"
            ;;
        *)
            log_error "Invalid environment: $target_env"
            log_info "Valid options: development, testing, production, all"
            exit 1
            ;;
    esac
    
    log_section "L1-L7 Configuration Demo Summary"
    log_success "🎉 All L1-L7 configuration demos completed successfully!"
    log_info "Demo log saved to: $DEMO_LOG"
    log_info "For full deployment validation, run: ./ci/validate-deployment-l1-l7.sh"
}

# Help function
show_help() {
    echo "L1-L7 Deployment Validation Configuration Demo"
    echo ""
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  development  - Demo development stage configuration"
    echo "  testing      - Demo testing stage configuration"
    echo "  production   - Demo production stage configuration"
    echo "  all          - Demo all stages (default)"
    echo ""
    echo "This script demonstrates L1-L7 validation configuration without full deployment:"
    echo "  L1 - Configuration Validation"
    echo "  L2 - Service Startup Configuration"
    echo "  L3 - Connectivity Configuration"
    echo "  L4 - Functionality Configuration"
    echo "  L5 - Integration Configuration"
    echo "  L6 - Performance Configuration"
    echo "  L7 - Regression Configuration"
    exit 0
}

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
fi

# Execute main function
main "$@"