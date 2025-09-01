#!/bin/bash
# Enhanced debugging validation script for CI/CD deployment stages
# Provides comprehensive debugging information for all deployment issues
# Last updated: 2025-09-01 by copilot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEBUG_LOG="$PROJECT_ROOT/debug-validation.log"
ERROR_LOG="$PROJECT_ROOT/debug-errors.log"

# Initialize log files
echo "Enhanced Debug Validation Started: $(date)" > "$DEBUG_LOG"
echo "Error Log Started: $(date)" > "$ERROR_LOG"

# Enhanced logging functions
log() {
    echo -e "$1" | tee -a "$DEBUG_LOG"
}

log_section() {
    echo "" | tee -a "$DEBUG_LOG"
    log "${BLUE}=== $1 ===${NC}"
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
    echo "$(date): $1" >> "$ERROR_LOG"
}

log_debug() {
    local message="🔍 DEBUG: $1"
    log "${PURPLE}$message${NC}"
}

# System Information Collection
collect_system_info() {
    log_section "System Information Collection"
    
    log_debug "Operating System: $(uname -a)"
    log_debug "Docker Version: $(docker --version 2>/dev/null || echo 'Not installed')"
    log_debug "Docker Compose Version: $(docker compose version 2>/dev/null || echo 'Not installed')"
    log_debug "Available Memory: $(free -h 2>/dev/null | grep Mem || echo 'Unknown')"
    log_debug "Available Disk Space: $(df -h . 2>/dev/null | tail -1 || echo 'Unknown')"
    log_debug "CPU Count: $(nproc 2>/dev/null || echo 'Unknown')"
    
    # Check Docker daemon status
    if docker info >/dev/null 2>&1; then
        log_success "Docker daemon is running"
        log_debug "Docker Info: $(docker info --format '{{.ServerVersion}}' 2>/dev/null)"
    else
        log_error "Docker daemon is not accessible"
        return 1
    fi
}

