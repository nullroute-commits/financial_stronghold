# DevOps Engineer Guide

This guide provides comprehensive information for DevOps engineers managing the Financial Stronghold CI/CD pipeline and infrastructure.

## Overview

Financial Stronghold uses a fully containerized CI/CD pipeline built with Docker Compose, supporting multi-architecture deployments and automated quality gates.

## CI/CD Pipeline Architecture

### Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Docker CI/CD Pipeline                               │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
     │   CI Runner     │         │   Test DB       │         │   Services      │
     │                 │         │                 │         │                 │
     │ • Python 3.12   │◄────────┤ • PostgreSQL 17│◄────────┤ • Memcached     │
     │ • CI Tools      │         │ • Tmpfs storage │         │ • RabbitMQ      │
     │ • Docker-in-    │         │ • Fast test DB  │         │ • Test Services │
     │   Docker        │         │                 │         │                 │
     └─────────────────┘         └─────────────────┘         └─────────────────┘
```

### Stage Details

1. **Lint Stage** - Code quality validation
2. **Test Stage** - Comprehensive test execution  
3. **Build Stage** - Multi-architecture Docker builds
4. **Security Stage** - Vulnerability scanning
5. **Deploy Stage** - Environment deployment

## Pipeline Management

### Running the Complete Pipeline

```bash
# Start the CI/CD pipeline
docker compose -f ci/docker-compose.ci.yml up

# Run individual stages
docker compose -f ci/docker-compose.ci.yml run --rm ci-runner lint
docker compose -f ci/docker-compose.ci.yml run --rm ci-runner test
docker compose -f ci/docker-compose.ci.yml run --rm ci-runner build
docker compose -f ci/docker-compose.ci.yml run --rm ci-runner security
```

### Pipeline Configuration

#### CI Docker Compose (`ci/docker-compose.ci.yml`)

```yaml
version: '3.8'
services:
  # Main pipeline orchestrator
  ci-runner:
    build:
      context: .
      dockerfile: ci/Dockerfile.ci
    volumes:
      - .:/app
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - CI=true
      - DOCKER_BUILDKIT=1
    
  # Database for testing
  test-db:
    image: postgres:17.2
    environment:
      POSTGRES_DB: django_app_ci
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ci-password
    tmpfs:
      - /var/lib/postgresql/data
      
  # Cache for testing
  test-memcached:
    image: memcached:1.6.22
    command: memcached -m 64
    
  # Queue for testing
  test-rabbitmq:
    image: rabbitmq:3.12.8
    environment:
      RABBITMQ_DEFAULT_USER: ci
      RABBITMQ_DEFAULT_PASS: ci-password
```

## Deployment Management

### Environment Strategy

| Environment | Purpose | Deployment | Configuration |
|-------------|---------|------------|---------------|
| Development | Feature development | Automatic | Debug enabled, hot reload |
| Testing | Automated testing | Automatic | Production-like, test data |
| Staging | Pre-production validation | Manual | Production mirror, staging data |
| Production | Live user traffic | Manual with approval | Optimized, monitored |

### Deployment Commands

```bash
# Validate deployment configuration
./ci/validate-deployment-demo.sh [environment]

# Deploy to specific environment
./ci/deploy.sh [development|testing|staging|production]

# Example deployments
./ci/deploy.sh development   # Auto-deploy dev changes
./ci/deploy.sh testing       # Deploy for testing
./ci/deploy.sh staging       # Manual staging deployment
./ci/deploy.sh production    # Production deployment (requires approval)
```

### Deployment Validation

#### Quick Configuration Check

```bash
# Validate all environments
./ci/validate-deployment-demo.sh all

# Validate specific environment
./ci/validate-deployment-demo.sh production
```

#### Full Deployment Validation

```bash
# Complete validation with actual deployments
./ci/validate-deployment.sh production
```

### Multi-Architecture Builds

#### Build Configuration

```bash
# Initialize Docker Buildx for multi-architecture
docker buildx create --name multiarch --driver docker-container --use

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target production \
  --tag registry/django-app:latest \
  --push .
```

#### Build Targets

```dockerfile
# Multi-stage Dockerfile
FROM python:3.12.3-slim as base
# Base dependencies

FROM base as development  
# Development dependencies and tools

FROM base as testing
# Test dependencies

FROM base as production
# Production optimized
```

## Environment Configuration

### Environment Files Structure

```
environments/
├── .env.development.example    # Development configuration
├── .env.testing.example       # Testing configuration
├── .env.staging.example       # Staging configuration
└── .env.production.example    # Production configuration
```

### Configuration Management

#### Development Environment

```bash
# Copy and customize development config
cp environments/.env.development.example .env.development

# Key development settings
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
POSTGRES_DB=django_app_dev
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

#### Production Environment

```bash
# Copy and customize production config
cp environments/.env.production.example .env.production

# Key production settings
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
POSTGRES_DB=django_app_prod
ALLOWED_HOSTS=yourdomain.com
SECRET_KEY=your-production-secret-key
```

### Secrets Management

#### Docker Secrets

```yaml
# docker-compose.production.yml
services:
  web:
    secrets:
      - postgres_password
      - secret_key
      - rabbitmq_password

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
  rabbitmq_password:
    file: ./secrets/rabbitmq_password.txt
```

#### Environment Variable Loading

