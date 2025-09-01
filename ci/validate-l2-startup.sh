#!/bin/bash
# L2 Service Startup Validation Script
# Container startup and basic health validation
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    local port="${2:-8000}"
    log_section "L2 Service Startup Validation"
    validate_l2_startup "$env" "$port"
}

main "$@"