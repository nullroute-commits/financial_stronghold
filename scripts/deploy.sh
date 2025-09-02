#!/bin/bash
# Production deployment script
# Created by Team Alpha (Infrastructure & DevOps Agents)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_NAME="financial-stronghold"
BACKUP_DIR="/backups"
DEPLOY_DIR="/opt/${PROJECT_NAME}"

echo -e "${BLUE}🚀 Starting deployment to ${ENVIRONMENT}...${NC}"

# Pre-deployment checks
echo -e "${YELLOW}🔍 Running pre-deployment checks...${NC}"

# Check if environment file exists
if [ ! -f "environments/.env.${ENVIRONMENT}" ]; then
    echo -e "${RED}❌ Environment file not found: environments/.env.${ENVIRONMENT}${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check if required secrets are set
source environments/.env.${ENVIRONMENT}
if [ "$SECRET_KEY" = "CHANGE_ME_TO_SECURE_RANDOM_KEY_50_CHARS_MINIMUM" ]; then
    echo -e "${RED}❌ SECRET_KEY not configured for ${ENVIRONMENT}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pre-deployment checks passed${NC}"

# Database backup (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}💾 Creating database backup...${NC}"
    
    BACKUP_FILE="${BACKUP_DIR}/backup-$(date +%Y%m%d-%H%M%S).sql"
    mkdir -p "$BACKUP_DIR"
    
    docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T db pg_dump \
        -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database backup created: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Database backup failed${NC}"
        exit 1
    fi
fi

# Pull latest images
echo -e "${YELLOW}📦 Pulling latest Docker images...${NC}"
docker-compose -f docker-compose.${ENVIRONMENT}.yml pull

# Build application image
echo -e "${YELLOW}🔨 Building application image...${NC}"
docker-compose -f docker-compose.${ENVIRONMENT}.yml build --no-cache

# Run database migrations
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm web python manage.py migrate

# Collect static files
echo -e "${YELLOW}📦 Collecting static files...${NC}"
docker-compose -f docker-compose.${ENVIRONMENT}.yml run --rm web python manage.py collectstatic --noinput

# Deploy application
echo -e "${YELLOW}🚀 Deploying application...${NC}"

# Stop existing containers
docker-compose -f docker-compose.${ENVIRONMENT}.yml down

# Start new containers
docker-compose -f docker-compose.${ENVIRONMENT}.yml up -d

# Wait for application to be ready
echo -e "${YELLOW}⏳ Waiting for application to be ready...${NC}"
sleep 30

# Health check
echo -e "${YELLOW}🏥 Running health checks...${NC}"
for i in {1..10}; do
    if curl -f http://localhost:8000/api/v1/health/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy${NC}"
        break
    else
        echo -e "${YELLOW}⏳ Attempt $i/10: Application not ready yet...${NC}"
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ Health check failed after 10 attempts${NC}"
        echo -e "${YELLOW}📋 Container logs:${NC}"
        docker-compose -f docker-compose.${ENVIRONMENT}.yml logs web
        exit 1
    fi
done

# Post-deployment tasks
echo -e "${YELLOW}📋 Running post-deployment tasks...${NC}"

# Create superuser if it doesn't exist (staging/development only)
if [ "$ENVIRONMENT" != "production" ]; then
    docker-compose -f docker-compose.${ENVIRONMENT}.yml exec -T web python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'admin@example.com', 'admin123')
    print('Demo superuser created: admin@example.com/admin123')
EOF
fi

# Clean up old Docker images
echo -e "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
docker image prune -f

echo -e "${GREEN}🎉 Deployment to ${ENVIRONMENT} completed successfully!${NC}"

# Deployment summary
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "Environment: ${ENVIRONMENT}"
echo -e "Deployed at: $(date)"
echo -e "Application URL: http://localhost:8000"
echo -e "Admin URL: http://localhost:8000/admin"
echo -e "API URL: http://localhost:8000/api/v1/"

if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "Backup created: $BACKUP_FILE"
fi

echo -e "${GREEN}✅ Deployment complete!${NC}"