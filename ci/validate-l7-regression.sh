#!/bin/bash
# L7 Regression Validation Script
# Comprehensive testing and backwards compatibility
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    local port="${2:-8000}"
    log_section "L7 Regression Validation"
    validate_l7_regression "$env" "$port"
}

main "$@"