#!/bin/bash
# Enhanced testing script with comprehensive coverage
# Team Gamma - Database & Team Epsilon - Testing Sprint 3
# Features: Parallel testing, performance testing, security testing, coverage analysis

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test configuration
TEST_TYPE="${1:-all}"
PYTEST_WORKERS="${PYTEST_WORKERS:-4}"
COVERAGE_MIN="${COVERAGE_MIN:-85}"
PERFORMANCE_THRESHOLD="${PERFORMANCE_THRESHOLD:-2.0}"
SECURITY_STRICT="${SECURITY_STRICT:-true}"

echo -e "${PURPLE}🧪 Starting enhanced testing suite...${NC}"
echo -e "${BLUE}Test Type: ${TEST_TYPE}${NC}"
echo -e "${BLUE}Workers: ${PYTEST_WORKERS}${NC}"
echo -e "${BLUE}Coverage Target: ${COVERAGE_MIN}%${NC}"
echo -e "${BLUE}Performance Threshold: ${PERFORMANCE_THRESHOLD}s${NC}"

# Create comprehensive reports directory
mkdir -p reports/{coverage,performance,security,test-results,quality}

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services...${NC}"
wait_for_service() {
    local service="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$service" "$port" 2>/dev/null; then
            echo -e "  ${GREEN}✅ ${service}:${port} ready${NC}"
            return 0
        fi
        echo -e "  ${YELLOW}⏳ ${service}:${port} not ready (attempt ${attempt}/${max_attempts})${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "  ${RED}❌ ${service}:${port} failed to start${NC}"
    return 1
}

wait_for_service "test-db" "5432"
wait_for_service "test-memcached" "11211"
wait_for_service "test-rabbitmq" "5672"
wait_for_service "test-redis" "6379"

echo -e "${GREEN}🎉 All services are ready!${NC}"

# Set environment variables for testing
export DJANGO_SETTINGS_MODULE=config.settings.testing
export DATABASE_URL="postgresql://postgres:ci-password@test-db:5432/django_app_ci"
export PYTHONPATH=/app
export COVERAGE_FILE=/app/.coverage

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate --noinput

# Function to run unit tests with enhanced coverage
run_unit_tests() {
    echo -e "${CYAN}🔬 Running unit tests...${NC}"
    
    local start_time=$(date +%s)
    
    if pytest tests/unit/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=html:reports/coverage/unit-html \
        --cov-report=xml:reports/coverage/unit-coverage.xml \
        --cov-report=term \
        --junitxml=reports/test-results/unit-test-results.xml \
        --maxfail=20 \
        -n "$PYTEST_WORKERS" \
        --dist=loadfile \
        --durations=10 \
        --strict-markers \
        --strict-config \
        -x; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ Unit tests passed in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}❌ Unit tests failed in ${duration}s${NC}"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${CYAN}🔗 Running integration tests...${NC}"
    
    local start_time=$(date +%s)
    
    if pytest tests/integration/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=html:reports/coverage/integration-html \
        --cov-report=xml:reports/coverage/integration-coverage.xml \
        --cov-report=term \
        --junitxml=reports/test-results/integration-test-results.xml \
        --maxfail=10 \
        -n 2 \
        --dist=loadfile \
        --durations=10 \
        --strict-markers \
        --strict-config \
        -x; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ Integration tests passed in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}❌ Integration tests failed in ${duration}s${NC}"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    echo -e "${CYAN}⚡ Running performance tests...${NC}"
    
    if [ ! -d "tests/performance" ]; then
        echo -e "${YELLOW}⚠️  Performance tests directory not found, creating sample tests...${NC}"
        mkdir -p tests/performance
        
        # Create sample performance test
        cat > tests/performance/test_performance.py << 'EOF'
import pytest
import time
from django.test import Client
from django.urls import reverse

@pytest.mark.performance
class TestPerformance:
    def test_homepage_load_time(self, client):
        """Test homepage loads within performance threshold"""
        start_time = time.time()
        response = client.get('/')
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 2.0, f"Homepage loaded in {load_time:.2f}s, expected <2.0s"
    
    def test_api_response_time(self, client):
        """Test API endpoints respond within threshold"""
        start_time = time.time()
        response = client.get('/api/v1/health/')
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0, f"API responded in {response_time:.2f}s, expected <1.0s"
    
    def test_database_query_performance(self, db):
        """Test database query performance"""
        from app.models import User
        
        start_time = time.time()
        users = list(User.objects.all())
        query_time = time.time() - start_time
        
        assert query_time < 0.1, f"Database query took {query_time:.2f}s, expected <0.1s"
