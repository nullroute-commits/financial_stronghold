#!/bin/bash
# L4 Functionality Validation Script
# Application endpoint and core functionality validation
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    local port="${2:-8000}"
    log_section "L4 Functionality Validation"
    validate_l4_functionality "$env" "$port"
}

main "$@"