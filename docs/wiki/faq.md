# Frequently Asked Questions (FAQ)

Common questions and answers about Financial Stronghold.

## General Questions

### What is Financial Stronghold?

Financial Stronghold is a comprehensive Django 5 application with multi-architecture CI/CD pipeline support. It features:
- Django 5.1.13 with Python 3.12.3
- PostgreSQL 17.2 database
- Containerized deployment with Docker
- Role-based access control (RBAC)
- Audit logging system
- Multi-architecture support (AMD64, ARM64)

### What are the system requirements?

**Minimum Requirements:**
- Docker 24.0.7+
- Docker Compose 2.18.1+
- 4GB RAM
- 20GB disk space
- Git

**Recommended for Production:**
- 8GB+ RAM
- 100GB+ SSD storage
- 4+ CPU cores
- SSL certificates

### Is Financial Stronghold free to use?

Yes, Financial Stronghold is open source and available under the MIT License. See the [LICENSE](../../LICENSE) file for details.

## Installation and Setup

### How do I install Financial Stronghold?

1. **Quick Start (Development):**
   ```bash
   git clone https://github.com/nullroute-commits/financial_stronghold.git
   cd financial_stronghold
   ./scripts/start-dev.sh
   ```

2. **Production Deployment:**
   ```bash
   git clone https://github.com/nullroute-commits/financial_stronghold.git
   cd financial_stronghold
   cp environments/.env.production.example .env.production
   # Edit .env.production with your values
   ./scripts/start-prod.sh
   ```

### What ports does Financial Stronghold use?

**Development Environment:**
- 8000: Web application
- 8080: Database admin (Adminer)
- 8025: Email testing (Mailhog)
- 15672: RabbitMQ management
- 5432: PostgreSQL (internal)
- 11211: Memcached (internal)

**Production Environment:**
- 80: HTTP (redirects to HTTPS)
- 443: HTTPS
- Internal ports are not exposed

### How do I access the admin interface?

1. Start the application
2. Go to: http://localhost:8000/admin
3. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`

**Note**: Change these credentials in production!

### Can I run Financial Stronghold without Docker?

While the application is designed for Docker deployment, you can run it natively with:
- Python 3.12.3
- PostgreSQL 17.2
- Memcached 1.6.22
- RabbitMQ 3.12.8

However, we strongly recommend using Docker for consistency and easier deployment.

## Development Questions

### How do I set up a development environment?

1. **Clone and start:**
   ```bash
   git clone https://github.com/nullroute-commits/financial_stronghold.git
   cd financial_stronghold
   ./scripts/start-dev.sh
   ```

2. **Verify installation:**
   ```bash
   curl http://localhost:8000/health/
   ```

See the [Developer Guide](user-guides/developer-guide.md) for detailed instructions.

### How do I run tests?

```bash
# Run all tests
./ci/test.sh all

# Run specific test types
./ci/test.sh unit           # Unit tests only
./ci/test.sh integration    # Integration tests only

# Run in containerized environment
docker compose -f ci/docker-compose.ci.yml run --rm unit-tests
```

### How do I add new dependencies?

1. **Add to requirements file:**
   ```bash
   echo "new-package==1.0.0" >> requirements/base.txt
   ```

2. **Rebuild containers:**
   ```bash
   docker compose -f docker-compose.development.yml build
   docker compose -f docker-compose.development.yml up -d
   ```

### How do I create database migrations?

```bash
# Create migrations
docker compose -f docker-compose.development.yml exec web python manage.py makemigrations

