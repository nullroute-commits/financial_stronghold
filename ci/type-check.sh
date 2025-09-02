#!/bin/bash
# Enhanced type checking script with strict MyPy configuration
# Team Beta - Architecture Sprint 2

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Starting enhanced type checking...${NC}"

# Create reports directory
mkdir -p reports/type-checking

# Set MyPy configuration
export MYPY_CONFIG_FILE_DIR=/app
export PYTHONPATH=/app

# MyPy strict configuration
MYPY_OPTS=(
    --strict
    --disallow-any-explicit
    --disallow-untyped-defs
    --disallow-incomplete-defs
    --check-untyped-defs
    --disallow-untyped-decorators
    --no-implicit-optional
    --warn-redundant-casts
    --warn-unused-ignores
    --warn-return-any
    --warn-unreachable
    --strict-equality
    --show-error-codes
    --show-column-numbers
    --pretty
    --verbose
)

# Check if MyPy is installed
if ! command -v mypy &> /dev/null; then
    echo -e "${YELLOW}Installing MyPy...${NC}"
    pip install mypy[reports] django-stubs
fi

echo -e "${YELLOW}Running MyPy type checking...${NC}"

# Run MyPy on the main application
echo -e "${BLUE}Checking main application...${NC}"
if mypy "${MYPY_OPTS[@]}" app/ > reports/type-checking/app-types.txt 2>&1; then
    echo -e "${GREEN}✅ Main application type checking passed${NC}"
    APP_EXIT=0
else
    echo -e "${RED}❌ Main application type checking failed${NC}"
    APP_EXIT=1
fi

# Run MyPy on configuration
echo -e "${BLUE}Checking configuration...${NC}"
if mypy "${MYPY_OPTS[@]}" config/ > reports/type-checking/config-types.txt 2>&1; then
    echo -e "${GREEN}✅ Configuration type checking passed${NC}"
    CONFIG_EXIT=0
else
    echo -e "${RED}❌ Configuration type checking failed${NC}"
    CONFIG_EXIT=1
fi

# Run MyPy on tests
echo -e "${BLUE}Checking tests...${NC}"
if mypy "${MYPY_OPTS[@]}" tests/ > reports/type-checking/tests-types.txt 2>&1; then
    echo -e "${GREEN}✅ Tests type checking passed${NC}"
    TESTS_EXIT=0
else
    echo -e "${RED}❌ Tests type checking failed${NC}"
    TESTS_EXIT=1
fi

# Generate type checking summary
echo -e "${YELLOW}Generating type checking summary...${NC}"
cat > reports/type-checking/type-check-summary.md << EOF
# Type Checking Summary

## Overview
Type checking results from MyPy with strict configuration.

## Results

### Main Application
- **Status**: $(if [ $APP_EXIT -eq 0 ]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **File**: [app-types.txt](app-types.txt)

### Configuration
- **Status**: $(if [ $CONFIG_EXIT -eq 0 ]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **File**: [config-types.txt](config-types.txt)

### Tests
- **Status**: $(if [ $TESTS_EXIT -eq 0 ]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)
- **File**: [tests-types.txt](tests-types.txt)

## MyPy Configuration
- **Strict Mode**: Enabled
- **Disallow Any Explicit**: Yes
- **Disallow Untyped Defs**: Yes
- **Check Untyped Defs**: Yes
- **No Implicit Optional**: Yes

## Recommendations
$(if [ $APP_EXIT -eq 0 ] && [ $CONFIG_EXIT -eq 0 ] && [ $TESTS_EXIT -eq 0 ]; then
    echo "- All type checking passed! Maintain current type annotation standards."
else
    echo "- Review and fix type annotation issues"
    echo "- Add type hints to untyped functions"
    echo "- Consider using @typing.no_type_check for complex cases"
fi)

## Generated: $(date)
EOF

# Calculate overall exit code
OVERALL_EXIT=$((APP_EXIT + CONFIG_EXIT + TESTS_EXIT))

# Show summary
echo ""
echo -e "${YELLOW}=== TYPE CHECKING SUMMARY ===${NC}"
echo -e "Main Application: $(if [ $APP_EXIT -eq 0 ]; then echo -e "${GREEN}✅ PASSED${NC}"; else echo -e "${RED}❌ FAILED${NC}"; fi)"
echo -e "Configuration: $(if [ $CONFIG_EXIT -eq 0 ]; then echo -e "${GREEN}✅ PASSED${NC}"; else echo -e "${RED}❌ FAILED${NC}"; fi)"
echo -e "Tests: $(if [ $TESTS_EXIT -eq 0 ]; then echo -e "${GREEN}✅ PASSED${NC}"; else echo -e "${RED}❌ FAILED${NC}"; fi)"

if [ $OVERALL_EXIT -eq 0 ]; then
    echo -e "${GREEN}🎉 All type checking passed!${NC}"
else
    echo -e "${RED}⚠️  Some type checking failed. Check reports/type-checking/ for details.${NC}"
fi

echo -e "${BLUE}📋 Detailed reports available in: reports/type-checking/${NC}"

exit $OVERALL_EXIT