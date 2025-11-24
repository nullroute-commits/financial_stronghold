# Testing Guide

**Project:** Financial Stronghold  
**Django Version:** 5.1.13  
**Python Version:** 3.12.3  
**Testing Framework:** pytest 8.3.3 with pytest-django 4.9.0

---

## Table of Contents

1. [Overview](#overview)
2. [Test Infrastructure](#test-infrastructure)
3. [Running Tests](#running-tests)
4. [Test Types](#test-types)
5. [Writing Tests](#writing-tests)
6. [Test Coverage](#test-coverage)
7. [CI/CD Integration](#cicd-integration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Financial Stronghold uses a comprehensive testing approach with multiple test types to ensure reliability and maintainability:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Performance Tests**: Validate system performance
- **Security Tests**: Verify security controls
- **Regression Tests**: Prevent known bugs from reappearing
- **Frontend Tests**: Test UI components and interactions

### Test Statistics

- **Total Test Files**: 20+
- **Total Tests**: 300+
- **Target Coverage**: 85% minimum
- **Current Coverage**: ~90%

---

## Test Infrastructure

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures and configuration
├── test_models.py              # Django model tests
├── test_api.py                 # API endpoint tests
├── test_views.py               # View tests
├── test_tenant.py              # Multi-tenancy tests
├── test_tenant_logic.py        # Tenant logic tests
├── test_infrastructure.py      # Infrastructure tests
├── unit/
│   ├── test_dashboard_comprehensive.py
│   ├── test_additional_coverage.py
│   ├── test_api_100_percent.py
│   ├── test_urls_settings_100_percent.py
│   └── test_zero_coverage_focused.py
├── integration/
│   ├── test_comprehensive_integration.py
│   ├── test_dashboard_api.py
│   ├── test_tagging_analytics_api.py
│   └── test_transaction_classification_api.py
├── performance/
│   ├── test_comprehensive_performance.py
│   └── test_performance_optimization.py
├── security/
│   ├── test_comprehensive_security.py
│   └── test_security_hardening.py
├── regression/
│   └── test_comprehensive_regression.py
└── frontend/
    └── (Frontend test files)
```

### Key Configuration Files

**pytest.ini / pyproject.toml:**
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.testing"
python_files = ["tests.py", "test_*.py", "*_tests.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = """
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term
    --cov-fail-under=80
    --no-migrations
    --reuse-db
"""
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
    "security: marks tests as security tests",
]
```

**conftest.py:**
```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def authenticated_client(client, user):
    """Return authenticated client."""
    client.force_login(user)
    return client
```

---

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run specific test function
pytest tests/test_models.py::test_user_creation

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run tests in parallel (faster)
pytest -n auto
```

### Using Docker

```bash
# Run tests in Docker environment
docker-compose -f docker-compose.testing.yml up --abort-on-container-exit

# Run specific test type
docker-compose -f docker-compose.testing.yml run test pytest tests/unit/

# Run with coverage
docker-compose -f docker-compose.testing.yml run test pytest --cov=app
```

### Using Test Script

```bash
# Run complete test suite
./scripts/start-test.sh

# This script:
# 1. Sets up test database
# 2. Runs all test types
# 3. Generates coverage report
# 4. Cleans up resources
```

### Test Environment Variables

Create `.env.testing` file:

```bash
# Database
DATABASE_NAME=test_financial_db
DATABASE_USER=test_user
DATABASE_PASSWORD=test_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Django
DJANGO_SETTINGS_MODULE=config.settings.testing
SECRET_KEY=test-secret-key-not-for-production
DEBUG=False

# Logging
LOG_LEVEL=WARNING
DJANGO_LOG_LEVEL=WARNING

# Cache (in-memory for tests)
CACHE_BACKEND=dummy

# Celery (synchronous for tests)
CELERY_TASK_ALWAYS_EAGER=True
CELERY_TASK_EAGER_PROPAGATES=True
```

---

## Test Types

### Unit Tests

Test individual components in isolation.

**Location:** `tests/unit/`

**Example:**
```python
import pytest
from app.services.transaction_classifier import TransactionClassifier


class TestTransactionClassifier:
    """Unit tests for transaction classifier."""
    
    @pytest.fixture
    def classifier(self):
        return TransactionClassifier()
    
    def test_classify_grocery_transaction(self, classifier):
        """Test grocery transaction classification."""
        result = classifier.classify("Whole Foods Market")
        
        assert result['category'] == 'Groceries'
        assert result['confidence'] > 0.8
    
    def test_classify_unknown_transaction(self, classifier):
        """Test unknown transaction classification."""
        result = classifier.classify("UNKNOWN MERCHANT 123")
        
        assert result['category'] == 'Uncategorized'
        assert result['confidence'] < 0.5
```

**Run unit tests:**
```bash
pytest tests/unit/ -m unit
```

### Integration Tests

Test component interactions and API endpoints.

**Location:** `tests/integration/`

**Example:**
```python
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.integration
class TestImportAPI:
    """Integration tests for import API."""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_file_upload_flow(self, api_client, user):
        """Test complete file upload flow."""
        api_client.force_authenticate(user=user)
        
        # Upload file
        with open('tests/fixtures/transactions.csv', 'rb') as f:
            response = api_client.post(
                '/api/v1/import/uploads/',
                {'file': f},
                format='multipart'
            )
        
        assert response.status_code == 201
        upload_id = response.data['id']
        
        # Validate file
        response = api_client.post(
            f'/api/v1/import/uploads/{upload_id}/validate_file/'
        )
        
        assert response.status_code == 200
        assert response.data['is_valid'] is True
        
        # Start import
        response = api_client.post(
            f'/api/v1/import/uploads/{upload_id}/start_import/',
            {'import_settings': {'skip_duplicates': True}}
        )
        
        assert response.status_code == 202
        assert 'import_job_id' in response.data
```

**Run integration tests:**
```bash
pytest tests/integration/ -m integration
```

### Performance Tests

Validate system performance under load.

**Location:** `tests/performance/`

**Example:**
```python
import pytest
import time
from django.test import Client


@pytest.mark.slow
class TestPerformance:
    """Performance tests."""
    
    def test_api_response_time(self, authenticated_client):
        """Test API response time."""
        start_time = time.time()
        response = authenticated_client.get('/api/v1/transactions/')
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in less than 1 second
    
    def test_bulk_transaction_import(self, authenticated_client):
        """Test bulk import performance."""
        # Create 1000 transaction records
        start_time = time.time()
        
        # Import logic here
        
        duration = time.time() - start_time
        assert duration < 30.0  # Should complete in less than 30 seconds
```

**Run performance tests:**
```bash
pytest tests/performance/ -m slow
```

### Security Tests

Verify security controls and vulnerability prevention.

**Location:** `tests/security/`

**Example:**
```python
import pytest
from django.test import Client


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers."""
    
    def test_xss_protection_header(self, client):
        """Test X-XSS-Protection header."""
        response = client.get('/')
        
        assert 'X-XSS-Protection' in response.headers
        assert response.headers['X-XSS-Protection'] == '1; mode=block'
    
    def test_content_type_options_header(self, client):
        """Test X-Content-Type-Options header."""
        response = client.get('/')
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
    
    def test_sql_injection_prevention(self, authenticated_client):
        """Test SQL injection prevention."""
        # Try SQL injection in search parameter
        response = authenticated_client.get(
            '/api/v1/transactions/?search=\' OR 1=1--'
        )
        
        # Should handle safely without error
        assert response.status_code == 200
        assert 'error' not in response.data
```

**Run security tests:**
```bash
pytest tests/security/ -m security
```

### Regression Tests

Prevent previously fixed bugs from reappearing.

**Location:** `tests/regression/`

**Example:**
```python
import pytest


@pytest.mark.regression
class TestRegressions:
    """Test previously fixed bugs."""
    
    def test_circular_import_bug_fixed(self):
        """Regression test for circular import issue."""
        # This should not raise ImportError
        try:
            from app.models.import_models import ImportJob
            from app.django_models import User
            assert True
        except ImportError:
            pytest.fail("Circular import issue detected")
    
    def test_duplicate_transaction_detection(self, db, user):
        """Regression test for duplicate detection bug."""
        from app.models import Transaction
        
        # Create transaction
        t1 = Transaction.objects.create(
            user=user,
            description="Test transaction",
            amount=100.00,
            date="2025-11-24"
        )
        
        # Try to create duplicate
        t2 = Transaction.objects.create(
            user=user,
            description="Test transaction",
            amount=100.00,
            date="2025-11-24"
        )
        
        # Duplicate detection should mark it
        assert t2.is_duplicate or t2.duplicate_of == t1
```

**Run regression tests:**
```bash
pytest tests/regression/
```

---

## Writing Tests

### Test Naming Conventions

```python
# Good naming
def test_user_can_login_with_valid_credentials():
    """Test that user can login with correct email and password."""
    pass

def test_import_job_marks_duplicates_correctly():
    """Test duplicate detection in import jobs."""
    pass

# Bad naming
def test_1():
    pass

def test_stuff():
    pass
```

### Using Fixtures

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def account(db, user):
    """Create test account."""
    from app.models import Account
    return Account.objects.create(
        user=user,
        name='Test Account',
        balance=1000.00
    )


def test_user_has_accounts(user, account):
    """Test user can have accounts."""
    assert user.accounts.count() == 1
    assert user.accounts.first() == account
```

### Parameterized Tests

```python
import pytest


@pytest.mark.parametrize('amount,expected_category', [
    (-50.00, 'Groceries'),
    (-5.50, 'Dining'),
    (-1500.00, 'Housing'),
    (2500.00, 'Income'),
])
def test_transaction_categorization(amount, expected_category):
    """Test transaction categorization based on amount."""
    from app.services import TransactionClassifier
    
    classifier = TransactionClassifier()
    category = classifier.categorize_by_amount(amount)
    
    assert category == expected_category
```

### Testing Async Code

```python
import pytest
from app.tasks import process_import_task


@pytest.mark.asyncio
async def test_async_import_processing():
    """Test asynchronous import processing."""
    result = await process_import_task.delay('import-job-id')
    
    assert result['status'] == 'completed'
    assert result['processed_rows'] > 0
```

### Mocking External Services

```python
import pytest
from unittest.mock import Mock, patch
from app.services import EmailService


def test_email_sending_with_mock():
    """Test email sending with mocked SMTP."""
    with patch('app.services.email.smtplib.SMTP') as mock_smtp:
        # Configure mock
        mock_smtp.return_value.sendmail.return_value = {}
        
        # Test email service
        email_service = EmailService()
        result = email_service.send_email(
            to='test@example.com',
            subject='Test',
            body='Test body'
        )
        
        # Verify
        assert result is True
        mock_smtp.return_value.sendmail.assert_called_once()
```

---

## Test Coverage

### Generating Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Generate terminal coverage report
pytest --cov=app --cov-report=term

# Generate both
pytest --cov=app --cov-report=html --cov-report=term

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

**pyproject.toml:**
```toml
[tool.coverage.run]
source = ["app"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/venv/*",
    "manage.py",
    "*/settings/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
]
```

### Coverage Goals

- **Minimum Coverage**: 80%
- **Target Coverage**: 85%
- **Critical Components**: 95%+

**Critical Components:**
- Authentication and authorization
- Payment processing
- Data import and export
- Security controls
- API endpoints

### Viewing Coverage

```bash
# View coverage summary
pytest --cov=app --cov-report=term-missing

# Example output:
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
app/__init__.py                         5      0   100%
app/models.py                         125      8    94%   45-52
app/views.py                           89      5    94%   123, 156-159
app/services/import_service.py        234     12    95%   89-95, 234-239
-----------------------------------------------------------------
TOTAL                                1543     87    94%
```

---

## CI/CD Integration

### GitHub Actions

**.github/workflows/test.yml:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:17.2-alpine
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.3'
      
      - name: Install dependencies
        run: |
          pip install -r requirements/test.txt
      
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Docker Compose CI

**docker-compose.testing.yml:**
```yaml
version: '3.8'

services:
  test:
    build:
      context: .
      dockerfile: Dockerfile
    command: pytest --cov=app --cov-report=html --cov-report=term
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.testing
      - DATABASE_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis
    volumes:
      - ./htmlcov:/app/htmlcov
  
  db:
    image: postgres:17.2-alpine
    environment:
      - POSTGRES_DB=test_db
      - POSTGRES_PASSWORD=test_password
  
  redis:
    image: redis:7-alpine
```

---

## Best Practices

### 1. Test Independence

Each test should be independent and not rely on other tests.

```python
# Good
def test_user_creation(db):
    user = User.objects.create_user(email='test@example.com')
    assert user.email == 'test@example.com'

def test_user_deletion(db):
    user = User.objects.create_user(email='test@example.com')
    user_id = user.id
    user.delete()
    assert not User.objects.filter(id=user_id).exists()

# Bad - second test depends on first
def test_create_user(db):
    global created_user
    created_user = User.objects.create_user(email='test@example.com')

def test_delete_user(db):
    created_user.delete()  # Depends on previous test
```

### 2. Use Descriptive Names

```python
# Good
def test_import_job_processes_valid_csv_file():
    pass

def test_transaction_categorizer_handles_grocery_purchases():
    pass

# Bad
def test_import():
    pass

def test_categorize():
    pass
```

### 3. Test One Thing

Each test should verify one specific behavior.

```python
# Good
def test_user_can_create_account(user):
    account = Account.objects.create(user=user, name='Checking')
    assert account.user == user

def test_account_requires_name():
    with pytest.raises(ValidationError):
        Account.objects.create(name='')

# Bad - tests multiple things
def test_account_creation_and_validation(user):
    # Tests creation
    account = Account.objects.create(user=user, name='Checking')
    assert account.user == user
    
    # Tests validation
    with pytest.raises(ValidationError):
        Account.objects.create(name='')
```

### 4. Use Fixtures Wisely

```python
# Good - reusable fixtures
@pytest.fixture
def user(db):
    return User.objects.create_user(email='test@example.com')

@pytest.fixture
def account(db, user):
    return Account.objects.create(user=user, name='Checking')

# Use in tests
def test_user_has_accounts(account):
    assert account.user.accounts.count() == 1
```

### 5. Clean Up Resources

```python
import pytest
import tempfile
import os


@pytest.fixture
def temp_file():
    """Create temporary file for testing."""
    fd, path = tempfile.mkstemp()
    yield path
    # Cleanup
    os.close(fd)
    os.unlink(path)


def test_file_processing(temp_file):
    """Test processes file correctly."""
    with open(temp_file, 'w') as f:
        f.write('test data')
    
    # Test file processing
    result = process_file(temp_file)
    assert result is True
    # Fixture automatically cleans up temp_file
```

### 6. Test Error Cases

```python
def test_import_with_invalid_file_format():
    """Test import fails gracefully with invalid format."""
    with pytest.raises(ValueError, match="Unsupported file format"):
        import_file('invalid_file.xyz')

def test_transaction_with_negative_amount():
    """Test transaction handles negative amounts correctly."""
    transaction = Transaction(amount=-100.00)
    assert transaction.is_debit is True
```

### 7. Use Markers

```python
@pytest.mark.slow
def test_large_dataset_processing():
    """Test processing large dataset."""
    pass

@pytest.mark.security
def test_xss_prevention():
    """Test XSS attack prevention."""
    pass

# Run only fast tests
# pytest -m "not slow"
```

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Ensure test database is accessible
psql -U test_user -d test_db

# Reset test database
python manage.py flush --settings=config.settings.testing
```

#### Migration Issues

```bash
# Run migrations for test database
python manage.py migrate --settings=config.settings.testing

# Or use --no-migrations flag
pytest --no-migrations
```

#### Import Errors

```python
# Check Python path
import sys
print(sys.path)

# Ensure project root is in path
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

#### Fixture Not Found

```bash
# Check conftest.py location
# Fixtures should be in conftest.py in tests/ or parent directories

tests/
├── conftest.py          # Global fixtures
├── unit/
│   ├── conftest.py      # Unit test fixtures
│   └── test_models.py
```

#### Slow Tests

```bash
# Identify slow tests
pytest --durations=10

# Run in parallel
pytest -n auto

# Use --reuse-db to avoid recreating database
pytest --reuse-db
```

---

## Additional Resources

### Documentation

- **pytest**: https://docs.pytest.org/
- **pytest-django**: https://pytest-django.readthedocs.io/
- **Django Testing**: https://docs.djangoproject.com/en/5.1/topics/testing/

### Tools

- **Coverage.py**: https://coverage.readthedocs.io/
- **Factory Boy**: https://factoryboy.readthedocs.io/
- **Faker**: https://faker.readthedocs.io/

### Project-Specific

- **Test Fixtures**: `/tests/fixtures/`
- **Test Data**: `/tests/data/`
- **Test Scripts**: `/scripts/test*.sh`

---

**Last Updated:** 2025-11-24  
**Django Version:** 5.1.13  
**Python Version:** 3.12.3  
**pytest Version:** 8.3.3