# Apply migrations
docker compose -f docker-compose.development.yml exec web python manage.py migrate
```

### How do I access the Django shell?

```bash
docker compose -f docker-compose.development.yml exec web python manage.py shell
```

## Deployment Questions

### How do I deploy to production?

1. **Configure environment:**
   ```bash
   cp environments/.env.production.example .env.production
   # Edit with your production values
   ```

2. **Deploy:**
   ```bash
   ./scripts/start-prod.sh
   ```

See the [System Administrator Guide](user-guides/sysadmin-guide.md) for complete instructions.

### How do I configure SSL/HTTPS?

1. **Obtain SSL certificates** (Let's Encrypt, commercial CA, etc.)

2. **Place certificates:**
   ```bash
   mkdir -p nginx/ssl
   cp your-cert.pem nginx/ssl/cert.pem
   cp your-key.pem nginx/ssl/key.pem
   chmod 600 nginx/ssl/key.pem
   ```

3. **Update configuration** in `docker-compose.production.yml`

### How do I scale the application?

```bash
# Scale web workers
docker compose -f docker-compose.production.yml up -d --scale web=3

# Scale with Docker Swarm
docker stack deploy -c docker-compose.swarm.yml financial-stronghold
```

### How do I backup the database?

```bash
# Create backup
docker compose -f docker-compose.production.yml exec -T db pg_dump -U django_user django_app_prod | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore backup
gunzip -c backup_20240101.sql.gz | docker compose -f docker-compose.production.yml exec -T db psql -U django_user django_app_prod
```

## CI/CD Questions

### How does the CI/CD pipeline work?

The pipeline has 5 stages:
1. **Lint**: Code quality checks
2. **Test**: Unit and integration tests
3. **Build**: Multi-architecture Docker builds
4. **Security**: Vulnerability scanning
5. **Deploy**: Environment deployment

### How do I run the CI/CD pipeline locally?

```bash
# Run complete pipeline
docker compose -f ci/docker-compose.ci.yml up

# Run individual stages
./ci/lint.sh
./ci/test.sh
./ci/build.sh
```

### How do I customize the pipeline?

1. **Modify CI scripts** in the `ci/` directory
2. **Update Docker Compose** configuration in `ci/docker-compose.ci.yml`
3. **Add custom stages** following existing patterns

See the [DevOps Guide](user-guides/devops-guide.md) for details.

### How do I deploy to different environments?

```bash
# Deploy to development
./ci/deploy.sh development

# Deploy to staging
./ci/deploy.sh staging

# Deploy to production (requires approval)
./ci/deploy.sh production
```

## Performance Questions

### How do I optimize performance?

1. **Database optimization:**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX CONCURRENTLY idx_user_email ON auth_user(email);
   ```

2. **Cache optimization:**
   ```python
   # Use cache decorators
   from django.views.decorators.cache import cache_page
   
   @cache_page(60 * 15)  # Cache for 15 minutes
   def my_view(request):
       # View logic
   ```

3. **Scale horizontally:**
   ```bash
   docker compose -f docker-compose.production.yml up -d --scale web=3
   ```

### Why is the application slow?

Common causes and solutions:

1. **Database issues:**
   - Add missing indexes
   - Optimize queries
   - Check connection pool settings

2. **Resource constraints:**
   - Increase container memory limits
   - Scale horizontally
   - Monitor with `docker stats`

3. **Cache issues:**
   - Verify Memcached is running
   - Check cache hit rates
   - Restart cache service

### How do I monitor performance?

```bash
# Container resource usage
docker stats

# Application health
curl http://localhost:8000/health/

# Database performance
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Cache statistics
echo "stats" | nc localhost 11211
```

## Security Questions

### How do I secure the application?

1. **Change default passwords:**
   ```bash
   docker compose -f docker-compose.production.yml exec web python manage.py changepassword admin
   ```

2. **Configure HTTPS** (see SSL/HTTPS section above)

