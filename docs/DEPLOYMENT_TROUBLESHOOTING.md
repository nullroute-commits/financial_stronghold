# Comprehensive Deployment Troubleshooting Guide

## Overview

This guide provides systematic troubleshooting procedures for the dockerized CI/CD deployment stages in the Financial Stronghold application.

## Quick Diagnosis Tools

### 1. Enhanced Debug Validation
```bash
# Run comprehensive debugging for all environments
./ci/enhanced-debug-validation.sh all

# Debug specific environment
./ci/enhanced-debug-validation.sh development
```

### 2. Service-Specific Validation
```bash
# Test individual services in isolation
./ci/service-validation.sh development

# Test all environments
./ci/service-validation.sh all
```

### 3. Health Monitoring
```bash
# Single health check
./ci/health-monitor.sh once

# Continuous monitoring
./ci/health-monitor.sh continuous
```

## Common Issues and Solutions

### Issue 1: Missing Dependencies

**Symptoms:**
- `ModuleNotFoundError: No module named 'yaml'`
- `ModuleNotFoundError: No module named 'markdown'`
- Import errors during test collection

**Solution:**
Dependencies have been added to all requirements files:
- `PyYAML==6.0.1` - For YAML parsing in tests
- `markdown==3.5.1` - For documentation validation

**Verification:**
```bash
# Check requirements files
grep -r "PyYAML\|markdown" requirements/
```

### Issue 2: Missing Schema Definitions

**Symptoms:**
- `ImportError: cannot import name 'UserCreateSchema' from 'app.schemas'`
- Test collection failures due to missing schema classes

**Solution:**
Added comprehensive schema definitions in `app/schemas.py`:
- User schemas: `UserCreateSchema`, `UserUpdateSchema`, `UserResponseSchema`
- Tenant schemas: `TenantCreateSchema`, `TenantUpdateSchema`, `TenantResponseSchema`
- Schema aliases for backward compatibility

**Verification:**
```bash
# Check schema definitions
grep -E "(UserCreateSchema|TenantCreateSchema)" app/schemas.py
```

### Issue 3: Container Startup Issues

**Symptoms:**
- Services fail to start
- Health checks timeout
- Database connection failures

**Diagnosis Steps:**
1. Check individual service status:
   ```bash
   docker compose -f docker-compose.development.yml ps
   ```

2. View service logs:
   ```bash
   docker compose -f docker-compose.development.yml logs web
   docker compose -f docker-compose.development.yml logs db
   ```

3. Test service isolation:
   ```bash
   ./ci/service-validation.sh development
   ```

**Common Solutions:**
- **Database not ready**: Increase startup wait times in entrypoint scripts
- **Port conflicts**: Check for existing services on ports 8000-8003, 5432, 11211, 5672
- **Memory issues**: Increase Docker memory allocation
- **Network issues**: Restart Docker daemon, check network connectivity

### Issue 4: Test Collection and Execution

**Symptoms:**
- Django test runner errors
- Import errors in test modules
- Test discovery failures

**Enhanced Test Collection:**
The validation script now uses proper Django test discovery:
```python
from django.test.utils import get_runner
from django.conf import settings
TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=0, interactive=False)
loader = test_runner.test_loader
suite = loader.discover('tests', pattern='test*.py')
```

**Manual Test Debugging:**
```bash
# Test within container
docker compose -f docker-compose.development.yml exec web python manage.py test --verbosity=2

# Check test discovery
docker compose -f docker-compose.development.yml exec web python -c "
import django
django.setup()
from django.test.utils import get_runner
from django.conf import settings
TestRunner = get_runner(settings)
print('Test runner available')
"
```

### Issue 5: Health Check Failures

**Symptoms:**
- `/health/` endpoint returning 503
- Health checks timing out
- Service dependency failures

**Debugging Steps:**
1. Check endpoint accessibility:
   ```bash
   curl -v http://localhost:8000/health/
   ```

2. Examine health check implementation:
   ```bash
   grep -A 20 "health_check" config/urls.py
   ```

3. Test individual components:
   ```bash
   # Database connection
   docker compose exec web python -c "
   import django; django.setup()
   from django.db import connection
   cursor = connection.cursor()
   cursor.execute('SELECT 1')
   print('DB OK')
   "
   
   # Cache connection
   docker compose exec web python -c "
   import django; django.setup()
   from django.core.cache import cache
   cache.set('test', 'ok', 10)
   print('Cache OK' if cache.get('test') == 'ok' else 'Cache FAIL')
   "
   ```

