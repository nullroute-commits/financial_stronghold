#!/bin/bash
# Deployment Health Monitoring Script
# Continuously monitors deployed environments and provides real-time health status
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
HEALTH_LOG="$PROJECT_ROOT/health-monitoring.log"
MONITOR_INTERVAL=${MONITOR_INTERVAL:-30}
MAX_RETRIES=${MAX_RETRIES:-3}

# Initialize log
echo "Health Monitoring Started: $(date)" > "$HEALTH_LOG"

# Logging functions
log() {
    echo -e "$1" | tee -a "$HEALTH_LOG"
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

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

log_debug() {
    log "${PURPLE}🔍 $1${NC}"
}

# Health check functions
check_service_health() {
    local env=$1
    local port=$2
    local retries=0
    
    log_debug "Checking health for $env environment on port $port..."
    
    while [[ $retries -lt $MAX_RETRIES ]]; do
        # Check if port is accessible
        if ! nc -z localhost "$port" >/dev/null 2>&1; then
            log_warning "$env service not accessible on port $port (attempt $((retries + 1))/$MAX_RETRIES)"
            ((retries++))
            sleep 5
            continue
        fi
        
        # Check health endpoint
        local health_response
        if health_response=$(curl -s --max-time 10 "http://localhost:$port/health/" 2>/dev/null); then
            # Parse JSON response
            if echo "$health_response" | jq -e '.status' >/dev/null 2>&1; then
                local status
                status=$(echo "$health_response" | jq -r '.status')
                
                case "$status" in
                    "healthy")
                        log_success "$env environment is healthy"
                        return 0
                        ;;
                    "degraded")
                        log_warning "$env environment is degraded"
                        # Get detailed status
                        local checks
                        checks=$(echo "$health_response" | jq -r '.checks' 2>/dev/null || echo "No details")
                        log_debug "$env health details: $checks"
                        return 1
                        ;;
                    *)
                        log_error "$env environment status: $status"
                        return 2
                        ;;
                esac
            else
                log_warning "$env health endpoint returned non-JSON response"
                return 3
            fi
        else
            log_warning "$env health endpoint not responding (attempt $((retries + 1))/$MAX_RETRIES)"
            ((retries++))
            sleep 5
        fi
    done
    
    log_error "$env environment failed health check after $MAX_RETRIES attempts"
    return 4
}

check_container_status() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    if [[ ! -f "$compose_file" ]]; then
        log_warning "Compose file not found: $compose_file"
        return 1
    fi
    
    log_debug "Checking container status for $env..."
    
    # Get container status
    local containers
    if containers=$(docker compose -f "$compose_file" ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null); then
        local running_count=0
        local total_count=0
        
        while IFS=$'\t' read -r name status; do
            if [[ "$name" == "NAME" ]]; then continue; fi  # Skip header
            if [[ -z "$name" ]]; then continue; fi  # Skip empty lines
            
            ((total_count++))
            if echo "$status" | grep -q "Up"; then
                ((running_count++))
                log_debug "$env: $name is running"
            else
                log_warning "$env: $name is not running ($status)"
            fi
        done <<< "$containers"
        
        if [[ $running_count -eq $total_count ]] && [[ $total_count -gt 0 ]]; then
            log_success "$env: All $total_count containers are running"
            return 0
        else
            log_warning "$env: Only $running_count/$total_count containers are running"
            return 1
        fi
    else
        log_warning "$env: Could not get container status"
        return 2
    fi
}

check_resource_usage() {
    local env=$1
    local compose_file="docker-compose.$env.yml"
    
    if [[ ! -f "$compose_file" ]]; then
        return 1
    fi
    
    log_debug "Checking resource usage for $env..."
    
    # Get resource stats
    local stats
    if stats=$(docker compose -f "$compose_file" ps -q 2>/dev/null | xargs docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null); then
        log_debug "$env resource usage:"
        echo "$stats" | tee -a "$HEALTH_LOG"
    else
        log_debug "$env: Could not get resource usage"
    fi
}

generate_health_summary() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    log_info "=== Health Summary at $timestamp ==="
    
    # Check all environments
    local environments=(
        "development:8000"
        "testing:8001" 
        "staging:8003"
        "production:8002"
    )
    
    local healthy_count=0
    local total_count=${#environments[@]}
    
    for env_config in "${environments[@]}"; do
        local env="${env_config%:*}"
        local port="${env_config#*:}"
        
        log_info "Checking $env environment..."
        
        # Check container status
        if check_container_status "$env"; then
            # Check service health
            if check_service_health "$env" "$port"; then
                ((healthy_count++))
                check_resource_usage "$env"
            fi
        fi
        
        log_info ""
    done
    
    # Overall summary
    if [[ $healthy_count -eq $total_count ]]; then
        log_success "All $total_count environments are healthy"
    else
        log_warning "$healthy_count/$total_count environments are healthy"
    fi
    
    # System resource check
    log_info "System Resources:"
    log_debug "Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"
    log_debug "Disk: $(df -h . | tail -1 | awk '{print $3"/"$2" ("$5" used)"}')"
    log_debug "Load: $(uptime | awk -F'load average:' '{print $2}')"
    
    log_info "=== End Health Summary ==="
}

# Cleanup function
cleanup() {
    log_info "Health monitoring stopped"
}

# Signal handling
trap cleanup EXIT INT TERM

# Main monitoring loop
main() {
    local mode="${1:-continuous}"
    
    case "$mode" in
        "once"|"single")
            log_info "Running single health check..."
            generate_health_summary
            ;;
        "continuous"|"monitor")
            log_info "Starting continuous health monitoring (interval: ${MONITOR_INTERVAL}s)..."
            log_info "Press Ctrl+C to stop monitoring"
            
            while true; do
                generate_health_summary
                
                log_info "Sleeping for ${MONITOR_INTERVAL} seconds..."
                sleep "$MONITOR_INTERVAL"
            done
            ;;
        *)
            echo "Usage: $0 [mode]"
            echo ""
            echo "Modes:"
            echo "  once         - Run single health check (default)"
            echo "  continuous   - Run continuous monitoring"
            echo ""
            echo "Environment variables:"
            echo "  MONITOR_INTERVAL - Monitoring interval in seconds (default: 30)"
            echo "  MAX_RETRIES      - Maximum retries for health checks (default: 3)"
            exit 1
            ;;
    esac
}

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
    log_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    log_warning "jq is not installed - JSON parsing will be limited"
fi

if ! command -v nc >/dev/null 2>&1; then
    log_error "netcat is required but not installed"
    exit 1
fi

# Execute main function
main "$@"