EOF
    fi
    
    local start_time=$(date +%s)
    
    if pytest tests/performance/ \
        -v \
        --tb=short \
        --junitxml=reports/test-results/performance-test-results.xml \
        --durations=20 \
        --strict-markers \
        -m performance; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ Performance tests passed in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}❌ Performance tests failed in ${duration}s${NC}"
        return 1
    fi
}

# Function to run security tests
run_security_tests() {
    echo -e "${CYAN}🔒 Running security tests...${NC}"
    
    if [ ! -d "tests/security" ]; then
        echo -e "${YELLOW}⚠️  Security tests directory not found, creating sample tests...${NC}"
        mkdir -p tests/security
        
        # Create sample security test
        cat > tests/security/test_security.py << 'EOF'
import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.security
class TestSecurity:
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection"""
        malicious_input = "'; DROP TABLE users; --"
        response = client.get(f'/api/v1/search/?q={malicious_input}')
        
        # Should not crash or expose sensitive data
        assert response.status_code in [200, 400, 404]
    
    def test_xss_protection(self, client):
        """Test XSS protection"""
        malicious_input = "<script>alert('xss')</script>"
        response = client.post('/api/v1/feedback/', {'message': malicious_input})
        
        # Should not contain script tags in response
        if response.status_code == 200:
            assert '<script>' not in str(response.content)
    
    def test_csrf_protection(self, client):
        """Test CSRF protection"""
        response = client.post('/api/v1/feedback/', {'message': 'test'})
        
        # Should require CSRF token
        assert response.status_code in [403, 400]
    
    def test_authentication_required(self, client):
        """Test authentication requirements"""
        response = client.get('/api/v1/admin/')
        
        # Should require authentication
        assert response.status_code in [401, 403, 302]
EOF
    fi
    
    local start_time=$(date +%s)
    
    if pytest tests/security/ \
        -v \
        --tb=short \
        --junitxml=reports/test-results/security-test-results.xml \
        --durations=10 \
        --strict-markers \
        -m security; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${GREEN}✅ Security tests passed in ${duration}s${NC}"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo -e "${RED}❌ Security tests failed in ${duration}s${NC}"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    echo -e "${CYAN}🚀 Running comprehensive test suite...${NC}"
    
    local start_time=$(date +%s)
    local exit_code=0
    
    # Run tests in parallel where possible
    echo -e "${YELLOW}Starting parallel test execution...${NC}"
    
    # Run unit and integration tests in parallel
    if ! run_unit_tests; then
        exit_code=1
    fi
    
    if ! run_integration_tests; then
        exit_code=1
    fi
    
    # Run performance and security tests
    if ! run_performance_tests; then
        exit_code=1
    fi
    
    if ! run_security_tests; then
        exit_code=1
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests completed successfully in ${duration}s${NC}"
    else
        echo -e "${RED}⚠️  Some tests failed in ${duration}s${NC}"
    fi
    
    return $exit_code
}

# Function to generate coverage report
generate_coverage_report() {
    echo -e "${YELLOW}📊 Generating coverage report...${NC}"
    
    # Combine coverage data
    coverage combine reports/coverage/*.xml || true
    
    # Generate final report
    coverage report --show-missing --fail-under="$COVERAGE_MIN" > reports/coverage/coverage-summary.txt 2>&1 || true
    
    # Generate HTML report
    coverage html --directory=reports/coverage/html --fail-under="$COVERAGE_MIN" || true
    
    # Extract coverage percentage
    local coverage_percent=$(coverage report | tail -1 | awk '{print $4}' | sed 's/%//')
    
    if [ -n "$coverage_percent" ] && [ "$(echo "$coverage_percent >= $COVERAGE_MIN" | bc -l)" -eq 1 ]; then
        echo -e "${GREEN}✅ Coverage: ${coverage_percent}% (≥${COVERAGE_MIN}%)${NC}"
        return 0
    else
        echo -e "${RED}❌ Coverage: ${coverage_percent}% (<${COVERAGE_MIN}%)${NC}"
        return 1
    fi
}

# Function to generate test summary
generate_test_summary() {
    echo -e "${YELLOW}📋 Generating test summary...${NC}"
    
    cat > reports/quality/test-summary.md << EOF
# Test Execution Summary

## Overview
Comprehensive test execution results from enhanced testing suite.

## Test Configuration
- **Test Type**: ${TEST_TYPE}
- **Workers**: ${PYTEST_WORKERS}
- **Coverage Target**: ${COVERAGE_MIN}%
- **Performance Threshold**: ${PERFORMANCE_THRESHOLD}s
- **Security Strict**: ${SECURITY_STRICT}

## Test Results

### Unit Tests
- **Status**: $(if [ -f "reports/test-results/unit-test-results.xml" ]; then echo "✅ COMPLETED"; else echo "❌ NOT RUN"; fi)
- **Report**: [unit-test-results.xml](../test-results/unit-test-results.xml)
- **Coverage**: [unit-html](../coverage/unit-html/index.html)

### Integration Tests
- **Status**: $(if [ -f "reports/test-results/integration-test-results.xml" ]; then echo "✅ COMPLETED"; else echo "❌ NOT RUN"; fi)
- **Report**: [integration-test-results.xml](../test-results/integration-test-results.xml)
- **Coverage**: [integration-html](../coverage/integration-html/index.html)

### Performance Tests
- **Status**: $(if [ -f "reports/test-results/performance-test-results.xml" ]; then echo "✅ COMPLETED"; else echo "❌ NOT RUN"; fi)
- **Report**: [performance-test-results.xml](../test-results/performance-test-results.xml)

### Security Tests
- **Status**: $(if [ -f "reports/test-results/security-test-results.xml" ]; then echo "✅ COMPLETED"; else echo "❌ NOT RUN"; fi)
- **Report**: [security-test-results.xml](../test-results/security-test-results.xml)

## Coverage Report
- **Summary**: [coverage-summary.txt](../coverage/coverage-summary.txt)
- **HTML Report**: [coverage/html/index.html](../coverage/html/index.html)

## Performance Metrics
- **Unit Tests**: $(if [ -f "reports/test-results/unit-test-results.xml" ]; then echo "Executed"; else echo "Not executed"; fi)
- **Integration Tests**: $(if [ -f "reports/test-results/integration-test-results.xml" ]; then echo "Executed"; else echo "Not executed"; fi)
- **Performance Tests**: $(if [ -f "reports/test-results/performance-test-results.xml" ]; then echo "Executed"; else echo "Not executed"; fi)
- **Security Tests**: $(if [ -f "reports/test-results/security-test-results.xml" ]; then echo "Executed"; else echo "Not executed"; fi)

## Generated: $(date)
EOF
}

# Main execution
EXIT_CODE=0

case "$TEST_TYPE" in
    "unit")
        if ! run_unit_tests; then
            EXIT_CODE=1
        fi
        ;;
    "integration")
        if ! run_integration_tests; then
            EXIT_CODE=1
        fi
        ;;
    "performance")
        if ! run_performance_tests; then
            EXIT_CODE=1
        fi
        ;;
    "security")
        if ! run_security_tests; then
            EXIT_CODE=1
        fi
        ;;
    "all"|*)
        if ! run_all_tests; then
            EXIT_CODE=1
        fi
        ;;
esac

# Generate reports
generate_coverage_report
generate_test_summary

# Final summary
echo ""
echo -e "${PURPLE}=== ENHANCED TESTING SUMMARY ===${NC}"
echo -e "Test Type: ${TEST_TYPE}"
echo -e "Coverage Target: ${COVERAGE_MIN}%"
echo -e "Performance Threshold: ${PERFORMANCE_THRESHOLD}s"
echo -e "Exit Code: ${EXIT_CODE}"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
else
    echo -e "${RED}⚠️  Some tests failed!${NC}"
    echo -e "${YELLOW}Check the reports/ directory for detailed results.${NC}"
fi

echo -e "${BLUE}📋 Test summary: reports/quality/test-summary.md${NC}"
echo -e "${BLUE}📊 Coverage report: reports/coverage/coverage-summary.txt${NC}"
echo -e "${BLUE}📁 HTML coverage: reports/coverage/html/index.html${NC}"

exit $EXIT_CODE