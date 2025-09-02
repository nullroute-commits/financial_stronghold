#!/bin/bash
# Docker entrypoint script for Django application
# Handles database migrations and application startup
# Created by Team Alpha (Infrastructure & DevOps)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Django application...${NC}"

# Wait for database to be ready
echo -e "${YELLOW}⏳ Waiting for database...${NC}"
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  echo -e "${YELLOW}Database not ready, waiting...${NC}"
  sleep 1
done
echo -e "${GREEN}✅ Database is ready!${NC}"

# Wait for cache to be ready
echo -e "${YELLOW}⏳ Waiting for cache...${NC}"
while ! nc -z ${MEMCACHED_SERVERS%:*} ${MEMCACHED_SERVERS#*:}; do
  echo -e "${YELLOW}Cache not ready, waiting...${NC}"
  sleep 1
done
echo -e "${GREEN}✅ Cache is ready!${NC}"

# Run database migrations
echo -e "${YELLOW}🔄 Running database migrations...${NC}"
python manage.py migrate --noinput

# Collect static files for production
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo -e "${YELLOW}📦 Collecting static files...${NC}"
    python manage.py collectstatic --noinput
fi

# Create superuser if it doesn't exist (development only)
if [ "$DEBUG" = "True" ]; then
    echo -e "${YELLOW}👤 Creating development superuser...${NC}"
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF
fi

echo -e "${GREEN}🎉 Application startup complete!${NC}"

# Execute the main command
exec "$@"