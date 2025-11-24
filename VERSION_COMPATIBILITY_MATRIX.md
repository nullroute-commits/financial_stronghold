# Version Compatibility Matrix

**Last Updated:** 2025-11-22  
**Python Version:** 3.12.3  
**Django Version:** 5.1.13

## Core Framework Versions

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| Python | 3.12.3 | ✅ Stable | Ubuntu 24.04 default |
| Django | 5.1.13 | ✅ Stable | Latest stable release |
| PostgreSQL | 17.2 | ✅ Stable | Alpine-based image |
| Nginx | 1.24 | ✅ Stable | Alpine-based image |

## Cache & Queue Services

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| Redis | 7 (latest) | ✅ Stable | Alpine-based image |
| Memcached | 1.6 (latest) | ✅ Stable | Alpine-based image |
| RabbitMQ | 3.12 (latest) | ✅ Stable | Alpine-based image |

## Python Dependencies

### Core Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| Django | 5.1.13 | ✅ Compatible | Latest stable |
| psycopg2-binary | 2.9.10 | ✅ Compatible | PostgreSQL adapter |
| python-memcached | 1.59 | ✅ Compatible | Memcached client |
| pika | 1.3.2 | ✅ Compatible | RabbitMQ client |
| gunicorn | 23.0.0 | ✅ Compatible | WSGI server |
| djangorestframework | 3.15.2 | ✅ Compatible | REST API framework |
| django-cors-headers | 4.6.0 | ✅ Compatible | CORS support |

### Import Feature Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| celery | 5.4.0 | ✅ Compatible | Async task queue |
| redis | 5.2.1 | ✅ Compatible | Redis client |
| pandas | 2.2.3 | ✅ Compatible | Data manipulation |
| openpyxl | 3.1.5 | ✅ Compatible | Excel support |
| python-magic | 0.4.27 | ✅ Compatible | File type detection |
| PyPDF2 | 3.0.1 | ✅ Compatible | PDF parsing |
| pdfplumber | 0.11.4 | ✅ Compatible | PDF data extraction |

### Machine Learning Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| numpy | 1.26.4 | ✅ Compatible | **UPGRADED** from 1.24.4 |
| scikit-learn | 1.4.2 | ✅ Compatible | **UPGRADED** from 1.3.2 |

### Development Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| black | 24.3.0 | ✅ Compatible | Code formatter |
| flake8 | 7.1.1 | ✅ Compatible | **UPGRADED** from 6.1.0 |
| mypy | 1.13.0 | ✅ Compatible | **UPGRADED** from 1.5.1 |
| django-stubs | 5.1.1 | ✅ Compatible | **UPGRADED** from 4.2.6 |
| django-debug-toolbar | 4.4.6 | ✅ Compatible | **UPGRADED** from 4.2.0 |
| pytest | 8.3.3 | ✅ Compatible | **UPGRADED** from 7.4.3 |
| pytest-django | 4.9.0 | ✅ Compatible | **UPGRADED** from 4.7.0 |
| pytest-cov | 6.0.0 | ✅ Compatible | **UPGRADED** from 4.1.0 |
| factory-boy | 3.3.1 | ✅ Compatible | **UPGRADED** from 3.3.0 |

### Documentation Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| mkdocs | 1.6.1 | ✅ Compatible | **UPGRADED** from 1.5.3 |
| mkdocs-material | 9.5.47 | ✅ Compatible | **UPGRADED** from 9.4.8 |
| pymdown-extensions | 10.12 | ✅ Compatible | **UPGRADED** from 10.7 |

### Production Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| sentry-sdk | 2.18.0 | ✅ Compatible | **UPGRADED** from 1.45.1 |
| whitenoise | 6.8.2 | ✅ Compatible | **UPGRADED** from 6.5.0 |
| python-json-logger | 2.0.7 | ✅ Compatible | Structured logging |
| psutil | 5.9.6 | ✅ Compatible | System monitoring |

### Testing & CI/CD Dependencies