## Environment-Specific Troubleshooting

### Development Environment (Port 8000)
**Common Issues:**
- Debug mode causing performance issues
- Development tools not loading
- Hot reloading not working

**Configuration Check:**
```bash
# Verify development settings
docker compose -f docker-compose.development.yml exec web python -c "
from django.conf import settings
print(f'DEBUG: {settings.DEBUG}')
print(f'Environment: {settings.ENVIRONMENT}')
"
```

### Testing Environment (Port 8001)
**Common Issues:**
- Test database not using tmpfs
- Test isolation failures
- Parallel test conflicts

**Optimization:**
- Uses tmpfs for faster database operations
- Dedicated test runner service
- Isolated test environment variables

### Staging Environment (Port 8003)
**Common Issues:**
- Production-like settings causing issues
- Resource constraints
- Load balancing configuration

**Monitoring:**
```bash
# Check staging resources
docker compose -f docker-compose.staging.yml exec web python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"
```

### Production Environment (Port 8002)
**Common Issues:**
- Security restrictions
- Performance bottlenecks
- Monitoring and logging

**Security Validation:**
- SSL/TLS configuration
- Environment variable protection
- Access control verification

## Performance Optimization

### Database Optimization
```bash
# Check database performance
docker compose -f docker-compose.production.yml exec db psql -U postgres -c "
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
FROM pg_stat_database 
WHERE datname = 'django_app_prod';
"
```

### Cache Optimization
```bash
# Monitor cache hit rates
echo "stats" | nc localhost 11211 | grep -E "(cmd_get|cmd_set|get_hits|get_misses)"
```

### Resource Monitoring
```bash
# Container resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

## Rollback Procedures

### Quick Rollback
```bash
# Stop problematic deployment
docker compose -f docker-compose.production.yml down

# Revert to previous stable image
docker tag registry/django-app:previous-stable registry/django-app:latest

# Restart with stable version
docker compose -f docker-compose.production.yml up -d
```

### Database Rollback
```bash
# Restore database backup
./scripts/restore-database.sh production backup_timestamp

# Verify data integrity
./scripts/verify-data-integrity.sh production
```

## Monitoring and Alerting

### Real-time Monitoring
```bash
# Continuous health monitoring
./ci/health-monitor.sh continuous

# Set monitoring interval (seconds)
MONITOR_INTERVAL=60 ./ci/health-monitor.sh continuous
```

### Log Aggregation
```bash
# Centralized logging
docker compose -f docker-compose.production.yml logs -f --tail=100

# Service-specific logs
docker compose -f docker-compose.production.yml logs web -f
```

### Alert Configuration
- **Health check failures**: Immediate notification
- **Resource thresholds**: CPU > 80%, Memory > 90%
- **Error rates**: > 5% error rate in 5-minute window
- **Response times**: > 2s average response time

## Best Practices

1. **Always run validation before deployment:**
   ```bash
   ./ci/enhanced-debug-validation.sh production
   ```

2. **Use service isolation for debugging:**
   ```bash
   ./ci/service-validation.sh development
   ```

3. **Monitor deployment health:**
   ```bash
   ./ci/health-monitor.sh once
   ```

4. **Keep logs and debugging information:**
   - All scripts generate detailed logs
   - Debug reports are automatically generated
   - Service validation provides isolation testing

5. **Regular maintenance:**
   - Clean up unused Docker images and volumes
   - Monitor resource usage trends
   - Update dependencies regularly
   - Test rollback procedures

## Emergency Contacts and Procedures

### Critical Issues
1. **Stop all environments:**
   ```bash
   for env in development testing staging production; do
       docker compose -f docker-compose.$env.yml down
   done
   ```

2. **System resource check:**
   ```bash
   # Check system resources
   free -h
   df -h
   docker system df
   ```

3. **Network diagnostics:**
   ```bash
   # Check port availability
   netstat -tulpn | grep -E "(8000|8001|8002|8003|5432|11211|5672)"
   ```

This troubleshooting guide provides comprehensive coverage of common deployment issues and their solutions, leveraging the enhanced debugging tools created to systematically identify and resolve problems.