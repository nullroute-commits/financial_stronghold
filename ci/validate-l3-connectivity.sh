#!/bin/bash
# L3 Connectivity Validation Script
# Inter-service connectivity and basic operations
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    local port="${2:-8000}"
    log_section "L3 Connectivity Validation"
    validate_l3_connectivity "$env" "$port"
}

main "$@"