| Package | Version | Python 3.12.3 | Notes |
|---------|---------|---------------|-------|
| docker | 7.1.0 | ✅ Compatible | **UPGRADED** from 6.1.3 |
| PyJWT | 2.10.1 | ✅ Compatible | **UPGRADED** from 2.8.0 |
| PyYAML | 6.0.2 | ✅ Compatible | **UPGRADED** from 6.0.1 |
| markdown | 3.7 | ✅ Compatible | **UPGRADED** from 3.5.1 |

## Known Compatibility Issues

### Resolved Issues

1. **NumPy 1.24.4 → 1.26.4**
   - **Issue:** NumPy 1.24.4 not compatible with Python 3.12.3
   - **Resolution:** Upgraded to 1.26.4 which has full Python 3.12 support
   - **Impact:** Import feature ML functionality

2. **scikit-learn 1.3.2 → 1.4.2**
   - **Issue:** Build issues with Python 3.12.3
   - **Resolution:** Upgraded to 1.4.2 with Python 3.12 support
   - **Impact:** Transaction classification ML model

3. **Black 23.9.1 vs 24.3.0**
   - **Issue:** Version mismatch between pyproject.toml and requirements
   - **Resolution:** Standardized to 24.3.0 across all files
   - **Impact:** Code formatting consistency

### Outstanding Issues

1. **pylibmc and uwsgi**
   - **Status:** Commented out in production requirements
   - **Reason:** Python 3.12 compatibility issues
   - **Workaround:** Using python-memcached instead
   - **Future:** Wait for upstream Python 3.12 support

## Docker Image Versions

| Service | Base Image | Version | Platform Support |
|---------|-----------|---------|------------------|
| Web App | python | 3.12.3-slim | linux/amd64, linux/arm64 |
| PostgreSQL | postgres | 17.2-alpine | linux/amd64, linux/arm64 |
| Redis | redis | 7-alpine | linux/amd64, linux/arm64 |
| Memcached | memcached | 1.6-alpine | linux/amd64, linux/arm64 |
| RabbitMQ | rabbitmq | 3.12-alpine | linux/amd64, linux/arm64 |
| Nginx | nginx | 1.24-alpine | linux/amd64, linux/arm64 |

## Verification Commands

### Check Python Version
```bash
python --version
# Expected: Python 3.12.3
```

### Check Django Version
```bash
python -m django --version
# Expected: 5.1.13
```

### Check All Package Versions
```bash
pip list | grep -E "Django|numpy|scikit-learn|black|pytest"
```

### Verify Database Connection
```bash
docker-compose exec db psql --version
# Expected: psql (PostgreSQL) 17.2
```

### Verify Service Versions
```bash
# Redis
docker-compose exec redis redis-server --version

# Memcached
docker-compose exec memcached memcached --version

# RabbitMQ
docker-compose exec rabbitmq rabbitmqctl version
```

## Migration Notes

### Upgrading from Previous Versions

1. **NumPy 1.24.x → 1.26.4**
   ```bash
   pip install --upgrade numpy==1.26.4
   ```

2. **scikit-learn 1.3.x → 1.4.2**
   ```bash
   pip install --upgrade scikit-learn==1.4.2
   ```

3. **All Dependencies**
   ```bash
   pip install -r requirements/base.txt --upgrade
   ```

## Testing Matrix

| Test Type | Python 3.12.3 | Status |
|-----------|---------------|--------|
| Unit Tests | ✅ | All passing |
| Integration Tests | ⏳ | Pending verification |
| Performance Tests | ⏳ | Pending verification |
| Security Tests | ⏳ | Pending verification |

## Support & Compatibility Timeline

- **Python 3.12**: Supported until October 2028
- **Django 5.1**: Supported until December 2025 (6.0 LTS expected April 2026)
- **PostgreSQL 17**: Supported until November 2029
- **All dependencies**: Using latest stable versions as of 2025-11-22

## References

- [Python Release Schedule](https://www.python.org/dev/peps/pep-0693/)
- [Django Supported Versions](https://www.djangoproject.com/download/#supported-versions)
- [PostgreSQL Versioning Policy](https://www.postgresql.org/support/versioning/)
- [NumPy Python 3.12 Support](https://numpy.org/devdocs/release.html)
- [scikit-learn Python 3.12 Support](https://scikit-learn.org/stable/whats_new.html)

---

**Note:** This compatibility matrix is actively maintained and updated as new versions are tested and verified.
