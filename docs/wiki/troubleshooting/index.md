# Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with Financial Stronghold.

## Quick Diagnosis

### System Health Check

Run these commands to quickly assess system health:

```bash
# 1. Check if all services are running
docker compose -f docker-compose.development.yml ps

# 2. Test application health
curl http://localhost:8000/health/

# 3. Check Docker system resources
docker system df

# 4. View recent logs
docker compose -f docker-compose.development.yml logs --tail=50
```

### Common Symptoms and Quick Fixes

| Symptom | Quick Fix | Details |
|---------|-----------|---------|
| Application won't start | `docker compose down && docker compose up -d` | [Service Startup Issues](#service-startup-issues) |
| Port already in use | `lsof -i :8000` then kill process | [Port Conflicts](#port-conflicts) |
| Database connection error | `docker compose restart db` | [Database Issues](#database-issues) |
| Slow performance | `docker stats` to check resources | [Performance Issues](#performance-issues) |
| Build failures | `docker system prune -f` | [Build and Image Issues](#build-and-image-issues) |

## Service Startup Issues

### Services Won't Start

**Symptoms:**
- Services exit immediately after starting
- "Container exited with code 1" errors
- Services stuck in "starting" state

**Diagnosis:**
```bash
# Check service status
docker compose -f docker-compose.development.yml ps

# View detailed logs
docker compose -f docker-compose.development.yml logs [service_name]

# Check for resource constraints
docker system df
free -h
df -h
```

**Solutions:**

1. **Clear Docker Cache**
   ```bash
   docker system prune -f
   docker compose -f docker-compose.development.yml down -v
   docker compose -f docker-compose.development.yml up -d
   ```

2. **Check Environment Variables**
   ```bash
   # Verify environment file exists
   ls -la .env*
   
   # Check for missing variables
   docker compose -f docker-compose.development.yml config
   ```

3. **Rebuild Images**
   ```bash
   docker compose -f docker-compose.development.yml build --no-cache
   docker compose -f docker-compose.development.yml up -d
   ```

### Service Dependencies

**Issue:** Services start but can't communicate

**Solution:**
```bash
# Check network connectivity
docker network ls
docker network inspect financial_stronghold_default

# Restart with dependency order
docker compose -f docker-compose.development.yml down
docker compose -f docker-compose.development.yml up -d db memcached rabbitmq
sleep 10
docker compose -f docker-compose.development.yml up -d web
```

## Port Conflicts

### Port Already in Use

**Symptoms:**
- "Port already in use" errors
- Cannot bind to port messages
- Connection refused errors

**Diagnosis:**
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5432
lsof -i :11211

# Check all listening ports
netstat -tlnp | grep LISTEN
```

**Solutions:**

1. **Kill Conflicting Process**
   ```bash
   # Find and kill process using port 8000
   sudo lsof -t -i :8000 | xargs sudo kill -9
   ```

2. **Change Application Ports**
   ```yaml
   # In docker-compose.development.yml
   services:
     web:
       ports:
         - "8001:8000"  # Change external port to 8001
   ```

3. **Use Different Environment**
   ```bash
   # Use testing environment with different ports
   docker compose -f docker-compose.testing.yml up -d
   ```

## Database Issues

### Connection Failures

**Symptoms:**
- Database connection timeout
- "Database is unavailable" errors
- Authentication failures

**Diagnosis:**
```bash
# Check database service
docker compose -f docker-compose.development.yml logs db

# Test direct connection
docker compose -f docker-compose.development.yml exec db psql -U postgres -d django_app_dev

# Check database process
docker compose -f docker-compose.development.yml exec db ps aux
```

**Solutions:**

1. **Restart Database Service**
   ```bash
   docker compose -f docker-compose.development.yml restart db
   sleep 10
   docker compose -f docker-compose.development.yml restart web
   ```

2. **Check Database Configuration**
   ```bash
   # Verify environment variables
   docker compose -f docker-compose.development.yml exec web printenv | grep POSTGRES
   
   # Check database settings
   docker compose -f docker-compose.development.yml exec web python manage.py check --database default
   ```

3. **Recreate Database**
   ```bash
   # ⚠️ This will delete all data
   docker compose -f docker-compose.development.yml down -v
   docker compose -f docker-compose.development.yml up -d
   ```

### Migration Issues

**Symptoms:**
- Migration failures
- Database schema errors
- "Table doesn't exist" errors

**Solutions:**

1. **Reset Migrations**
   ```bash
   # Check migration status
   docker compose -f docker-compose.development.yml exec web python manage.py showmigrations
   
   # Apply migrations
   docker compose -f docker-compose.development.yml exec web python manage.py migrate
   ```

2. **Create Initial Migrations**
   ```bash
   docker compose -f docker-compose.development.yml exec web python manage.py makemigrations
   docker compose -f docker-compose.development.yml exec web python manage.py migrate
   ```

### Database Performance

**Symptoms:**
- Slow query responses
- High database CPU usage
- Connection pool exhaustion

**Diagnosis:**
```sql
-- Connect to database
docker compose -f docker-compose.development.yml exec db psql -U postgres -d django_app_dev

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**Solutions:**

1. **Optimize Database Settings**
   ```bash
   # Increase connection limits (in docker-compose)
   environment:
     - POSTGRES_MAX_CONNECTIONS=200
   ```

2. **Add Database Indexes**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX CONCURRENTLY idx_user_email ON auth_user(email);
   ```

## Build and Image Issues

### Build Failures

**Symptoms:**
- Docker build errors
- Package installation failures
- Permission denied errors

**Diagnosis:**
```bash
# Check build logs
docker compose -f docker-compose.development.yml build web

# Check Dockerfile syntax
docker run --rm -i hadolint/hadolint < Dockerfile

# Check disk space
df -h
```

**Solutions:**

1. **Clear Build Cache**
   ```bash
   docker builder prune -f
   docker system prune -f
   docker compose -f docker-compose.development.yml build --no-cache
   ```

2. **Fix Package Issues**
   ```bash
   # Update package lists
   docker compose -f docker-compose.development.yml build --pull
   
   # Check requirements files
   cat requirements/development.txt
   ```

3. **Permission Issues**
   ```bash
   # Fix file permissions
   chmod +x scripts/*.sh
   sudo chown -R $USER:$USER .
   ```

### Image Size Issues

**Issue:** Docker images are too large

**Solutions:**

1. **Use Multi-stage Builds**
   ```dockerfile
   # Already implemented in Dockerfile
   FROM python:3.12.5-slim as base
   # ... base setup
   
   FROM base as production
   # ... production optimizations
   ```

2. **Clean Up Build Cache**
   ```bash
   # Remove unused images
   docker image prune -f
   
   # Remove all unused Docker objects
   docker system prune -a -f
   ```

## Performance Issues

### Slow Application Response

**Symptoms:**
- High response times
- Timeouts
- Unresponsive interface

**Diagnosis:**
```bash
# Check container resource usage
docker stats --no-stream

# Check application logs
docker compose -f docker-compose.development.yml logs web | grep ERROR

# Test specific endpoints
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health/
```

**Solutions:**

1. **Increase Resource Limits**
   ```yaml
   # In docker-compose.development.yml
   services:
     web:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '1.0'
   ```

2. **Optimize Database Queries**
   ```python
   # Enable SQL debugging
   LOGGING = {
       'loggers': {
           'django.db.backends': {
               'level': 'DEBUG',
               'handlers': ['console'],
           }
       }
   }
   ```

3. **Check Cache Performance**
   ```bash
   # Test Memcached
   echo "stats" | nc localhost 11211
   
   # Restart cache if needed
   docker compose -f docker-compose.development.yml restart memcached
   ```

### Memory Issues

**Symptoms:**
- Out of memory errors
- Container crashes
- System slowdown

**Solutions:**

1. **Monitor Memory Usage**
   ```bash
   # Check system memory
   free -h
   
   # Check container memory
   docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"
   ```

2. **Increase Memory Limits**
   ```yaml
   # In docker-compose file
   services:
     web:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

3. **Optimize Application**
   ```python
   # Reduce database connection pool
   DATABASES['default']['CONN_MAX_AGE'] = 60
   DATABASES['default']['OPTIONS'] = {
       'MAX_CONNS': 10,
   }
   ```

## Network and Connectivity Issues

### Internal Service Communication

**Symptoms:**
- Services can't reach each other
- DNS resolution failures
- Connection timeouts between services

**Diagnosis:**
```bash
# Check Docker networks
docker network ls
docker network inspect financial_stronghold_default

# Test service connectivity
docker compose -f docker-compose.development.yml exec web ping db
docker compose -f docker-compose.development.yml exec web nslookup memcached
```

**Solutions:**

1. **Restart Network Stack**
   ```bash
   docker compose -f docker-compose.development.yml down
   docker network prune -f
   docker compose -f docker-compose.development.yml up -d
   ```

2. **Use Service Names**
   ```python
   # In settings, use service names not localhost
   DATABASES = {
       'default': {
           'HOST': 'db',  # Not 'localhost'
       }
   }
   ```

### External Connectivity

**Issue:** Application can't reach external services

**Solutions:**

1. **Check DNS Resolution**
   ```bash
   docker compose -f docker-compose.development.yml exec web nslookup google.com
   ```

2. **Configure Proxy (if needed)**
   ```yaml
   # In docker-compose file
   services:
     web:
       environment:
         - HTTP_PROXY=http://proxy.company.com:8080
         - HTTPS_PROXY=http://proxy.company.com:8080
   ```

## CI/CD Pipeline Issues

### Pipeline Failures

**Symptoms:**
- CI tests failing
- Build stage errors
- Deployment failures

**Diagnosis:**
```bash
# Run pipeline locally
docker compose -f ci/docker-compose.ci.yml up

# Check individual stages
./ci/lint.sh
./ci/test.sh
./ci/build.sh
```

**Solutions:**

1. **Fix Test Failures**
   ```bash
   # Run tests with verbose output
   ./ci/test.sh all --verbose
   
   # Run specific test
   docker compose -f ci/docker-compose.ci.yml run --rm unit-tests pytest tests/specific_test.py -v
   ```

2. **Fix Build Issues**
   ```bash
   # Clear CI cache
   docker compose -f ci/docker-compose.ci.yml down -v
   docker system prune -f
   
   # Rebuild
   ./ci/build.sh
   ```

## Security Issues

### Authentication Problems

**Symptoms:**
- Login failures
- Permission denied errors
- Session issues

**Solutions:**

1. **Reset Admin Password**
   ```bash
   docker compose -f docker-compose.development.yml exec web python manage.py changepassword admin
   ```

2. **Check User Permissions**
   ```bash
   # Access Django shell
   docker compose -f docker-compose.development.yml exec web python manage.py shell
   
   # In shell:
   from django.contrib.auth.models import User
   user = User.objects.get(username='admin')
   print(user.is_superuser, user.is_staff)
   ```

### SSL/TLS Issues (Production)

**Symptoms:**
- Certificate errors
- HTTPS not working
- Mixed content warnings

**Solutions:**

1. **Check Certificate**
   ```bash
   openssl x509 -in nginx/ssl/cert.pem -text -noout
   ```

2. **Verify Configuration**
   ```bash
   # Test SSL configuration
   openssl s_client -connect yourdomain.com:443
   ```

## Getting Additional Help

### Diagnostic Information

When seeking help, provide this information:

```bash
# System information
uname -a
docker --version
docker compose version

# Service status
docker compose -f docker-compose.development.yml ps

# Recent logs
docker compose -f docker-compose.development.yml logs --tail=100

# Resource usage
docker stats --no-stream
free -h
df -h
```

### Support Channels

1. **Documentation**: Check [User Guides](../user-guides/index.md)
2. **FAQ**: Review [Frequently Asked Questions](../faq.md)
3. **GitHub Issues**: [Open an issue](https://github.com/nullroute-commits/financial_stronghold/issues)
4. **Architecture**: Review [System Architecture](../architecture/index.md)

### Reporting Bugs

When reporting issues, include:

1. **Environment**: Development/Testing/Production
2. **Docker Info**: Version, compose file used
3. **Error Messages**: Complete error logs
4. **Steps to Reproduce**: Exact commands run
5. **Expected vs Actual**: What should happen vs what happens