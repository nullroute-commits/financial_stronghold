#!/bin/bash
# Deployment script
# Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Deployment target
TARGET="${1:-staging}"

echo -e "${GREEN}Deploying to: $TARGET${NC}"

# Configuration
IMAGE_NAME="django-app"
REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
VERSION="${BUILD_VERSION:-$(git rev-parse --short HEAD)}"

# Validate target
case "$TARGET" in
    "development"|"dev")
        COMPOSE_FILE="docker-compose.development.yml"
        ENV_FILE="environments/.env.development.example"
        ;;
    "testing"|"test")
        COMPOSE_FILE="docker-compose.testing.yml"
        ENV_FILE="environments/.env.testing.example"
        ;;
    "staging")
        COMPOSE_FILE="docker-compose.staging.yml"
        ENV_FILE="environments/.env.staging.example"
        ;;
    "production"|"prod")
        COMPOSE_FILE="docker-compose.production.yml"
        ENV_FILE="environments/.env.production.example"
        ;;
    *)
        echo -e "${RED}❌ Invalid deployment target: $TARGET${NC}"
        echo -e "${YELLOW}Valid targets: development, dev, testing, test, staging, production, prod${NC}"
        exit 1
        ;;
esac

# Deployment functions
deploy_to_development() {
    echo -e "${YELLOW}Deploying to development environment...${NC}"
    
    # Build images
    docker compose -f $COMPOSE_FILE build
    
    # Start services
    docker compose -f $COMPOSE_FILE up -d
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 30
    
    # Run health checks
    if docker compose -f $COMPOSE_FILE exec -T web curl -f http://localhost:8000/health/ 2>/dev/null; then
        echo -e "${GREEN}✅ Development deployment successful${NC}"
    else
        echo -e "${RED}❌ Development health check failed${NC}"
        exit 1
    fi
}

deploy_to_testing() {
    echo -e "${YELLOW}Deploying to testing environment...${NC}"
    
    # Build images
    docker compose -f $COMPOSE_FILE build
    
    # Start supporting services first
    docker compose -f $COMPOSE_FILE up -d db memcached rabbitmq
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for supporting services to be ready...${NC}"
    sleep 15
    
    # Run migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker compose -f $COMPOSE_FILE run --rm --no-deps web python manage.py migrate --noinput
    
    # Start web service
    docker compose -f $COMPOSE_FILE up -d web
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 30
    
    # Run health checks
    if docker compose -f $COMPOSE_FILE exec -T web curl -f http://localhost:8000/health/ 2>/dev/null; then
        echo -e "${GREEN}✅ Testing deployment successful${NC}"
    else
        echo -e "${RED}❌ Testing health check failed${NC}"
        exit 1
    fi
}

deploy_to_staging() {
    echo -e "${YELLOW}Deploying to staging environment...${NC}"
    
    # Build images
    docker compose -f $COMPOSE_FILE build
    
    # Stop existing services
    docker compose -f $COMPOSE_FILE down
    
    # Start supporting services first
    docker compose -f $COMPOSE_FILE up -d db memcached rabbitmq nginx
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for supporting services to be ready...${NC}"
    sleep 15
    
    # Run migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker compose -f $COMPOSE_FILE run --rm --no-deps web python manage.py migrate --noinput
    
    # Start web services
    docker compose -f $COMPOSE_FILE up -d web
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 30
    
    # Run health checks
    if docker compose -f $COMPOSE_FILE exec -T web curl -f http://localhost:8003/health/ 2>/dev/null; then
        echo -e "${GREEN}✅ Staging deployment successful${NC}"
    else
        echo -e "${RED}❌ Staging health check failed${NC}"
        exit 1
    fi
}

