# Quick Start Guide

**Project:** Financial Stronghold  
**Target Audience:** Developers  
**Time Required:** 15-30 minutes

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [First Run](#first-run)
4. [Verify Installation](#verify-installation)
5. [Next Steps](#next-steps)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Docker** 24.0.7 or higher ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.18.1 or higher ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git** ([Install Git](https://git-scm.com/downloads))

### Optional (for local development)

- **Python** 3.12.3 ([Download Python](https://www.python.org/downloads/))
- **Node.js** 18+ (for frontend development)
- **PostgreSQL** 17.2 (if running database locally)

### System Requirements

- **OS:** Linux, macOS, or Windows (with WSL2)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 10GB free space
- **Network:** Internet connection for pulling Docker images

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/nullroute-commits/financial_stronghold.git
cd financial_stronghold
```

### Step 2: Verify Python Version

The project uses Python 3.12.3. Verify your Python version:

```bash
python3 --version
# Should output: Python 3.12.3
```

If you have a different version, install Python 3.12.3 or use Docker (recommended).

### Step 3: Verify Docker Installation

```bash
docker --version
# Should output: Docker version 24.0.7 or higher

docker-compose --version
# Should output: Docker Compose version 2.18.1 or higher
```

### Step 4: Configure Environment

The project includes example environment files. For development, the default values work out of the box:

```bash
# Optional: Review environment files
ls -la .env.*

# Files you'll find:
# .env.development    - Development environment (default)
# .env.testing        - Test environment
# .env.production     - Production environment
# .env.example        - Template for custom environments
```

**Note:** For initial setup, you don't need to modify these files. The development environment works with defaults.

---

## First Run

### Option 1: Using Startup Script (Recommended)

The easiest way to start the application:

```bash
./scripts/start-dev.sh
```

This script will:
1. Build Docker images
2. Start all services (database, cache, message queue, application)
3. Run database migrations
4. Create a superuser account
5. Collect static files
6. Display access URLs

**Wait for startup to complete** (usually 30-60 seconds). You'll see:

```
✅ All services started successfully!

Access the application at:
  🌐 Django App: http://localhost:8000
  📥 Import Feature: http://localhost:8000/import/
  👤 Admin Panel: http://localhost:8000/admin
  🔗 API Docs: http://localhost:8000/api/v1/
  💾 Database Admin: http://localhost:8080
  📬 RabbitMQ Management: http://localhost:15672
  📧 Mailhog: http://localhost:8025

Default credentials:
  Username: admin
  Password: admin123
```

### Option 2: Manual Docker Compose

If you prefer manual control:

```bash
# Build images
docker-compose -f docker-compose.development.yml build

# Start services
docker-compose -f docker-compose.development.yml up -d

# Wait for database to be ready
docker-compose -f docker-compose.development.yml exec web python manage.py check --deploy

# Run migrations
docker-compose -f docker-compose.development.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.development.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.development.yml exec web python manage.py collectstatic --noinput
```

### Option 3: Local Development (Without Docker)

For local development without Docker:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Set environment
export DJANGO_SETTINGS_MODULE=config.settings.development

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

**Note:** This requires PostgreSQL, Redis, and RabbitMQ to be installed and running locally.

---

## Verify Installation

### 1. Check Services Status

```bash
# View running containers
docker-compose -f docker-compose.development.yml ps

# Should show all services as "Up"
# - web (Django application)
# - db (PostgreSQL)
# - redis (Redis cache)
# - memcached (Memcached)
# - rabbitmq (RabbitMQ)
# - nginx (Nginx web server)
# - adminer (Database admin tool)
# - mailhog (Email testing)
```

### 2. Access the Application

Open your browser and navigate to:

**Main Application:**
```
http://localhost:8000
```

You should see the Financial Stronghold homepage.

**Admin Panel:**
```
http://localhost:8000/admin
```

Login with:
- Username: `admin`
- Password: `admin123` (or the password you set during superuser creation)

**API Documentation:**
```
http://localhost:8000/api/v1/
```

Browse available API endpoints.

### 3. Test API

Using cURL:

```bash
# Get API root
curl http://localhost:8000/api/v1/

# Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Use token to access protected endpoint
curl http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 4. Run Tests

Verify everything is working correctly:

```bash
# Run quick smoke tests
docker-compose -f docker-compose.testing.yml run test pytest tests/test_infrastructure.py -v

# Run full test suite (takes longer)
./scripts/start-test.sh
```

### 5. Check Version Consistency

Run the version verification script:

```bash
python scripts/verify_versions.py
```

Expected output:
```
============================================================
Version Verification
============================================================

Expected Versions:
  python: 3.12.3
  django: 5.1.13
  postgres: 17.2
  redis: 7
  memcached: 1.6
  rabbitmq: 3.12
  nginx: 1.24

Verification Results:
------------------------------------------------------------
✅ .python-version: 3.12.3
✅ Docker Compose PostgreSQL: postgres:17.2-alpine
✅ Docker Compose Redis: redis:7-alpine
✅ Docker Compose Memcached: memcached:1.6-alpine
✅ Docker Compose RabbitMQ: rabbitmq:3.12-alpine
✅ Docker Compose Nginx: nginx:1.24-alpine
✅ requirements/base.txt Django: 5.1.13
✅ Documentation version references verified

============================================================
✅ All version checks PASSED
```

---

## Next Steps

### Learn the Basics

1. **Explore the Admin Interface**
   - Navigate to http://localhost:8000/admin
   - Browse users, accounts, transactions
   - Try creating sample data

2. **Try the Import Feature**
   - Navigate to http://localhost:8000/import/
   - Upload a sample CSV file
   - Watch the import process
   - Review imported transactions

3. **Explore the API**
   - Read [API Documentation](docs/API_DOCUMENTATION.md)
   - Try API endpoints using cURL or Postman
   - Experiment with filtering and pagination

### Development Tasks

1. **Set Up Your IDE**
   - Install Python extensions
   - Configure linting (Black, Flake8, MyPy)
   - Set up debugging
   - See [IDE Setup Guide](docs/IDE_SETUP_GUIDE.md)

2. **Understand the Codebase**
   - Read [Architecture Documentation](ARCHITECTURE.md)
   - Review [Solution Architecture Analysis](SOLUTION_ARCHITECTURE_ANALYSIS.md)
   - Explore the `app/` directory structure

3. **Make Your First Change**
   - Create a feature branch
   - Make a small change
   - Run tests
   - Submit a pull request

4. **Learn Testing**
   - Read [Testing Guide](docs/TESTING_GUIDE.md)
   - Run unit tests
   - Write a simple test
   - Check test coverage

### Common Development Workflows

#### Add a New Model

```bash
# 1. Define model in app/models.py
# 2. Create migration
docker-compose exec web python manage.py makemigrations

# 3. Apply migration
docker-compose exec web python manage.py migrate

# 4. Register in admin.py
# 5. Write tests
# 6. Run tests
pytest tests/test_models.py -v
```

#### Add a New API Endpoint

```bash
# 1. Create serializer in app/serializers/
# 2. Create view in app/api/
# 3. Add URL pattern in app/urls.py
# 4. Write tests
# 5. Run tests
pytest tests/test_api.py -v

# 6. Test endpoint manually
curl http://localhost:8000/api/v1/your-endpoint/
```

#### Debug an Issue

```bash
# View logs
docker-compose logs -f web

# Access Django shell
docker-compose exec web python manage.py shell

# Run specific test
pytest tests/test_file.py::test_function -v

# Check database
docker-compose exec db psql -U django_user -d financial_db
```

---

## Troubleshooting

### Common Issues and Solutions

#### Port Already in Use

**Error:**
```
Error: Port 8000 is already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
docker-compose -f docker-compose.development.yml down
```

#### Database Connection Failed

**Error:**
```
OperationalError: could not connect to server
```

**Solution:**
```bash
# Check database service
docker-compose ps db

# Restart database
docker-compose restart db

# Wait for database to be ready
docker-compose exec web python manage.py check --database default
```

#### Migrations Conflict

**Error:**
```
Conflicting migrations detected
```

**Solution:**
```bash
# Reset migrations (development only)
docker-compose exec web python manage.py migrate --fake app zero
docker-compose exec web python manage.py migrate app

# Or reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

#### Permission Denied

**Error:**
```
Permission denied: './scripts/start-dev.sh'
```

**Solution:**
```bash
# Make script executable
chmod +x scripts/start-dev.sh

# Run script
./scripts/start-dev.sh
```

#### Docker Out of Space

**Error:**
```
no space left on device
```

**Solution:**
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

#### Static Files Not Loading

**Error:**
```
404 Not Found for static files
```

**Solution:**
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check static files configuration
docker-compose exec web python manage.py check
```

#### Import Feature Not Working

**Error:**
```
Import job stuck in PENDING status
```

**Solution:**
```bash
# Check Celery workers
docker-compose logs celery

# Restart Celery
docker-compose restart celery

# Check RabbitMQ
docker-compose logs rabbitmq
```

### Getting Help

If you encounter issues not covered here:

1. **Check Documentation**
   - [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
   - [FAQ](docs/wiki/faq.md)
   - [Known Issues](KNOWN_ISSUES.md)

2. **View Logs**
   ```bash
   # All services
   docker-compose logs

   # Specific service
   docker-compose logs web
   docker-compose logs db

   # Follow logs
   docker-compose logs -f web
   ```

3. **Search Issues**
   - GitHub Issues: https://github.com/nullroute-commits/financial_stronghold/issues
   - Search for similar problems
   - Check closed issues

4. **Ask for Help**
   - Create a new GitHub issue
   - Include error messages
   - Share relevant logs
   - Describe steps to reproduce

---

## What's Next?

### Learn More

- **Architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md)
- **API**: Explore [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- **Testing**: Study [TESTING_GUIDE.md](docs/TESTING_GUIDE.md)
- **Security**: Review [SECURITY_MODEL.md](docs/SECURITY_MODEL.md)

### Contribute

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Pick an issue to work on
3. Create a feature branch
4. Make your changes
5. Write tests
6. Submit a pull request

### Deploy to Production

When you're ready to deploy:

1. Read [DEPLOYMENT_GUIDE.md](docs/FEATURE_DEPLOYMENT_GUIDE.md)
2. Configure production environment
3. Set up SSL certificates
4. Configure monitoring
5. Deploy using production Docker Compose

---

## Summary

You should now have:

- ✅ Financial Stronghold running locally
- ✅ Access to admin panel and API
- ✅ Understanding of basic workflows
- ✅ Knowledge of where to find help

**Happy coding! 🚀**

---

**Last Updated:** 2025-11-24  
**Version:** 1.0  
**Django:** 5.1.13  
**Python:** 3.12.3
