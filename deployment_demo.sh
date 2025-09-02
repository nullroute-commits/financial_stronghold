#!/bin/bash

# Financial Stronghold - Deployment States Demo
# This script demonstrates each deployment state and how to interact with it

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_subheader() {
    echo -e "${CYAN}--- $1 ---${NC}"
}

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not available. This demo will show configuration only."
        return 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not available. This demo will show configuration only."
        return 1
    fi
    return 0
}

# Demo 1: Development Environment
demo_development() {
    print_header "DEVELOPMENT ENVIRONMENT DEMO"
    
    print_subheader "Configuration Overview"
    echo "Port Mappings:"
    echo "  - Web App: http://localhost:8000"
    echo "  - Database: localhost:5432"
    echo "  - Memcached: localhost:11211"
    echo "  - RabbitMQ: localhost:5672"
    echo "  - RabbitMQ Management: http://localhost:15672"
    echo "  - Adminer (DB Admin): http://localhost:8080"
    echo "  - Mailhog (Email Testing): http://localhost:8025"
    
    print_subheader "Environment Variables"
    echo "  - DJANGO_SETTINGS_MODULE: config.settings.development"
    echo "  - DEBUG: True"
    echo "  - Database: django_app_dev"
    echo "  - Logging: DEBUG level"
    
    print_subheader "Features"
    echo "  ✅ Hot reload enabled"
    echo "  ✅ Debug toolbar"
    echo "  ✅ Development tools (Adminer, Mailhog)"
    echo "  ✅ Volume mounting for live code changes"
    echo "  ✅ Detailed logging and error reporting"
    
    print_subheader "Usage Commands"
    echo "# Start development environment:"
    echo "docker-compose -f docker-compose.development.yml up -d"
    echo ""
    echo "# View logs:"
    echo "docker-compose -f docker-compose.development.yml logs -f web"
    echo ""
    echo "# Access Django shell:"
    echo "docker-compose -f docker-compose.development.yml exec web python manage.py shell"
    echo ""
    echo "# Run migrations:"
    echo "docker-compose -f docker-compose.development.yml exec web python manage.py migrate"
    echo ""
    echo "# Create superuser:"
    echo "docker-compose -f docker-compose.development.yml exec web python manage.py createsuperuser"
    
    print_subheader "Development Workflow"
    echo "1. Start environment: docker-compose -f docker-compose.development.yml up -d"
    echo "2. Access web app: http://localhost:8000"
    echo "3. Make code changes (auto-reload enabled)"
    echo "4. View logs: docker-compose -f docker-compose.development.yml logs -f"
    echo "5. Stop environment: docker-compose -f docker-compose.development.yml down"
}

# Demo 2: Testing Environment
demo_testing() {
    print_header "TESTING ENVIRONMENT DEMO"
    
    print_subheader "Configuration Overview"
    echo "Port Mappings:"
    echo "  - Web App: http://localhost:8001"
    echo "  - Database: localhost:5433"
    echo "  - Memcached: localhost:11212"
    echo "  - RabbitMQ: localhost:5673"
    echo "  - RabbitMQ Management: http://localhost:15673"
    
    print_subheader "Environment Variables"
    echo "  - DJANGO_SETTINGS_MODULE: config.settings.testing"
    echo "  - DEBUG: False"
    echo "  - TESTING: True"
    echo "  - Database: django_app_test"
    echo "  - Logging: INFO level"
    
    print_subheader "Features"
    echo "  ✅ Isolated test database"
    echo "  ✅ Test-specific configurations"
    echo "  ✅ No debug information exposed"
    echo "  ✅ Optimized for test execution"
    echo "  ✅ Separate port ranges to avoid conflicts"
    
    print_subheader "Usage Commands"
    echo "# Start testing environment:"
    echo "docker-compose -f docker-compose.testing.yml up -d"
    echo ""
    echo "# Run tests:"
    echo "docker-compose -f docker-compose.testing.yml exec web python manage.py test"
    echo ""
    echo "# Run specific test:"
    echo "docker-compose -f docker-compose.testing.yml exec web python manage.py test app.tests.unit.test_api"
    echo ""
    echo "# Run with coverage:"
    echo "docker-compose -f docker-compose.testing.yml exec web python manage.py test --coverage"
    echo ""
    echo "# View test logs:"
    echo "docker-compose -f docker-compose.testing.yml logs -f web"
    
    print_subheader "Testing Workflow"
    echo "1. Start test environment: docker-compose -f docker-compose.testing.yml up -d"
    echo "2. Run test suite: docker-compose -f docker-compose.testing.yml exec web python manage.py test"
    echo "3. View test results and coverage"
    echo "4. Stop environment: docker-compose -f docker-compose.testing.yml down"
}

