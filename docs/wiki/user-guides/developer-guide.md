# Developer Guide

This guide provides comprehensive information for developers working on the Financial Stronghold project.

## Development Environment Setup

### Prerequisites

- **Docker**: 24.0.7 or later
- **Docker Compose**: 2.18.1 or later  
- **Git**: Latest stable version
- **Python**: 3.12.5 (for local development)

### Quick Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/nullroute-commits/financial_stronghold.git
   cd financial_stronghold
   ```

2. **Start Development Environment**
   ```bash
   ./scripts/start-dev.sh
   ```

3. **Verify Installation**
   ```bash
   # Check all services are running
   docker compose -f docker-compose.development.yml ps
   
   # Access the application
   curl http://localhost:8000/health/
   ```

## Development Workflow

### Code Structure

```
financial_stronghold/
├── app/                    # Django application code
│   ├── core/              # Core functionality
│   ├── users/             # User management
│   ├── rbac/              # Role-based access control
│   └── audit/             # Audit logging
├── config/                # Django settings
│   ├── settings/          # Environment-specific settings
│   ├── urls.py           # URL configuration
│   └── wsgi.py           # WSGI configuration
├── ci/                    # CI/CD scripts and configuration
├── environments/          # Environment variable templates
├── requirements/          # Python dependencies
└── tests/                # Test suite
```

### Development Services

When you start the development environment, these services become available:

| Service | URL | Purpose |
|---------|-----|---------|
| Web Application | http://localhost:8000 | Main Django application |
| Admin Interface | http://localhost:8000/admin | Django admin (admin/admin123) |
| Database Admin | http://localhost:8080 | Adminer for database management |
| Email Testing | http://localhost:8025 | Mailhog for email testing |
| Message Queue UI | http://localhost:15672 | RabbitMQ management (guest/guest) |

### Code Quality Standards

#### Formatting and Linting

```bash
# Format code with Black
black app/ config/ --line-length 120

# Lint with Flake8
flake8 app/ config/ --max-line-length=120

# Type checking with MyPy
mypy app/ config/

# Security scanning
bandit -r app/ -f json
safety check -r requirements/base.txt
```

#### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
./scripts/pre-commit.sh
git config core.hooksPath scripts/
```

### Testing

#### Running Tests

```bash
# Run all tests
./ci/test.sh all

# Run specific test types
./ci/test.sh unit           # Unit tests only
./ci/test.sh integration    # Integration tests only

# Run tests in containerized environment
docker compose -f ci/docker-compose.ci.yml run --rm unit-tests
docker compose -f ci/docker-compose.ci.yml run --rm integration-tests
```

#### Test Structure

```
tests/
├── unit/                  # Unit tests
│   ├── test_models.py
│   ├── test_views.py
│   └── test_utils.py
├── integration/           # Integration tests
│   ├── test_api.py
│   ├── test_auth.py
│   └── test_workflows.py
└── fixtures/              # Test data
```

#### Writing Tests

```python
# Unit test example
from django.test import TestCase
from app.models import User

class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))

# Integration test example
from django.test import TransactionTestCase
from rest_framework.test import APIClient

class UserAPITest(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_user_registration(self):
        response = self.client.post('/api/users/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, 201)
```

### Debugging

#### Debug Mode

Enable debug mode for development:

```bash
# In your environment file
DEBUG=True
DJANGO_LOG_LEVEL=DEBUG
LOG_LEVEL=DEBUG
```

#### Using Django Debug Toolbar

The development environment includes Django Debug Toolbar:

1. Access any page with `?debug=1` parameter
2. Click on the debug panel on the right side
3. Review SQL queries, cache hits, and performance metrics

#### Container Debugging

```bash
# Enter a running container
docker compose -f docker-compose.development.yml exec web bash

# View logs
docker compose -f docker-compose.development.yml logs -f web

# Debug database issues
docker compose -f docker-compose.development.yml exec db psql -U postgres -d django_app_dev
```

### Database Management

#### Migrations

```bash
# Create migrations
docker compose -f docker-compose.development.yml exec web python manage.py makemigrations

# Apply migrations
docker compose -f docker-compose.development.yml exec web python manage.py migrate

# Check migration status
docker compose -f docker-compose.development.yml exec web python manage.py showmigrations
```

#### Database Console

```bash
# Access Django shell
docker compose -f docker-compose.development.yml exec web python manage.py shell

# Access database directly
docker compose -f docker-compose.development.yml exec web python manage.py dbshell
```

### Environment Configuration

#### Development Settings

Development-specific settings in `config/settings/development.py`:

```python
# Debug settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'django_app_dev',
        'USER': 'postgres',
        'PASSWORD': 'dev-password',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
    }
}
```

#### Environment Variables

Key development environment variables:

```bash
# Application
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=your-secret-key

# Database
POSTGRES_DB=django_app_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev-password

# Cache
MEMCACHED_SERVERS=memcached:11211

# Queue
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
```

### Common Development Tasks

#### Adding a New Django App

```bash
# Create new app
docker compose -f docker-compose.development.yml exec web python manage.py startapp myapp

# Add to INSTALLED_APPS in settings
# Create migrations
# Write tests
# Implement functionality
```

#### Adding Dependencies

```bash
# Add to appropriate requirements file
echo "new-package==1.0.0" >> requirements/base.txt

# Rebuild containers
docker compose -f docker-compose.development.yml build

# Restart services
docker compose -f docker-compose.development.yml up -d
```

#### Working with Async Tasks

```python
# Define a task
from app.utils.queue import task_queue

@task_queue
def process_data(data):
    # Process data asynchronously
    pass

# Use the task
process_data.delay({'key': 'value'})
```

### Troubleshooting

#### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill the process or change port in docker-compose
   ```

2. **Database Connection Issues**
   ```bash
   # Check database logs
   docker compose -f docker-compose.development.yml logs db
   
   # Restart database
   docker compose -f docker-compose.development.yml restart db
   ```

3. **Cache Issues**
   ```bash
   # Clear cache
   docker compose -f docker-compose.development.yml exec web python manage.py clear_cache
   
   # Restart Memcached
   docker compose -f docker-compose.development.yml restart memcached
   ```

#### Getting Help

- Check the [Troubleshooting Guide](../troubleshooting/index.md)
- Review [FAQ](../faq.md)
- Open an issue on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)
- Join our development chat (link in README)

## Contributing

See our [Contributing Guidelines](../../CONTRIBUTING.md) for information on:

- Code review process
- Branch naming conventions  
- Commit message format
- Pull request guidelines