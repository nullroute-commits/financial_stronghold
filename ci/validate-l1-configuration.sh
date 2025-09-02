#!/bin/bash
# L1 Configuration Validation Script
# Basic configuration and file validation
# Part of L1-L7 deployment validation system

source "$(dirname "$0")/validate-deployment-l1-l7.sh"

main() {
    local env="${1:-development}"
    log_section "L1 Configuration Validation"
    validate_l1_configuration "$env"
}

main "$@"