```python
# In Django settings
import os
import stat
import logging

def load_secret(secret_name: str, default: str = '') -> str:
    """Load secret from file or environment variable."""
    secret_file = f'/run/secrets/{secret_name}'
    
    # Try Docker secret file first
    if os.path.exists(secret_file):
        try:
            st = os.stat(secret_file)
            # Check that file is only readable by owner (mode 0o600)
            if (st.st_mode & 0o077):
                logging.warning(f"Secret file {secret_file} has overly permissive permissions: {oct(st.st_mode)}")
                # Optionally, refuse to read the secret if permissions are too open
                # return default
            with open(secret_file, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Error reading secret file {secret_file}: {e}")
            # Fall back to environment variable
            return os.environ.get(secret_name, default)
    
    # Fall back to environment variable
    return os.environ.get(secret_name, default)

SECRET_KEY = load_secret('SECRET_KEY', 'change-me-in-production')
```

## Monitoring and Health Checks

### Health Check Endpoints

```bash
# Application health
curl http://localhost:8000/health/

# Database health
curl http://localhost:8000/health/db/

# Cache health  
curl http://localhost:8000/health/cache/

# Queue health
curl http://localhost:8000/health/queue/
```

### Service Monitoring

```bash
# Check all services status
docker compose -f docker-compose.production.yml ps

# View service logs
docker compose -f docker-compose.production.yml logs -f [service]

# Monitor resource usage
docker stats $(docker compose -f docker-compose.production.yml ps -q)
```

### Pipeline Monitoring

```bash
# Check pipeline status
docker compose -f ci/docker-compose.ci.yml ps

# View pipeline logs
docker compose -f ci/docker-compose.ci.yml logs -f ci-runner

# Monitor build progress
docker compose -f ci/docker-compose.ci.yml logs -f --tail=50 ci-runner
```

## Automation Scripts

### CI Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `ci/build.sh` | Build Docker images | `./ci/build.sh` |
| `ci/test.sh` | Run test suite | `./ci/test.sh [all\|unit\|integration]` |
| `ci/lint.sh` | Code quality checks | `./ci/lint.sh` |
| `ci/deploy.sh` | Deploy to environment | `./ci/deploy.sh [environment]` |
| `ci/validate-deployment.sh` | Full deployment validation | `./ci/validate-deployment.sh [environment]` |

### Promotion Workflow

#### Development to Staging

```bash
# Automatic promotion script
./ci/scripts/promote-to-test.sh

# Manual steps:
# 1. Quality gates check
# 2. Tag image for staging
# 3. Deploy to staging environment
# 4. Run staging tests
```

#### Staging to Production

```bash
# Production promotion (requires approval)
./ci/scripts/promote-to-release.sh

# Manual steps:
# 1. Final security scan
# 2. Database migration safety check  
# 3. Rolling deployment
# 4. Health verification
```

### Custom Automation

#### Adding New Pipeline Stage

1. **Create script in `ci/` directory**
   ```bash
   # ci/custom-stage.sh
   #!/bin/bash
   set -e
   
   echo "Running custom stage..."
   # Your custom logic here
   ```

2. **Add to CI Docker Compose**
   ```yaml
   # ci/docker-compose.ci.yml
   services:
     custom-stage:
       build:
         context: .
         dockerfile: ci/Dockerfile.ci
       command: ./ci/custom-stage.sh
   ```

3. **Integrate with main pipeline**
   ```bash
   # In ci/entrypoint.sh
   case "$1" in
     "custom")
       ./ci/custom-stage.sh
       ;;
   esac
   ```

## Security Management

### Security Scanning

```bash
# Container vulnerability scanning
trivy image django-app:latest \
  --severity HIGH,CRITICAL \
  --exit-code 1

# Code security scanning
docker run --rm -v $(pwd):/app \
  securecodewarrior/docker-security-scanning \
  /app

# Dependency vulnerability scanning
safety check -r requirements/production.txt
```

### Security Configuration

#### HTTPS/TLS

```yaml
# docker-compose.production.yml
services:
  nginx:
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
    environment:
      - SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
      - SSL_KEY_PATH=/etc/nginx/ssl/key.pem
```

#### Security Headers

```python
# config/settings/production.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## Performance Optimization

### Build Optimization

```dockerfile
# Use multi-stage builds to reduce image size
FROM python:3.12.3-alpine as base
RUN apk update && apk add --no-cache \
    build-base \
    && rm -rf /var/cache/apk/*

FROM base as production
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt
```

### Deployment Optimization

```yaml
# docker-compose.production.yml
services:
  web:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

## Troubleshooting

### Common Pipeline Issues

1. **Build Failures**
   ```bash
   # Check build logs
   docker compose -f ci/docker-compose.ci.yml logs ci-runner
   
   # Debug build interactively
   docker compose -f ci/docker-compose.ci.yml run --rm ci-runner bash
   ```

2. **Test Failures**
   ```bash
   # Run tests with verbose output
   ./ci/test.sh all --verbose
   
   # Check test database
   docker compose -f ci/docker-compose.ci.yml exec test-db psql -U postgres -d django_app_ci
   ```

3. **Deployment Issues**
   ```bash
   # Validate deployment configuration
   ./ci/validate-deployment-demo.sh production
   
   # Check service health
   docker compose -f docker-compose.production.yml exec web curl http://localhost:8000/health/
   ```

### Performance Troubleshooting

```bash
# Monitor container resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check application performance
docker compose -f docker-compose.production.yml exec web python manage.py shell -c "
from django.test.utils import override_settings
from django.core.management import call_command
call_command('check', verbosity=2)
"
```

### Getting Help

- Review the [Complete Troubleshooting Guide](../troubleshooting/index.md)
- Check [System Architecture Documentation](../architecture/index.md)
- Consult [Configuration System Guide](../../CONFIGURATION_SYSTEM.md)
- Open an issue on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)