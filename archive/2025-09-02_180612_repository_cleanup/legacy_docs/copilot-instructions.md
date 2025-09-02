# GitHub Copilot Instructions for Financial Stronghold

**Project**: Django 5 Multi-Architecture CI/CD Pipeline - Financial Stronghold  
**Last Updated**: 2024-12-19  
**SOP Compliance**: Following FEATURE_DEPLOYMENT_GUIDE.md containerized development process  
**Documentation**: MkDocs compatible technical documentation

---

## Table of Contents

- [Repository Overview](#repository-overview)
- [Architecture & Technology Stack](#architecture--technology-stack)
- [Development Workflow & SOP](#development-workflow--sop)
- [Code Organization & Patterns](#code-organization--patterns)
- [Docker Compose Integration](#docker-compose-integration)
- [Testing Framework](#testing-framework)
- [CI/CD Pipeline](#cicd-pipeline)
- [Security & Authentication](#security--authentication)
- [Data Models & Database](#data-models--database)
- [API Design Patterns](#api-design-patterns)
- [Configuration Management](#configuration-management)
- [Monitoring & Logging](#monitoring--logging)
- [Code Quality Standards](#code-quality-standards)
- [Deployment Strategies](#deployment-strategies)
- [Troubleshooting Guide](#troubleshooting-guide)

---

## Repository Overview

### Project Description
Financial Stronghold is a production-ready multi-tenant Django 5 application with comprehensive financial management capabilities, built with modern DevOps practices including containerized CI/CD pipelines and multi-architecture Docker support.

### Key Features
- **Django 5.1.10** with Python 3.12.5
- **Multi-tenant architecture** with user and organization scoping
- **PostgreSQL 17.2** database with SQLAlchemy 1.4.49 ORM
- **FastAPI integration** for high-performance API endpoints
- **RBAC (Role-Based Access Control)** system
- **Comprehensive audit logging** for all operations
- **Real-time financial analytics** and dashboard
- **Multi-architecture Docker support** (linux/amd64, linux/arm64)
- **Containerized CI/CD pipeline** using Docker Compose
- **49.48% test coverage** with comprehensive testing framework

### Repository Structure
```
financial_stronghold/
├── app/                          # Main application code
│   ├── api.py                    # FastAPI endpoints
│   ├── auth.py                   # Authentication & authorization
│   ├── financial_models.py       # Core financial data models
│   ├── services.py               # Business logic services
│   ├── middleware.py             # Custom middleware
│   └── core/                     # Core utilities and helpers
├── ci/                           # CI/CD pipeline scripts
│   ├── docker-compose.ci.yml     # CI environment configuration
│   ├── test.sh                   # Testing automation
│   ├── build.sh                  # Build automation
│   └── deploy.sh                 # Deployment automation
├── config/                       # Django configuration
├── docs/                         # MkDocs documentation
├── tests/                        # Test suites
├── environments/                 # Environment configurations
└── docker-compose.*.yml          # Environment-specific Docker configs
```

---

## Architecture & Technology Stack

### Core Technologies
- **Backend Framework**: Django 5.1.10 + FastAPI
- **Database**: PostgreSQL 17.2 with SQLAlchemy 1.4.49
- **Cache**: Memcached 1.6.22 for high-performance caching
- **Message Queue**: RabbitMQ 3.12.8 for async processing
- **Authentication**: JWT-based with RBAC
- **API**: RESTful endpoints with FastAPI integration
- **ORM**: Both Django ORM and SQLAlchemy for advanced queries

### Infrastructure Stack
- **Containerization**: Docker 24.0.7+ with multi-stage builds
- **Orchestration**: Docker Compose 2.18.1+ for development and CI/CD
- **Load Balancer**: Nginx 1.24.0 with SSL termination
- **Monitoring**: Built-in health checks and metrics
- **Security**: Comprehensive security headers and CSP

### Architecture Patterns
- **Multi-tier architecture** with clear separation of concerns
- **Multi-tenant data isolation** at database and application level
- **Microservices-ready** design with FastAPI integration
- **Event-driven architecture** using RabbitMQ
- **CQRS pattern** for financial data operations

---

## Development Workflow & SOP

### Standard Operating Procedure (FEATURE_DEPLOYMENT_GUIDE.md)

#### 1. Pre-Deployment Preparation
```bash
# Environment verification
docker --version  # >= 24.0.7
docker compose --version  # >= 2.18.1
python --version  # >= 3.12.5

# System resource check
docker system info | grep -E "CPUs|Total Memory"
```

#### 2. Code Quality Gates
```bash
# Format code
black app/ --line-length 120 --target-version py312

# Lint code
flake8 app/ --max-line-length=120 --ignore=E203,W503

# Type checking
mypy app/ --python-version 3.12

# Security scanning
bandit -r app/ -f json -o reports/security-report.json
safety check -r requirements/base.txt --json
```

#### 3. Testing Framework Execution
```bash
# Comprehensive test suite (49.48% coverage)
export DJANGO_SETTINGS_MODULE=config.settings.testing
python -m pytest tests/unit/ -v --cov=app --cov-report=html --cov-report=term

# Containerized testing
docker compose -f docker-compose.testing.yml up --build -d
docker compose -f docker-compose.testing.yml exec web \
  python -m pytest tests/unit/ --cov=app
docker compose -f docker-compose.testing.yml down
```

#### 4. CI/CD Pipeline Stages
```bash
# Stage 1: Quality gates
./ci/lint.sh
./ci/test.sh all

# Stage 2: Build multi-architecture images
./ci/build.sh

# Stage 3: Deploy to environments
./ci/deploy.sh development
./ci/deploy.sh staging
./ci/deploy.sh production
```

---

## Code Organization & Patterns

### Application Structure
```python
# app/main.py - FastAPI application entry point
from fastapi import FastAPI, Depends
from app.api import router as financial_router
from app.auth import get_tenant_context

# Multi-tenant context injection
@app.get("/endpoint")
def endpoint(tenant_context: dict = Depends(get_tenant_context)):
    # All endpoints receive tenant context automatically
    pass
```

### Financial Models Pattern
```python
# app/financial_models.py
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from app.core.models import BaseModel, TenantMixin

class Account(BaseModel, TenantMixin):
    """Financial account with multi-tenant isolation."""
    __tablename__ = 'accounts'
    
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)
    balance = Column(Numeric(precision=15, scale=2), default=0)
    
    # Automatic tenant scoping via TenantMixin
```

### Service Layer Pattern
```python
# app/services.py
from app.core.services import BaseService
from app.financial_models import Account

class AccountService(BaseService):
    """Account management with tenant isolation."""
    model = Account
    
    def create_account(self, tenant_id: str, data: dict) -> Account:
        """Create account with automatic tenant scoping."""
        return self.create(tenant_id=tenant_id, **data)
```

### Authentication & Authorization
```python
# app/auth.py
from fastapi import Depends, HTTPException
from app.core.auth import JWTHandler, RBACChecker

def get_tenant_context(token: str = Depends(JWTHandler.get_token)):
    """Extract tenant context from JWT token."""
    payload = JWTHandler.decode_token(token)
    return {
        'tenant_type': payload.get('tenant_type'),
        'tenant_id': payload.get('tenant_id'),
        'user_id': payload.get('user_id'),
        'permissions': payload.get('permissions', [])
    }
```

---

## Docker Compose Integration

### Development Environment
```yaml
# docker-compose.development.yml
services:
  web:
    build:
      target: development
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DEBUG=True
    volumes:
      - .:/app  # Live code reloading
    ports:
      - "8000:8000"
    depends_on:
      - db
      - memcached
      - rabbitmq
```

### Testing Environment
```yaml
# docker-compose.testing.yml
services:
  test-runner:
    build:
      target: testing
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.testing
    depends_on:
      - test-db
      - test-memcached
      - test-rabbitmq
    command: python -m pytest tests/ --cov=app
```

### Production Environment
```yaml
# docker-compose.production.yml
services:
  web:
    build:
      target: production
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DEBUG=False
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Multi-Architecture Build
```bash
# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target production \
  --tag registry/financial-stronghold:latest \
  --push \
  .
```

---

## Testing Framework

### Test Coverage Strategy
- **Overall Coverage**: 49.48% (1,605 lines covered out of 3,244 total)
- **Core Components**: 
  - Financial Models: 100%
  - Schemas: 100%
  - Authentication: 56%
  - Services: 55%
  - Tenant System: 97%

### Test Categories
```python
# tests/unit/test_comprehensive_coverage.py
class TestFinancialModels:
    """100% coverage for financial models."""
    def test_account_creation(self):
        # Test account creation with tenant isolation
        pass
    
    def test_transaction_processing(self):
        # Test transaction with validation and audit
        pass

class TestAuthenticationSystem:
    """56% coverage for authentication."""
    def test_jwt_token_generation(self):
        # Test JWT token creation and validation
        pass
    
    def test_rbac_permissions(self):
        # Test role-based access control
        pass
```

### Mock Strategy
```python
# Enhanced mock-based testing
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def mock_database():
    """Mock database for isolated testing."""
    with patch('app.core.database.get_session') as mock:
        yield mock

def test_service_with_mocks(mock_database):
    """Test services with mocked dependencies."""
    # Test business logic without external dependencies
    pass
```

### Containerized Testing
```bash
# Run tests in containerized environment
docker compose -f docker-compose.testing.yml up --build -d

# Execute specific test suites
docker compose -f docker-compose.testing.yml exec test-runner \
  python -m pytest tests/unit/test_comprehensive_coverage.py \
  --cov=app --cov-report=html:reports/coverage/docker-html

# Cleanup
docker compose -f docker-compose.testing.yml down
```

---

## CI/CD Pipeline

### Pipeline Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │───▶│     Testing     │───▶│   Production    │
│   Environment   │    │   Environment   │    │   Environment   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                    Pipeline Stages                              │
 │                                                                 │
 │ Stage 1: Quality ──► Stage 2: Test ──► Stage 3: Build ──► Stage 4: Deploy │
 │                                                                 │
 │ • Lint           • Unit Tests     • Multi-arch    • Development │
 │ • Security       • Integration    • Production    • Testing     │
 │ • Type Check     • Coverage       • Optimization  • Staging     │
 │                                                   • Production  │
 └─────────────────────────────────────────────────────────────────┘
```

### CI Configuration
```yaml
# ci/docker-compose.ci.yml
services:
  ci-runner:
    build: ci/Dockerfile.ci
    volumes:
      - .:/app
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - CI=true
      - DOCKER_BUILDKIT=1

  # Parallel test services
  unit-tests:
    extends: ci-runner
    command: /app/ci/test.sh unit
    
  integration-tests:
    extends: ci-runner
    command: /app/ci/test.sh integration
    
  security-scan:
    image: pyupio/safety
    command: safety check -r requirements/base.txt
```

### Deployment Strategies
- **Blue-Green Deployment**: Zero-downtime deployments
- **Rolling Updates**: Gradual service updates
- **Canary Releases**: Gradual traffic shifting
- **Feature Flags**: Runtime feature toggling

---

## Security & Authentication

### Security Architecture
```python
# app/auth.py - JWT Authentication
class JWTHandler:
    """Secure JWT token management."""
    
    @staticmethod
    def create_token(user_data: dict, tenant_data: dict) -> str:
        payload = {
            'user_id': user_data['id'],
            'tenant_type': tenant_data['type'],
            'tenant_id': tenant_data['id'],
            'permissions': user_data['permissions'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
```

### RBAC System
```python
# app/django_rbac.py
class PermissionChecker:
    """Role-based access control."""
    
    def check_permission(self, user_permissions: list, required_permission: str) -> bool:
        """Check if user has required permission."""
        return required_permission in user_permissions or 'admin' in user_permissions
```

### Security Headers
```python
# config/settings/security.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSP Configuration
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
```

---

## Data Models & Database

### Financial Models
```python
# app/financial_models.py
class Account(BaseModel, TenantMixin):
    """Core financial account model."""
    __tablename__ = 'accounts'
    
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # checking, savings, credit
    balance = Column(Numeric(precision=15, scale=2), default=0)
    currency = Column(String(3), default='USD')
    is_active = Column(Boolean, default=True)

class Transaction(BaseModel, TenantMixin):
    """Financial transaction model."""
    __tablename__ = 'transactions'
    
    account_id = Column(UUID, ForeignKey('accounts.id'), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # debit, credit
    description = Column(String(500))
    category = Column(String(100))
    transaction_date = Column(DateTime, default=datetime.utcnow)
```

### Multi-Tenancy Pattern
```python
# app/core/models.py
class TenantMixin:
    """Mixin for multi-tenant data isolation."""
    tenant_type = Column(String(20), nullable=False)  # user, organization
    tenant_id = Column(String(255), nullable=False)
    
    @classmethod
    def get_for_tenant(cls, tenant_type: str, tenant_id: str):
        """Get records for specific tenant."""
        return cls.query.filter(
            cls.tenant_type == tenant_type,
            cls.tenant_id == tenant_id
        )
```

### Database Migrations
```python
# Alembic migration example
def upgrade():
    """Add financial analytics tables."""
    op.create_table(
        'transaction_analytics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_type', sa.String(20), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('period', sa.String(10), nullable=False),
        sa.Column('total_income', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_expenses', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
```

---

## API Design Patterns

### FastAPI Integration
```python
# app/api.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_tenant_context
from app.services import AccountService

router = APIRouter(prefix="/api/v1")

@router.post("/accounts")
async def create_account(
    account_data: AccountCreateSchema,
    tenant_context: dict = Depends(get_tenant_context)
):
    """Create new financial account."""
    service = AccountService()
    account = service.create_account(
        tenant_id=tenant_context['tenant_id'],
        data=account_data.dict()
    )
    return AccountResponseSchema.from_orm(account)
```

### Schema Validation
```python
# app/schemas.py - Pydantic models
from pydantic import BaseModel, validator
from decimal import Decimal
from typing import Optional

class AccountCreateSchema(BaseModel):
    name: str
    account_type: str
    initial_balance: Optional[Decimal] = Decimal('0.00')
    
    @validator('account_type')
    def validate_account_type(cls, v):
        allowed_types = ['checking', 'savings', 'credit', 'investment']
        if v not in allowed_types:
            raise ValueError(f'Account type must be one of: {allowed_types}')
        return v

class TransactionCreateSchema(BaseModel):
    account_id: str
    amount: Decimal
    transaction_type: str
    description: Optional[str] = None
    category: Optional[str] = None
```

### Error Handling
```python
# app/core/exceptions.py
class FinancialStrongholdException(Exception):
    """Base exception for application errors."""
    pass

class InsufficientFundsException(FinancialStrongholdException):
    """Raised when account has insufficient funds."""
    pass

class TenantAccessException(FinancialStrongholdException):
    """Raised when accessing data outside tenant scope."""
    pass

# API error handlers
@app.exception_handler(FinancialStrongholdException)
async def financial_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "type": exc.__class__.__name__}
    )
```

---

## Configuration Management

### Environment-Specific Settings
```python
# config/settings/base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment variables with defaults
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'django_app'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}
```

### Environment Files
```bash
# environments/.env.development.example
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=dev-secret-key

# Database
POSTGRES_DB=django_app_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Cache
MEMCACHED_LOCATION=memcached:11211

# Queue
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

### Docker Configuration
```dockerfile
# Multi-stage Dockerfile
FROM python:3.12.5-slim as base
WORKDIR /app
COPY requirements/ requirements/
RUN pip install -r requirements/base.txt

FROM base as development
RUN pip install -r requirements/dev.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base as production
RUN pip install -r requirements/prod.txt
COPY . .
RUN python manage.py collectstatic --noinput
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## Monitoring & Logging

### Audit Logging
```python
# app/django_audit.py
class AuditLogEntry(models.Model):
    """Comprehensive audit logging for all operations."""
    user_id = models.CharField(max_length=255, null=True, blank=True)
    tenant_type = models.CharField(max_length=20)
    tenant_id = models.CharField(max_length=255)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255, null=True, blank=True)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
```

### Health Checks
```python
# app/health.py
@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    checks = {
        'database': await check_database_connection(),
        'cache': await check_cache_connection(),
        'queue': await check_queue_connection(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    status_code = 200 if status == "healthy" else 503
    
    return Response(
        content=json.dumps({"status": status, "checks": checks}),
        status_code=status_code,
        media_type="application/json"
    )
```

### Metrics Collection
```python
# app/middleware.py
class MetricsMiddleware:
    """Collect application metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        start_time = time.time()
        
        # Process request
        await self.app(scope, receive, send)
        
        # Record metrics
        duration = time.time() - start_time
        metrics.record_request_duration(
            path=scope['path'],
            method=scope['method'],
            duration=duration
        )
```

---

## Code Quality Standards

### Linting Configuration
```ini
# .flake8
[flake8]
max-line-length = 120
ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    migrations,
    .venv,
    venv

# .mypy.ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### Code Formatting
```python
# pyproject.toml
[tool.black]
line-length = 120
target-version = ['py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  migrations
)/
'''

[tool.isort]
profile = "black"
line_length = 120
multi_line_output = 3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3.12
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
```

---

## Deployment Strategies

### Environment Promotion
```bash
# Development to Testing
./ci/deploy.sh testing --from-development

# Testing to Staging
./ci/deploy.sh staging --from-testing

# Staging to Production
./ci/deploy.sh production --from-staging --require-approval
```

### Blue-Green Deployment
```yaml
# docker-compose.production.yml
services:
  web-blue:
    image: financial-stronghold:blue
    environment:
      - DEPLOYMENT_SLOT=blue
    
  web-green:
    image: financial-stronghold:green
    environment:
      - DEPLOYMENT_SLOT=green
    
  nginx:
    depends_on:
      - web-blue
      - web-green
    environment:
      - ACTIVE_SLOT=blue  # Switch to green for deployment
```

### Rollback Procedures
```bash
# Automatic rollback on health check failure
./ci/deploy.sh production --rollback-on-failure

# Manual rollback to previous version
./ci/deploy.sh production --rollback --to-version=v1.2.3

# Quick rollback using blue-green
docker compose -f docker-compose.production.yml \
  exec nginx /scripts/switch-slot.sh blue
```

---

## Troubleshooting Guide

### Common Issues & Solutions

#### Database Connection Issues
```bash
# Check database connectivity
docker compose exec web python manage.py dbshell

# Reset database
docker compose down
docker volume rm financial_stronghold_postgres_data
docker compose up -d db
docker compose exec web python manage.py migrate
```

#### Cache Performance Issues
```bash
# Check cache statistics
docker compose exec memcached echo 'stats' | nc localhost 11211

# Flush cache
docker compose exec web python manage.py shell -c "
from django.core.cache import cache
cache.clear()
"
```

#### Test Failures
```bash
# Run specific failing test
docker compose -f docker-compose.testing.yml exec test-runner \
  python -m pytest tests/unit/test_specific.py::TestClass::test_method -v

# Debug with coverage
python -m pytest tests/unit/ --cov=app --cov-report=html --pdb
```

#### Performance Issues
```bash
# Profile application
docker compose exec web python -m cProfile -o profile.stats manage.py runserver

# Monitor container resources
docker stats financial_stronghold_web_1
```

### Debug Mode Setup
```python
# config/settings/debug.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'app': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

---

## Critical Guidelines for GitHub Copilot

### 🚨 **ALWAYS Follow These Patterns**

1. **Multi-Tenant Context**: Every database operation MUST include tenant scoping
   ```python
   # CORRECT
   accounts = Account.get_for_tenant(tenant_type, tenant_id)
   
   # INCORRECT - Never access data without tenant scope
   accounts = Account.query.all()
   ```

2. **Authentication Required**: All API endpoints MUST use tenant context dependency
   ```python
   # CORRECT
   @router.get("/accounts")
   async def get_accounts(tenant_context: dict = Depends(get_tenant_context)):
   
   # INCORRECT - Never create unprotected endpoints
   @router.get("/accounts")
   async def get_accounts():
   ```

3. **Docker Compose First**: Always use containerized development
   ```bash
   # CORRECT - Use Docker Compose
   docker compose -f docker-compose.development.yml up -d
   
   # INCORRECT - Never run services directly
   python manage.py runserver
   ```

4. **Testing Coverage**: Maintain comprehensive test coverage
   ```python
   # ALWAYS include both positive and negative test cases
   def test_create_account_success(self):
   def test_create_account_insufficient_permissions(self):
   ```

5. **Environment Configuration**: Use environment variables for all configuration
   ```python
   # CORRECT
   SECRET_KEY = os.environ.get('SECRET_KEY')
   
   # INCORRECT
   SECRET_KEY = 'hardcoded-secret'
   ```

### 🔧 **Development Commands Reference**

```bash
# Start development environment
docker compose -f docker-compose.development.yml up -d

# Run tests with coverage
docker compose -f docker-compose.testing.yml exec test-runner \
  python -m pytest tests/ --cov=app --cov-report=html

# Code quality checks
black app/ --line-length 120 --check
flake8 app/ --max-line-length=120
mypy app/ --python-version 3.12

# Database operations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py shell

# CI/CD pipeline
./ci/test.sh all
./ci/build.sh
./ci/deploy.sh development
```

### 📋 **MkDocs Documentation Standards**

- Use clear section headers with proper markdown hierarchy
- Include code examples with syntax highlighting
- Add diagrams using ASCII art or mermaid syntax
- Ensure all documentation is compatible with MkDocs material theme
- Include cross-references between related documentation files
- Maintain table of contents for easy navigation

---

**End of Copilot Instructions**

This comprehensive guide ensures GitHub Copilot has complete context about the Financial Stronghold repository, following the SOP outlined in FEATURE_DEPLOYMENT_GUIDE.md with full Docker Compose integration and MkDocs compatibility. All patterns, workflows, and architectural decisions are documented to prevent hallucinations and ensure accurate code generation.