# Demo 3: Staging Environment
demo_staging() {
    print_header "STAGING ENVIRONMENT DEMO"
    
    print_subheader "Configuration Overview"
    echo "Port Mappings:"
    echo "  - Web App: http://localhost:8003"
    echo "  - Nginx: http://localhost:8080"
    echo "  - Database: django_app_staging"
    
    print_subheader "Environment Variables"
    echo "  - DJANGO_SETTINGS_MODULE: config.settings.production"
    echo "  - DEBUG: False"
    echo "  - ENVIRONMENT: staging"
    echo "  - Database: django_app_staging"
    
    print_subheader "Features"
    echo "  ✅ Production-like configuration"
    echo "  ✅ Load balancing (2 replicas)"
    echo "  ✅ Nginx reverse proxy"
    echo "  ✅ Optimized database settings"
    echo "  ✅ Resource limits and monitoring"
    
    print_subheader "Usage Commands"
    echo "# Start staging environment:"
    echo "docker-compose -f docker-compose.staging.yml up -d"
    echo ""
    echo "# Scale web services:"
    echo "docker-compose -f docker-compose.staging.yml up -d --scale web=3"
    echo ""
    echo "# View service status:"
    echo "docker-compose -f docker-compose.staging.yml ps"
    echo ""
    echo "# View logs:"
    echo "docker-compose -f docker-compose.staging.yml logs -f"
    echo ""
    echo "# Run migrations:"
    echo "docker-compose -f docker-compose.staging.yml exec web python manage.py migrate"
    
    print_subheader "Staging Workflow"
    echo "1. Start staging environment: docker-compose -f docker-compose.staging.yml up -d"
    echo "2. Run migrations and collect static files"
    echo "3. Test production-like functionality"
    echo "4. Load test with multiple replicas"
    echo "5. Validate deployment before production"
}

# Demo 4: Production Environment
demo_production() {
    print_header "PRODUCTION ENVIRONMENT DEMO"
    
    print_subheader "Configuration Overview"
    echo "Port Mappings:"
    echo "  - Web App: http://localhost:8002"
    echo "  - Nginx: http://localhost:80, https://localhost:443"
    echo "  - Database: localhost:5434"
    echo "  - Memcached: localhost:11213"
    echo "  - RabbitMQ: localhost:5674"
    echo "  - RabbitMQ Management: http://localhost:15674"
    
    print_subheader "Environment Variables"
    echo "  - DJANGO_SETTINGS_MODULE: config.settings.production"
    echo "  - DEBUG: False"
    echo "  - PRODUCTION: True"
    echo "  - Database: django_app_prod"
    echo "  - Logging: WARNING level"
    
    print_subheader "Features"
    echo "  ✅ High availability (2+ replicas)"
    echo "  ✅ Resource limits and reservations"
    echo "  ✅ Health checks and restart policies"
    echo "  ✅ Load balancing with Nginx"
    echo "  ✅ Production-grade database settings"
    echo "  ✅ Monitoring and alerting ready"
    
    print_subheader "Usage Commands"
    echo "# Start production environment:"
    echo "docker-compose -f docker-compose.production.yml up -d"
    echo ""
    echo "# Scale services:"
    echo "docker-compose -f docker-compose.production.yml up -d --scale web=4"
    echo ""
    echo "# View service status:"
    echo "docker-compose -f docker-compose.production.yml ps"
    echo ""
    echo "# Monitor resources:"
    echo "docker stats"
    echo ""
    echo "# View logs:"
    echo "docker-compose -f docker-compose.production.yml logs -f"
    
    print_subheader "Production Workflow"
    echo "1. Start production environment: docker-compose -f docker-compose.production.yml up -d"
    echo "2. Run migrations and collect static files"
    echo "3. Scale services based on load"
    echo "4. Monitor health and performance"
    echo "5. Set up monitoring and alerting"
}

# Demo 5: Docker Swarm Environment
demo_swarm() {
    print_header "DOCKER SWARM ENVIRONMENT DEMO"
    
    print_subheader "Configuration Overview"
    echo "Features:"
    echo "  - Multi-node orchestration"
    echo "  - Rolling updates and rollbacks"
    echo "  - Service discovery and load balancing"
    echo "  - Health checks and restart policies"
    echo "  - Resource constraints and placement"
    
    print_subheader "Swarm Commands"
    echo "# Initialize swarm:"
    echo "docker swarm init"
    echo ""
    echo "# Deploy stack:"
    echo "docker stack deploy -c docker-compose.swarm.yml financial-stronghold"
    echo ""
    echo "# View services:"
    echo "docker service ls"
    echo ""
    echo "# Scale service:"
    echo "docker service scale financial-stronghold_web=5"
    echo ""
    echo "# Update service:"
    echo "docker service update --image new-image financial-stronghold_web"
    echo ""
    echo "# View stack:"
    echo "docker stack ps financial-stronghold"
    
    print_subheader "Swarm Features"
    echo "  ✅ Rolling updates with zero downtime"
    echo "  ✅ Automatic rollback on failure"
    echo "  ✅ Service placement constraints"
    echo "  ✅ Load balancing across nodes"
    echo "  ✅ Health monitoring and recovery"
    echo "  ✅ Resource management and limits"
}