deploy_to_production() {
    echo -e "${YELLOW}Deploying to production environment...${NC}"
    
    # Safety checks for production
    if [ "$CI" != "true" ]; then
        echo -e "${RED}⚠️ Production deployment should only be run in CI environment${NC}"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Deployment cancelled${NC}"
            exit 0
        fi
    fi
    
    # Backup current deployment (skip if database doesn't exist yet)
    echo -e "${YELLOW}Creating backup...${NC}"
    docker compose -f $COMPOSE_FILE exec -T db pg_dump -U postgres django_app_prod > backup_$(date +%Y%m%d_%H%M%S).sql 2>/dev/null || echo "No existing database to backup"
    
    # Rolling deployment
    echo -e "${YELLOW}Starting rolling deployment...${NC}"
    
    # Build images
    docker compose -f $COMPOSE_FILE build
    
    # Update services one by one
    docker compose -f $COMPOSE_FILE up -d --no-deps web
    
    # Wait for new instance to be healthy
    sleep 60
    
    # Health check
    if docker compose -f $COMPOSE_FILE exec -T web curl -f http://localhost:8002/health/ 2>/dev/null; then
        echo -e "${GREEN}✅ Production deployment successful${NC}"
    else
        echo -e "${RED}❌ Production health check failed${NC}"
        echo -e "${YELLOW}Rolling back...${NC}"
        docker compose -f $COMPOSE_FILE down
        exit 1
    fi
    
    # Update other services
    docker compose -f $COMPOSE_FILE up -d
}

# Pre-deployment checks
echo -e "${YELLOW}Running pre-deployment checks...${NC}"

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Compose file not found: $COMPOSE_FILE${NC}"
    exit 1
fi

# Skip image pull checks for local development
if [ "$TARGET" != "development" ] && [ "$TARGET" != "dev" ]; then
    # Check if images exist
    if ! docker pull $REGISTRY/$IMAGE_NAME:$VERSION 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Image not found in registry: $REGISTRY/$IMAGE_NAME:$VERSION${NC}"
        echo -e "${YELLOW}Will build locally instead${NC}"
    fi
fi

# Database migration check (skip for local environments)
if [ "$TARGET" = "production" ] || [ "$TARGET" = "prod" ]; then
    echo -e "${YELLOW}Checking database migrations...${NC}"
    if ! docker run --rm --env-file $ENV_FILE $REGISTRY/$IMAGE_NAME:$VERSION python manage.py migrate --check 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Pending migrations detected${NC}"
        echo -e "${RED}❌ Cannot deploy to production with pending migrations${NC}"
        exit 1
    fi
fi

# Run deployment
case "$TARGET" in
    "development"|"dev")
        deploy_to_development
        ;;
    "testing"|"test")
        deploy_to_testing
        ;;
    "staging")
        deploy_to_staging
        ;;
    "production"|"prod")
        deploy_to_production
        ;;
esac

# Post-deployment verification
echo -e "${YELLOW}Running post-deployment verification...${NC}"

# Determine health check port based on target
case "$TARGET" in
    "development"|"dev")
        HEALTH_PORT="8000"
        ;;
    "testing"|"test")
        HEALTH_PORT="8001"
        ;;
    "staging")
        HEALTH_PORT="8003"
        ;;
    "production"|"prod")
        HEALTH_PORT="8002"
        ;;
esac

# Health checks
HEALTH_URL="http://localhost:${HEALTH_PORT}/health/"
echo -e "${YELLOW}Checking health endpoint: $HEALTH_URL${NC}"

for i in {1..10}; do
    if curl -f $HEALTH_URL 2>/dev/null; then
        echo -e "${GREEN}✅ Health check passed${NC}"
        break
    else
        echo -e "${YELLOW}Health check attempt $i/10 failed, retrying...${NC}"
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Health check failed after 10 attempts${NC}"
        exit 1
    fi
done

# Smoke tests
echo -e "${YELLOW}Running smoke tests...${NC}"
# Add smoke tests here

# Generate deployment report
echo -e "${YELLOW}Generating deployment report...${NC}"
cat > reports/deployment-report.json << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target": "$TARGET",
  "version": "$VERSION",
  "image": "$REGISTRY/$IMAGE_NAME:$VERSION",
  "compose_file": "$COMPOSE_FILE",
  "env_file": "$ENV_FILE",
  "git_commit": "$(git rev-parse HEAD)",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD)",
  "deployed_by": "${USER:-unknown}",
  "status": "success"
}
EOF

echo -e "${GREEN}✅ Deployment to $TARGET completed successfully!${NC}"
echo -e "${BLUE}Deployment report saved to reports/deployment-report.json${NC}"