# Enhanced dependency validation
validate_dependencies() {
    log_section "Dependency Validation"
    
    local missing_deps=()
    local requirements_issues=()
    
    # Check requirements files
    for req_file in requirements/development.txt requirements/test.txt requirements/production.txt; do
        if [[ -f "$req_file" ]]; then
            log_success "Requirements file exists: $req_file"
            
            # Check for common missing dependencies
            if ! grep -q "PyYAML" "$req_file"; then
                requirements_issues+=("PyYAML missing in $req_file")
            fi
            if ! grep -q "markdown" "$req_file"; then
                requirements_issues+=("markdown missing in $req_file")
            fi
        else
            missing_deps+=("$req_file")
        fi
    done
    
    # Report findings
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing requirements files: ${missing_deps[*]}"
    fi
    
    if [[ ${#requirements_issues[@]} -gt 0 ]]; then
        log_warning "Requirements issues found:"
        for issue in "${requirements_issues[@]}"; do
            log_warning "  - $issue"
        done
    fi
}

# Enhanced schema validation
validate_schemas() {
    log_section "Schema Validation"
    
    if [[ -f "app/schemas.py" ]]; then
        log_success "Schemas file exists"
        
        # Check for required schema classes
        local required_schemas=(
            "UserCreateSchema"
            "UserUpdateSchema" 
            "UserResponseSchema"
            "TenantCreateSchema"
            "AccountCreateSchema"
            "TransactionCreateSchema"
        )
        
        local missing_schemas=()
        for schema in "${required_schemas[@]}"; do
            if ! grep -q "$schema" app/schemas.py; then
                missing_schemas+=("$schema")
            fi
        done
        
        if [[ ${#missing_schemas[@]} -gt 0 ]]; then
            log_error "Missing schema classes: ${missing_schemas[*]}"
        else
            log_success "All required schema classes found"
        fi
    else
        log_error "app/schemas.py file not found"
    fi
}

# Enhanced Docker configuration validation
validate_docker_configs() {
    log_section "Docker Configuration Validation"
    
    local environments=("development" "testing" "staging" "production")
    local config_issues=()
    
    for env in "${environments[@]}"; do
        local compose_file="docker-compose.$env.yml"
        local env_file="environments/.env.$env.example"
        
        log_debug "Validating $env environment..."
        
        # Check compose file
        if [[ -f "$compose_file" ]]; then
            log_success "$compose_file exists"
            
            # Validate compose syntax
            if docker compose -f "$compose_file" config >/dev/null 2>&1; then
                log_success "$compose_file syntax is valid"
            else
                log_error "$compose_file has syntax errors"
                docker compose -f "$compose_file" config 2>&1 | tee -a "$ERROR_LOG"
                config_issues+=("$compose_file syntax error")
            fi
            
            # Check required services
            local services
            services=$(docker compose -f "$compose_file" config --services 2>/dev/null)
            local required_services=("web" "db")
            
            for service in "${required_services[@]}"; do
                if echo "$services" | grep -q "^$service$"; then
                    log_success "$env has required service: $service"
                else
                    log_warning "$env missing service: $service"
                fi
            done
        else
            log_error "$compose_file not found"
            config_issues+=("$compose_file missing")
        fi
        
        # Check environment file
        if [[ -f "$env_file" ]]; then
            log_success "$env_file exists"
        else
            log_warning "$env_file not found"
        fi
    done
    
    return ${#config_issues[@]}
}

# Enhanced health check validation
validate_health_checks() {
    log_section "Health Check Validation"
    
    # Check health check endpoint implementation
    if [[ -f "config/urls.py" ]]; then
        if grep -q "health_check" config/urls.py; then
            log_success "Health check endpoint is implemented"
            
            # Analyze health check implementation
            if grep -q "database" config/urls.py; then
                log_success "Database health check is implemented"
            else
                log_warning "Database health check may be missing"
            fi
            
            if grep -q "cache" config/urls.py; then
                log_success "Cache health check is implemented"
            else
                log_warning "Cache health check may be missing"
            fi
        else
            log_error "Health check endpoint not found in urls.py"
        fi
    else
        log_error "config/urls.py not found"
    fi
}

# Container diagnostics
run_container_diagnostics() {
    log_section "Container Diagnostics"
    
    # List running containers
    local running_containers
    running_containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers running")
    log_debug "Running containers:"
    echo "$running_containers" | tee -a "$DEBUG_LOG"
    
    # Check for any stopped containers from previous runs
    local stopped_containers
    stopped_containers=$(docker ps -a --filter "status=exited" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "No stopped containers")
    if [[ "$stopped_containers" != "No stopped containers" ]]; then
        log_warning "Found stopped containers:"
        echo "$stopped_containers" | tee -a "$DEBUG_LOG"
    fi
    
    # Check Docker resource usage
    log_debug "Docker system info:"
    docker system df 2>/dev/null | tee -a "$DEBUG_LOG" || log_warning "Could not get Docker system info"
}

# Test execution with detailed error capture
run_test_diagnostics() {
    log_section "Test Diagnostics"
    
    # Try to collect Django tests without running them
    log_debug "Attempting to collect Django tests..."
    
    if command -v python >/dev/null 2>&1; then
        local test_collection_output
        test_collection_output=$(python manage.py test --dry-run 2>&1 || echo "Test collection failed")
        log_debug "Test collection result:"
        echo "$test_collection_output" | tee -a "$DEBUG_LOG"
        
        # Check for specific import errors
        if echo "$test_collection_output" | grep -q "ImportError"; then
            log_error "Import errors detected in tests"
            echo "$test_collection_output" | grep "ImportError" | tee -a "$ERROR_LOG"
        fi
        
        if echo "$test_collection_output" | grep -q "ModuleNotFoundError"; then
            log_error "Missing modules detected"
            echo "$test_collection_output" | grep "ModuleNotFoundError" | tee -a "$ERROR_LOG"
        fi
    else
        log_warning "Python not available for test diagnostics"
    fi
}

# Network and port diagnostics
check_network_diagnostics() {
    log_section "Network Diagnostics"
    
    # Check common ports
    local ports=(8000 8001 8002 8003 5432 11211 5672 15672)
    
    for port in "${ports[@]}"; do
        if netstat -ln 2>/dev/null | grep -q ":$port "; then
            log_warning "Port $port is already in use"
        else
            log_debug "Port $port is available"
        fi
    done
    
    # Check for Docker networks
    local networks
    networks=$(docker network ls 2>/dev/null || echo "Could not list networks")
    log_debug "Docker networks:"
    echo "$networks" | tee -a "$DEBUG_LOG"
}

# Generate comprehensive report
generate_debug_report() {
    log_section "Debug Report Generation"
    
    local report_file="$PROJECT_ROOT/debug-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "====================================="
        echo "Enhanced Debug Validation Report"
        echo "Generated: $(date)"
        echo "====================================="
        echo ""
        echo "SYSTEM INFORMATION:"
        echo "-------------------"
        uname -a
        echo ""
        echo "DOCKER INFORMATION:"
        echo "------------------"
        docker --version 2>/dev/null || echo "Docker not available"
        docker compose version 2>/dev/null || echo "Docker Compose not available"
        echo ""
        echo "VALIDATION LOG:"
        echo "---------------"
        cat "$DEBUG_LOG" 2>/dev/null || echo "Debug log not available"
        echo ""
        echo "ERROR LOG:"
        echo "----------"
        cat "$ERROR_LOG" 2>/dev/null || echo "No errors logged"
    } > "$report_file"
    
    log_success "Debug report generated: $report_file"
}

# Cleanup function
cleanup() {
    log_section "Cleanup"
    log_success "Debug validation completed"
    log "Logs available at:"
    log "  Debug log: $DEBUG_LOG"
    log "  Error log: $ERROR_LOG"
}

# Main execution
main() {
    local target_env="${1:-all}"
    
    log_section "Enhanced Debug Validation for CI/CD Deployment Stages"
    log "Target environment: $target_env"
    
    # Run all diagnostic functions
    collect_system_info || log_error "System info collection failed"
    validate_dependencies || log_error "Dependency validation failed"
    validate_schemas || log_error "Schema validation failed"
    validate_docker_configs || log_error "Docker config validation failed"
    validate_health_checks || log_error "Health check validation failed"
    run_container_diagnostics || log_error "Container diagnostics failed"
    run_test_diagnostics || log_error "Test diagnostics failed"
    check_network_diagnostics || log_error "Network diagnostics failed"
    
    generate_debug_report
    cleanup
}

# Handle help option
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Enhanced Debug Validation Script"
    echo ""
    echo "Usage: $0 [environment]"
    echo ""
    echo "Arguments:"
    echo "  environment  - Target environment (development, testing, staging, production, all)"
    echo "                 Default: all"
    echo ""
    echo "This script provides comprehensive debugging information for CI/CD deployment stages."
    exit 0
fi

# Execute main function
main "$@"