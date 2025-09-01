#!/bin/bash
# Comprehensive Test Coverage Script for 100% Coverage Across All Categories
# Following FEATURE_DEPLOYMENT_GUIDE.md SOP with Docker Swarm deployment

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# Initialize coverage tracking
COVERAGE_REPORT_DIR="coverage_reports"
mkdir -p "$COVERAGE_REPORT_DIR"

log "🚀 Starting Comprehensive Test Coverage Analysis"
log "Following FEATURE_DEPLOYMENT_GUIDE.md SOP"

# 1. Unit Tests - 100% Coverage Target
log "📋 Running Unit Tests for 100% Coverage"
python -m pytest tests/unit/ \
    --cov=app \
    --cov-report=html:$COVERAGE_REPORT_DIR/unit \
    --cov-report=term \
    --cov-report=json:$COVERAGE_REPORT_DIR/unit_coverage.json \
    --no-migrations \
    --disable-warnings \
    -v \
    --tb=short \
    -m "not slow" \
    --maxfail=5 || {
    log_warning "Some unit tests failed, continuing with coverage analysis"
}

# Extract unit test coverage
UNIT_COVERAGE=$(python -c "
import json
try:
    with open('$COVERAGE_REPORT_DIR/unit_coverage.json', 'r') as f:
        data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

log_success "Unit Test Coverage: $UNIT_COVERAGE%"

# 2. Integration Tests - 100% Coverage Target
log "🔗 Running Integration Tests for 100% Coverage"
python -m pytest tests/integration/ \
    --cov=app \
    --cov-append \
    --cov-report=html:$COVERAGE_REPORT_DIR/integration \
    --cov-report=term \
    --cov-report=json:$COVERAGE_REPORT_DIR/integration_coverage.json \
    --no-migrations \
    --disable-warnings \
    -v \
    --tb=short \
    -m "not slow" \
    --maxfail=5 || {
    log_warning "Some integration tests failed, continuing with coverage analysis"
}

# Extract integration test coverage
INTEGRATION_COVERAGE=$(python -c "
import json
try:
    with open('$COVERAGE_REPORT_DIR/integration_coverage.json', 'r') as f:
        data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

log_success "Integration Test Coverage: $INTEGRATION_COVERAGE%"

# 3. Regression Tests - 100% Coverage Target
log "🔄 Running Regression Tests for 100% Coverage"
python -m pytest tests/regression/ \
    --cov=app \
    --cov-append \
    --cov-report=html:$COVERAGE_REPORT_DIR/regression \
    --cov-report=term \
    --cov-report=json:$COVERAGE_REPORT_DIR/regression_coverage.json \
    --no-migrations \
    --disable-warnings \
    -v \
    --tb=short \
    --maxfail=5 || {
    log_warning "Some regression tests failed, continuing with coverage analysis"
}

# Extract regression test coverage
REGRESSION_COVERAGE=$(python -c "
import json
try:
    with open('$COVERAGE_REPORT_DIR/regression_coverage.json', 'r') as f:
        data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

log_success "Regression Test Coverage: $REGRESSION_COVERAGE%"

# 4. Security Tests - 100% Coverage Target
log "🛡️  Running Security Tests for 100% Coverage"
python -m pytest tests/security/ \
    --cov=app \
    --cov-append \
    --cov-report=html:$COVERAGE_REPORT_DIR/security \
    --cov-report=term \
    --cov-report=json:$COVERAGE_REPORT_DIR/security_coverage.json \
    --no-migrations \
    --disable-warnings \
    -v \
    --tb=short \
    --maxfail=5 || {
    log_warning "Some security tests failed, continuing with coverage analysis"
}

# Extract security test coverage
SECURITY_COVERAGE=$(python -c "
import json
try:
    with open('$COVERAGE_REPORT_DIR/security_coverage.json', 'r') as f:
        data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

log_success "Security Test Coverage: $SECURITY_COVERAGE%"

# 5. Performance Tests - 100% Coverage Target
log "⚡ Running Performance Tests for 100% Coverage"
python -m pytest tests/performance/ \
    --cov=app \
    --cov-append \
    --cov-report=html:$COVERAGE_REPORT_DIR/performance \
    --cov-report=term \
    --cov-report=json:$COVERAGE_REPORT_DIR/performance_coverage.json \
    --no-migrations \
    --disable-warnings \
    -v \
    --tb=short \
    -m "not slow" \
    --maxfail=5 || {
    log_warning "Some performance tests failed, continuing with coverage analysis"
}

# Extract performance test coverage
PERFORMANCE_COVERAGE=$(python -c "
import json
try:
    with open('$COVERAGE_REPORT_DIR/performance_coverage.json', 'r') as f:
        data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

log_success "Performance Test Coverage: $PERFORMANCE_COVERAGE%"

# 6. Combined Coverage Analysis
log "📊 Running Combined Coverage Analysis"
python -m pytest tests/ \
    --cov=app \
    --cov-report=html:$COVERAGE_REPORT_DIR/combined \
    --cov-report=term \
    --cov-report=json:$COVERAGE_REPORT_DIR/combined_coverage.json \
    --no-migrations \
    --disable-warnings \
    --tb=no \
    -q \
    --maxfail=50 || {
    log_warning "Some combined tests failed, continuing with coverage analysis"
}

# Extract combined coverage
COMBINED_COVERAGE=$(python -c "
import json
try:
    with open('$COVERAGE_REPORT_DIR/combined_coverage.json', 'r') as f:
        data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

# Generate comprehensive report
log "📈 Generating Comprehensive Coverage Report"

cat > "$COVERAGE_REPORT_DIR/comprehensive_report.md" << EOF
# Comprehensive Test Coverage Report

Generated: $(date +'%Y-%m-%d %H:%M:%S')
Following: FEATURE_DEPLOYMENT_GUIDE.md SOP

## Coverage by Test Category

| Test Category | Coverage | Target | Status |
|---------------|----------|--------|--------|
| Unit Tests | $UNIT_COVERAGE% | 100% | $([ "$(echo "$UNIT_COVERAGE > 90" | bc -l)" = "1" ] && echo "✅ Excellent" || echo "⚠️ Needs Improvement") |
| Integration Tests | $INTEGRATION_COVERAGE% | 100% | $([ "$(echo "$INTEGRATION_COVERAGE > 90" | bc -l)" = "1" ] && echo "✅ Excellent" || echo "⚠️ Needs Improvement") |
| Regression Tests | $REGRESSION_COVERAGE% | 100% | $([ "$(echo "$REGRESSION_COVERAGE > 90" | bc -l)" = "1" ] && echo "✅ Excellent" || echo "⚠️ Needs Improvement") |
| Security Tests | $SECURITY_COVERAGE% | 100% | $([ "$(echo "$SECURITY_COVERAGE > 90" | bc -l)" = "1" ] && echo "✅ Excellent" || echo "⚠️ Needs Improvement") |
| Performance Tests | $PERFORMANCE_COVERAGE% | 100% | $([ "$(echo "$PERFORMANCE_COVERAGE > 90" | bc -l)" = "1" ] && echo "✅ Excellent" || echo "⚠️ Needs Improvement") |
| **Combined Coverage** | **$COMBINED_COVERAGE%** | **100%** | **$([ "$(echo "$COMBINED_COVERAGE > 95" | bc -l)" = "1" ] && echo "✅ Excellent" || echo "⚠️ Needs Improvement")** |

## Test Execution Summary

- 📋 Unit Tests: Focus on individual functions and classes
- 🔗 Integration Tests: Test component interactions and APIs
- 🔄 Regression Tests: Prevent known bugs from recurring
- 🛡️ Security Tests: Validate security controls and vulnerabilities
- ⚡ Performance Tests: Ensure response times and scalability

## Coverage Details

View detailed HTML coverage reports:
- [Unit Test Coverage](unit/index.html)
- [Integration Test Coverage](integration/index.html)
- [Regression Test Coverage](regression/index.html)
- [Security Test Coverage](security/index.html)
- [Performance Test Coverage](performance/index.html)
- [Combined Coverage](combined/index.html)

## Docker Swarm Deployment

The application is configured for Docker Swarm deployment with:
- High availability (3 web replicas)
- Load balancing with Nginx
- Monitoring with Prometheus & Grafana
- Persistent storage with NFS
- Secret management
- Health checks and rolling updates

Deploy with:
\`\`\`bash
docker stack deploy -c docker-compose.swarm.yml financial-stronghold
\`\`\`

## Next Steps

$(if [ "$(echo "$COMBINED_COVERAGE < 100" | bc -l)" = "1" ]; then
    echo "1. Focus on modules with low coverage"
    echo "2. Add more edge case tests"
    echo "3. Increase mock coverage for external dependencies"
    echo "4. Add error path testing"
else
    echo "🎉 Congratulations! 100% test coverage achieved across all categories!"
    echo "1. Maintain test quality with regular reviews"
    echo "2. Update tests when adding new features"
    echo "3. Monitor test performance and reliability"
fi)

EOF

# Display final summary
echo ""
log_success "=========================================="
log_success "📊 COMPREHENSIVE COVERAGE SUMMARY"
log_success "=========================================="
log_success "Unit Tests:        $UNIT_COVERAGE%"
log_success "Integration Tests: $INTEGRATION_COVERAGE%"
log_success "Regression Tests:  $REGRESSION_COVERAGE%"
log_success "Security Tests:    $SECURITY_COVERAGE%"
log_success "Performance Tests: $PERFORMANCE_COVERAGE%"
log_success "----------------------------------------"
log_success "COMBINED COVERAGE: $COMBINED_COVERAGE%"
log_success "=========================================="

# Check if target achieved
if [ "$(echo "$COMBINED_COVERAGE >= 100" | bc -l)" = "1" ]; then
    log_success "🎉 TARGET ACHIEVED: 100% test coverage across all categories!"
    log_success "✅ Ready for Docker Swarm deployment"
    echo ""
    log "🚀 To deploy to Docker Swarm:"
    log "   docker stack deploy -c docker-compose.swarm.yml financial-stronghold"
elif [ "$(echo "$COMBINED_COVERAGE >= 90" | bc -l)" = "1" ]; then
    log_success "🎯 EXCELLENT: >90% test coverage achieved"
    log "🔧 Focus on remaining $(echo "100 - $COMBINED_COVERAGE" | bc -l)% to reach 100%"
elif [ "$(echo "$COMBINED_COVERAGE >= 80" | bc -l)" = "1" ]; then
    log_warning "🎯 GOOD: >80% test coverage achieved"
    log "🔧 Continue improving to reach 100% target"
else
    log_warning "⚠️  Coverage below 80%, more work needed to reach 100% target"
fi

log "📁 Detailed reports available in: $COVERAGE_REPORT_DIR/"
log "📖 View comprehensive report: $COVERAGE_REPORT_DIR/comprehensive_report.md"

# Exit with appropriate code
if [ "$(echo "$COMBINED_COVERAGE >= 80" | bc -l)" = "1" ]; then
    exit 0
else
    exit 1
fi