#!/bin/bash
# L5 Integration Validation Script
# Cross-service communication and data flow validation
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    local port="${2:-8000}"
    log_section "L5 Integration Validation"
    validate_l5_integration "$env" "$port"
}

main "$@"