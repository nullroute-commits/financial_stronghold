#!/bin/bash
# Comprehensive quality gate script
# Team Beta - Architecture Sprint 2
# Aggregates all test results and enforces quality thresholds

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
ORANGE='\033[0;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🚪 Starting comprehensive quality gate evaluation...${NC}"

# Create reports directory
mkdir -p reports/quality-gate

# Set thresholds from environment variables
QUALITY_THRESHOLD=${QUALITY_THRESHOLD:-90}
SECURITY_THRESHOLD=${SECURITY_THRESHOLD:-0}
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-85}

echo -e "${BLUE}Quality Gate Thresholds:${NC}"
echo -e "  Quality Score: ${QUALITY_THRESHOLD}%"
echo -e "  Security Issues: ${SECURITY_THRESHOLD} (0 = no issues allowed)"
echo -e "  Test Coverage: ${COVERAGE_THRESHOLD}%"

# Initialize results tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
QUALITY_SCORE=0

# Function to check test results
check_test_results() {
    local test_type="$1"
    local result_file="$2"
    local required_status="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$result_file" ]; then
        if grep -q "PASSED\|passed\|✅" "$result_file"; then
            echo -e "  ${test_type}: ${GREEN}✅ PASSED${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  ${test_type}: ${RED}❌ FAILED${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  ${test_type}: ${ORANGE}⚠️  NO RESULTS${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check coverage
check_coverage() {
    local coverage_file="$1"
    local threshold="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$coverage_file" ]; then
        # Extract coverage percentage from XML
        local coverage_percent=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('$coverage_file')
    root = tree.getroot()
    coverage = root.attrib.get('line-rate', '0')
    coverage_percent = float(coverage) * 100
    print(f'{coverage_percent:.1f}')
except Exception as e:
    print('0')
" 2>/dev/null)
        
        if [ "$coverage_percent" != "0" ] && [ "$(echo "$coverage_percent >= $threshold" | bc -l)" -eq 1 ]; then
            echo -e "  Test Coverage: ${GREEN}✅ ${coverage_percent}% (≥${threshold}%)${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  Test Coverage: ${RED}❌ ${coverage_percent}% (<${threshold}%)${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  Test Coverage: ${ORANGE}⚠️  NO COVERAGE DATA${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check security scan