3. **Use strong secrets:**
   ```bash
   # Generate secure secret key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Regular updates:**
   ```bash
   # Update dependencies
   pip-audit -r requirements/production.txt
   
   # Scan containers
   trivy image django-app:production
   ```

### How does authentication work?

Financial Stronghold uses Django's built-in authentication with enhancements:
- Role-based access control (RBAC)
- Session-based authentication
- Password validation
- Audit logging for authentication events

### How do I manage user permissions?

1. **Via Admin Interface:**
   - Go to http://localhost:8000/admin
   - Manage users, groups, and permissions

2. **Via Code:**
   ```python
   from django.contrib.auth.decorators import permission_required
   
   @permission_required('app.view_model')
   def my_view(request):
       # View logic
   ```

## Troubleshooting Questions

### Why won't the application start?

Common issues:

1. **Port conflicts:**
   ```bash
   lsof -i :8000  # Check what's using port 8000
   ```

2. **Docker issues:**
   ```bash
   docker system prune -f  # Clean up Docker
   ```

3. **Permission issues:**
   ```bash
   chmod +x scripts/*.sh  # Fix script permissions
   ```

See the [Troubleshooting Guide](troubleshooting/index.md) for complete solutions.

### How do I view logs?

```bash
# All services
docker compose -f docker-compose.development.yml logs -f

# Specific service
docker compose -f docker-compose.development.yml logs -f web

# Recent logs only
docker compose -f docker-compose.development.yml logs --tail=50
```

### How do I reset the database?

**⚠️ Warning: This will delete all data!**

```bash
# For development
docker compose -f docker-compose.development.yml down -v
docker compose -f docker-compose.development.yml up -d

# For specific database reset
docker compose -f docker-compose.development.yml exec db dropdb -U postgres django_app_dev
docker compose -f docker-compose.development.yml exec db createdb -U postgres django_app_dev
docker compose -f docker-compose.development.yml exec web python manage.py migrate
```

### How do I fix "Database is unavailable" errors?

1. **Check database service:**
   ```bash
   docker compose -f docker-compose.development.yml logs db
   ```

2. **Restart database:**
   ```bash
   docker compose -f docker-compose.development.yml restart db
   ```

3. **Test connection:**
   ```bash
   docker compose -f docker-compose.development.yml exec web python manage.py check --database default
   ```

## Architecture Questions

### What's the system architecture?

Financial Stronghold uses a multi-tier architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Presentation   │    │   Application   │    │      Data       │
│     Layer       │    │     Layer       │    │     Layer       │
│                 │    │                 │    │                 │
│ • Nginx         │───▶│ • Django        │───▶│ • PostgreSQL    │
│ • Load Balancer │    │ • RBAC          │    │ • Memcached     │
│ • SSL/TLS       │    │ • Audit Logging │    │ • RabbitMQ      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### How are containers organized?

Each environment has its own Docker Compose configuration:
- `docker-compose.development.yml`: Development environment
- `docker-compose.testing.yml`: Testing environment
- `docker-compose.staging.yml`: Staging environment
- `docker-compose.production.yml`: Production environment
- `ci/docker-compose.ci.yml`: CI/CD pipeline

### What databases are supported?

Currently supported:
- **PostgreSQL 17.2** (primary, recommended)
- SQLite (development/testing only)

Other databases can be configured by modifying Django settings.

### How does caching work?

Financial Stronghold uses Memcached for:
- Session storage
- Query result caching
- Template fragment caching
- Custom application caching

## Support Questions

### Where can I get help?

1. **Documentation**: Check the [User Guides](user-guides/index.md)
2. **Troubleshooting**: Review the [Troubleshooting Guide](troubleshooting/index.md)
3. **GitHub Issues**: [Open an issue](https://github.com/nullroute-commits/financial_stronghold/issues)
4. **Architecture**: Review [System Architecture](architecture/index.md)

### How do I report bugs?

1. **Search existing issues** on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)
2. **Create a new issue** with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
   - Log files (if applicable)

### How do I contribute?

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Submit a pull request**

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for detailed guidelines.

### How do I request new features?

1. **Check existing issues** for similar requests
2. **Open a feature request** on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)
3. **Describe the use case** and expected behavior
4. **Consider contributing** the feature yourself

## Licensing Questions

### What license is Financial Stronghold under?

Financial Stronghold is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for full details.

### Can I use it commercially?

Yes, the MIT License allows commercial use, modification, and distribution.

### Can I modify the code?

Yes, you can modify the code for any purpose. We encourage contributions back to the project!

---

**Still have questions?** Check our [User Guides](user-guides/index.md) or [open an issue](https://github.com/nullroute-commits/financial_stronghold/issues).