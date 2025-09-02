#!/bin/bash
# L6 Performance Validation Script
# Performance metrics and resource utilization validation
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    local port="${2:-8000}"
    log_section "L6 Performance Validation"
    validate_l6_performance "$env" "$port"
}

main "$@"