check_security_scan() {
    local security_file="$1"
    local threshold="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$security_file" ]; then
        # Count high severity issues
        local high_issues=$(python3 -c "
import json
try:
    with open('$security_file', 'r') as f:
        data = json.load(f)
    
    high_count = 0
    for issue in data.get('results', []):
        if issue.get('issue_severity') == 'HIGH':
            high_count += 1
    
    print(high_count)
except Exception as e:
    print('999')  # Error reading file
" 2>/dev/null)
        
        if [ "$high_issues" != "999" ] && [ "$high_issues" -le "$threshold" ]; then
            echo -e "  Security Scan: ${GREEN}✅ ${high_issues} high severity issues (≤${threshold})${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  Security Scan: ${RED}❌ ${high_issues} high severity issues (>${threshold})${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  Security Scan: ${ORANGE}⚠️  NO SECURITY DATA${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check linting results
check_linting() {
    local lint_file="$1"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$lint_file" ]; then
        if grep -q "PASSED\|passed\|✅\|No issues found" "$lint_file"; then
            echo -e "  Linting: ${GREEN}✅ PASSED${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  Linting: ${RED}❌ FAILED${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  Linting: ${ORANGE}⚠️  NO RESULTS${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check type checking
check_type_checking() {
    local type_file="$1"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$type_file" ]; then
        if grep -q "All type checking passed\|✅ PASSED" "$type_file"; then
            echo -e "  Type Checking: ${GREEN}✅ PASSED${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  Type Checking: ${RED}❌ FAILED${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  Type Checking: ${ORANGE}⚠️  NO RESULTS${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check build status
check_build_status() {
    local build_file="$1"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$build_file" ]; then
        if grep -q "BUILD SUCCESS\|✅\|PASSED" "$build_file"; then
            echo -e "  Build: ${GREEN}✅ PASSED${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  Build: ${RED}❌ FAILED${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  Build: ${ORANGE}⚠️  NO RESULTS${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check documentation build
check_docs_build() {
    local docs_file="$1"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if [ -f "$docs_file" ]; then
        if grep -q "BUILD SUCCESS\|✅\|PASSED" "$docs_file"; then
            echo -e "  Documentation: ${GREEN}✅ PASSED${NC}"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
            return 0
        else
            echo -e "  Documentation: ${RED}❌ FAILED${NC}"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
            return 1
        fi
    else
        echo -e "  Documentation: ${ORANGE}⚠️  NO RESULTS${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo -e "${YELLOW}Checking test results...${NC}"
check_test_results "Unit Tests" "reports/unit-test-results.xml" "PASSED"
check_test_results "Integration Tests" "reports/integration-test-results.xml" "PASSED"
check_test_results "Performance Tests" "reports/performance-test-results.xml" "PASSED"
check_test_results "Security Tests" "reports/security-test-results.xml" "PASSED"

echo -e "${YELLOW}Checking coverage...${NC}"
check_coverage "reports/coverage/all-coverage.xml" "$COVERAGE_THRESHOLD"

echo -e "${YELLOW}Checking security scan...${NC}"
check_security_scan "reports/security/bandit-report.json" "$SECURITY_THRESHOLD"

echo -e "${YELLOW}Checking code quality...${NC}"
check_linting "reports/linting/lint-results.txt"
check_type_checking "reports/type-checking/type-check-summary.md"

echo -e "${YELLOW}Checking build status...${NC}"
check_build_status "reports/build/build-results.txt"
check_docs_build "reports/docs/docs-build-results.txt"

# Calculate quality score
if [ $TOTAL_CHECKS -gt 0 ]; then
    QUALITY_SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
fi

echo ""
echo -e "${PURPLE}=== QUALITY GATE RESULTS ===${NC}"
echo -e "Total Checks: ${TOTAL_CHECKS}"
echo -e "Passed: ${GREEN}${PASSED_CHECKS}${NC}"
echo -e "Failed: ${RED}${FAILED_CHECKS}${NC}"
echo -e "Quality Score: ${BLUE}${QUALITY_SCORE}%${NC}"

# Generate quality gate report
echo -e "${YELLOW}Generating quality gate report...${NC}"
cat > reports/quality-gate/quality-gate-report.md << EOF
# Quality Gate Report

## Overview
Comprehensive quality gate evaluation results from all CI/CD pipeline stages.

## Quality Gate Thresholds
- **Quality Score**: ${QUALITY_THRESHOLD}%
- **Security Issues**: ${SECURITY_THRESHOLD} (0 = no issues allowed)
- **Test Coverage**: ${COVERAGE_THRESHOLD}%

## Results Summary
- **Total Checks**: ${TOTAL_CHECKS}
- **Passed**: ${PASSED_CHECKS}
- **Failed**: ${FAILED_CHECKS}
- **Quality Score**: ${QUALITY_SCORE}%

## Quality Gate Status
$(if [ $QUALITY_SCORE -ge $QUALITY_THRESHOLD ]; then
    echo "**Status**: 🟢 PASSED - Quality score ${QUALITY_SCORE}% meets threshold ${QUALITY_THRESHOLD}%"
else
    echo "**Status**: 🔴 FAILED - Quality score ${QUALITY_SCORE}% below threshold ${QUALITY_THRESHOLD}%"
fi)

## Detailed Results

### Test Results
- **Unit Tests**: $(if check_test_results "Unit Tests" "reports/unit-test-results.xml" "PASSED" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **Integration Tests**: $(if check_test_results "Integration Tests" "reports/integration-test-results.xml" "PASSED" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **Performance Tests**: $(if check_test_results "Performance Tests" "reports/performance-test-results.xml" "PASSED" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **Security Tests**: $(if check_test_results "Security Tests" "reports/security-test-results.xml" "PASSED" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)

### Code Quality
- **Linting**: $(if check_linting "reports/linting/lint-results.txt" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **Type Checking**: $(if check_type_checking "reports/type-checking/type-check-summary.md" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)

### Build & Documentation
- **Build**: $(if check_build_status "reports/build/build-results.txt" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **Documentation**: $(if check_docs_build "reports/docs/docs-build-results.txt" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)

### Security & Coverage
- **Security Scan**: $(if check_security_scan "reports/security/bandit-report.json" "$SECURITY_THRESHOLD" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **Test Coverage**: $(if check_coverage "reports/coverage/all-coverage.xml" "$COVERAGE_THRESHOLD" >/dev/null; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)

## Recommendations
$(if [ $QUALITY_SCORE -ge $QUALITY_THRESHOLD ]; then
    echo "- 🎉 Quality gate passed! Maintain current standards."
    echo "- Continue monitoring quality metrics"
    echo "- Consider raising thresholds for continuous improvement"
else
    echo "- 🔧 Quality gate failed! Address failed checks:"
    echo "  - Review failed tests and fix issues"
    echo "  - Address code quality problems"
    echo "  - Fix security vulnerabilities"
    echo "  - Improve test coverage"
    echo "- Re-run quality gate after fixes"
fi)

## Generated: $(date)
EOF

# Determine final status
if [ $QUALITY_SCORE -ge $QUALITY_THRESHOLD ]; then
    echo -e "${GREEN}🎉 QUALITY GATE PASSED!${NC}"
    echo -e "Quality score ${QUALITY_SCORE}% meets threshold ${QUALITY_THRESHOLD}%"
    FINAL_EXIT=0
else
    echo -e "${RED}❌ QUALITY GATE FAILED!${NC}"
    echo -e "Quality score ${QUALITY_SCORE}% below threshold ${QUALITY_THRESHOLD}%"
    FINAL_EXIT=1
fi

echo -e "${BLUE}📋 Quality gate report: reports/quality-gate/quality-gate-report.md${NC}"

exit $FINAL_EXIT