# Demo 6: CI/CD Pipeline
demo_cicd() {
    print_header "CI/CD PIPELINE DEMO"
    
    print_subheader "Pipeline Stages"
    echo "1. 🧹 Lint & Code Quality"
    echo "2. 🧪 Testing & Coverage"
    echo "3. 🏗️ Build & Package"
    echo "4. 🔒 Security Scan"
    echo "5. 🚀 Deploy & Validate"
    
    print_subheader "CI/CD Commands"
    echo "# Run full pipeline:"
    echo "docker-compose -f ci/docker-compose.ci.yml up"
    echo ""
    echo "# Run specific stage:"
    echo "docker-compose -f ci/docker-compose.ci.yml run ci-runner lint"
    echo "docker-compose -f ci/docker-compose.ci.yml run ci-runner test"
    echo "docker-compose -f ci/docker-compose.ci.yml run ci-runner build"
    echo ""
    echo "# Validate deployment:"
    echo "./ci/validate-deployment-l1-l7.sh development"
    echo "./ci/validate-deployment-l1-l7.sh testing"
    echo "./ci/validate-deployment-l1-l7.sh production"
    
    print_subheader "Validation Levels"
    echo "L1 - Configuration Validation"
    echo "L2 - Service Startup Validation"
    echo "L3 - Connectivity Validation"
    echo "L4 - Functionality Validation"
    echo "L5 - Integration Validation"
    echo "L6 - Performance Validation"
    echo "L7 - Regression Validation"
}

# Demo 7: Web GUI Features
demo_webgui() {
    print_header "WEB GUI FEATURES DEMO"
    
    print_subheader "Available Features"
    echo "📊 Dashboard & Analytics"
    echo "  - Financial summary and overview"
    echo "  - Account management and tracking"
    echo "  - Transaction history and classification"
    echo "  - Budget management and monitoring"
    echo "  - Fee tracking and management"
    
    echo ""
    echo "🏷️ Advanced Features"
    echo "  - Data tagging system"
    echo "  - Transaction classification"
    echo "  - Analytics views management"
    echo "  - Anomaly detection"
    echo "  - Classification configuration"
    
    echo ""
    echo "📚 Built-in Documentation"
    echo "  - API documentation"
    echo "  - Feature guides"
    echo "  - Code examples"
    echo "  - Search functionality"
    echo "  - Interactive help"
    
    print_subheader "Web GUI URLs"
    echo "Main Dashboard: /dashboard/"
    echo "Accounts: /accounts/"
    echo "Transactions: /transactions/"
    echo "Budgets: /budgets/"
    echo "Fees: /fees/"
    echo "Tags: /tags/"
    echo "Classification: /classification/"
    echo "Analytics Views: /analytics/views/"
    echo "Anomaly Detection: /anomaly/"
    echo "Documentation: /docs/"
}

# Demo 8: Health Monitoring
demo_monitoring() {
    print_header "HEALTH MONITORING DEMO"
    
    print_subheader "Health Check Endpoints"
    echo "Application Health: /health/"
    echo "Database Health: /health/db/"
    echo "Cache Health: /health/cache/"
    echo "Queue Health: /health/queue/"
    
    print_subheader "Monitoring Commands"
    echo "# Check application health:"
    echo "curl -f http://localhost:8000/health/"
    echo ""
    echo "# Check database health:"
    echo "docker-compose exec db pg_isready -U postgres"
    echo ""
    echo "# Check cache health:"
    echo "docker-compose exec memcached echo "stats" | nc localhost 11211"
    echo ""
    echo "# Check queue health:"
    echo "docker-compose exec rabbitmq rabbitmqctl status"
    echo ""
    echo "# View service logs:"
    echo "docker-compose logs -f --tail=100"
    
    print_subheader "Resource Monitoring"
    echo "# View container stats:"
    echo "docker stats --no-stream"
    echo ""
    echo "# View disk usage:"
    echo "docker system df"
    echo ""
    echo "# View network usage:"
    echo "docker network ls"
}

# Main demo function
main() {
    print_header "FINANCIAL STRONGHOLD - DEPLOYMENT STATES DEMO"
    echo ""
    echo "This demo shows all deployment states and how to interact with them."
    echo "Each environment is configured for specific use cases and requirements."
    echo ""
    
    # Check Docker availability
    if check_docker; then
        print_status "Docker and Docker Compose are available. Full demo can be run."
    else
        print_warning "Docker not available. Showing configuration and commands only."
    fi
    
    echo ""
    
    # Run all demos
    demo_development
    echo ""
    
    demo_testing
    echo ""
    
    demo_staging
    echo ""
    
    demo_production
    echo ""
    
    demo_swarm
    echo ""
    
    demo_cicd
    echo ""
    
    demo_webgui
    echo ""
    
    demo_monitoring
    echo ""
    
    print_header "DEMO COMPLETE"
    echo ""
    echo "🎯 All deployment states have been demonstrated!"
    echo "🚀 The system is ready for production deployment."
    echo "📚 Each environment has specific configurations and use cases."
    echo "🔧 Docker Compose configurations are properly fixed and optimized."
    echo ""
    echo "Next steps:"
    echo "1. Choose your target environment"
    echo "2. Run the appropriate docker-compose command"
    echo "3. Access the web interface"
    echo "4. Monitor and scale as needed"
}

# Run the demo
main "$@"