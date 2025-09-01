# System Administrator Guide

This guide provides comprehensive information for system administrators managing production deployments of Financial Stronghold.

## Production Deployment Overview

Financial Stronghold is designed for enterprise-grade production deployment with high availability, security, and performance features.

### Production Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Production Environment                              │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Nginx     │    │   Django    │    │ PostgreSQL  │    │ Monitoring  │   │
│  │ Load Balancer│───▶│ Application │───▶│  Database   │    │   Stack     │   │
│  │   (SSL/TLS) │    │  (3 nodes)  │    │ (Primary +  │    │ (Prometheus)│   │
│  └─────────────┘    └─────────────┘    │  Replica)   │    └─────────────┘   │
│                             │          └─────────────┘                      │
│                             ▼                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │ Memcached   │    │  RabbitMQ   │    │   Backup    │                      │
│  │   Cluster   │    │   Cluster   │    │   System    │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Initial Production Setup

### Prerequisites

- **Server Requirements**:
  - **Minimum (Development/Testing):**
    - CPU: 2 cores
    - RAM: 2GB
    - Storage: 20GB SSD
    - Network: Local/private IP (no DNS required)
  - **Recommended (Production):**
    - CPU: 4+ cores
    - RAM: 8GB+ (16GB recommended)
    - Storage: 100GB+ SSD
    - Network: Public IP with DNS

- **Software Requirements**:
  - Docker Engine 24.0.7+
  - Docker Compose 2.18.1+
  - Git
  - SSL certificates

### Production Installation

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Application Deployment**
   ```bash
   # Clone repository
   git clone https://github.com/nullroute-commits/financial_stronghold.git
   cd financial_stronghold
   
   # Configure production environment
   cp environments/.env.production.example .env.production
   
   # Edit configuration (see Configuration section below)
   nano .env.production
   
   # Deploy to production
   ./scripts/start-prod.sh
   ```

3. **SSL/TLS Configuration**
   ```bash
   # Create SSL directory
   mkdir -p nginx/ssl
   
   # Copy your SSL certificates
   cp your-cert.pem nginx/ssl/cert.pem
   cp your-key.pem nginx/ssl/key.pem
   
   # Set proper permissions
   chmod 600 nginx/ssl/key.pem
   chmod 644 nginx/ssl/cert.pem
   ```

## Configuration Management

### Production Environment Variables

#### Critical Settings

```bash
# .env.production
# Application Settings
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your-production-secret-key-minimum-50-characters-long
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
POSTGRES_DB=django_app_prod
POSTGRES_USER=django_user
POSTGRES_PASSWORD=secure-database-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Cache Configuration
MEMCACHED_SERVERS=memcached:11211

# Message Queue Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=django_user
RABBITMQ_PASSWORD=secure-rabbitmq-password

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True

# Email Configuration (Production SMTP)
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
```

#### Performance Settings

```bash
# Worker Configuration
GUNICORN_WORKERS=4
GUNICORN_WORKER_CLASS=gevent
GUNICORN_WORKER_CONNECTIONS=1000

# Database Connection Pool
DATABASE_CONN_MAX_AGE=60
DATABASE_POOL_SIZE=20

# Cache Settings
CACHE_TTL=3600
CACHE_KEY_PREFIX=financial_stronghold_prod
```

### Secrets Management

#### Using Docker Secrets

1. **Create secrets directory**
   ```bash
   mkdir -p secrets
   chmod 700 secrets
   ```

2. **Store sensitive values**
   ```bash
   echo "your-production-secret-key" > secrets/secret_key.txt
   echo "secure-database-password" > secrets/postgres_password.txt
   echo "secure-rabbitmq-password" > secrets/rabbitmq_password.txt
   chmod 600 secrets/*.txt
   ```

3. **Configure Docker Compose**
   ```yaml
   # docker-compose.production.yml
   services:
     web:
       secrets:
         - secret_key
         - postgres_password
         - rabbitmq_password
   
   secrets:
     secret_key:
       file: ./secrets/secret_key.txt
     postgres_password:
       file: ./secrets/postgres_password.txt
     rabbitmq_password:
       file: ./secrets/rabbitmq_password.txt
   ```

## System Monitoring

### Health Monitoring

#### Built-in Health Checks

```bash
# Application health
curl https://yourdomain.com/health/

# Database health
curl https://yourdomain.com/health/db/

# Cache health
curl https://yourdomain.com/health/cache/

# Queue health
curl https://yourdomain.com/health/queue/
```

#### Service Status Monitoring

```bash
# Check all services
docker compose -f docker-compose.production.yml ps

# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check service logs
docker compose -f docker-compose.production.yml logs -f --tail=100 web
```

### Log Management

#### Log Collection

```bash
# Application logs
docker compose -f docker-compose.production.yml logs web > logs/app.log

# Database logs  
docker compose -f docker-compose.production.yml logs db > logs/db.log

# Nginx logs
docker compose -f docker-compose.production.yml logs nginx > logs/nginx.log
```

#### Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/financial-stronghold << EOF
/var/log/financial-stronghold/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker compose -f /path/to/docker-compose.production.yml restart nginx
    endscript
}
EOF
```

### Performance Monitoring

#### Database Performance

```sql
-- Connect to PostgreSQL
psql -h localhost -U django_user -d django_app_prod

-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('django_app_prod'));
```

#### Cache Performance

```bash
# Memcached statistics
echo "stats" | nc localhost 11211

# Cache hit rate
echo "stats" | nc localhost 11211 | grep -E "(get_hits|get_misses|cmd_get)"
```

## Backup and Recovery

### Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/var/backups/financial-stronghold"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="django_app_prod"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker compose -f docker-compose.production.yml exec -T db pg_dump -U django_user $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Backup uploaded files
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Schedule Backups

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### Disaster Recovery

#### Database Restore

```bash
# Stop application
docker compose -f docker-compose.production.yml stop web

# Restore database
gunzip -c /var/backups/financial-stronghold/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.production.yml exec -T db psql -U django_user django_app_prod

# Restore media files
tar -xzf /var/backups/financial-stronghold/media_backup_YYYYMMDD_HHMMSS.tar.gz

# Start application
docker compose -f docker-compose.production.yml up -d
```

#### Full System Recovery

```bash
# 1. Reinstall Docker and dependencies
# 2. Clone repository
git clone https://github.com/nullroute-commits/financial_stronghold.git

# 3. Restore configuration
cp backup/.env.production .env.production

# 4. Restore SSL certificates
cp backup/nginx/ssl/* nginx/ssl/

# 5. Restore secrets
cp backup/secrets/* secrets/

# 6. Deploy application
./scripts/start-prod.sh

# 7. Restore database and media
# (use database restore process above)
```

## Security Management

### Security Hardening

#### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### Docker Security

```bash
# Run Docker daemon with user namespace
echo '{"userns-remap": "default"}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Use non-root user in containers
# (Already configured in Dockerfile)
```

#### SSL/TLS Management

```bash
# Check certificate expiration
openssl x509 -in nginx/ssl/cert.pem -text -noout | grep "Not After"

# Automated certificate renewal (if using Let's Encrypt)
# Add to crontab:
0 2 * * * certbot renew --quiet && docker compose -f docker-compose.production.yml restart nginx
```

### Security Monitoring

#### Intrusion Detection

```bash
# Install fail2ban
sudo apt install fail2ban

# Configure for Docker logs
sudo tee /etc/fail2ban/jail.local << EOF
[nginx-docker]
enabled = true
port = http,https
logpath = /var/lib/docker/containers/*/*.log
maxretry = 5
bantime = 3600
EOF

sudo systemctl restart fail2ban
```

#### Vulnerability Scanning

```bash
# Scan Docker images
trivy image django-app:production

# Scan for outdated packages
docker compose -f docker-compose.production.yml exec web pip list --outdated
```

## Scaling and Performance

### Horizontal Scaling

#### Web Application Scaling

```bash
# Scale web workers
docker compose -f docker-compose.production.yml up -d --scale web=5

# Update load balancer configuration
# (Nginx automatically detects new containers)
```

#### Database Scaling

```yaml
# docker-compose.production.yml
services:
  db-primary:
    image: postgres:17.2
    # Primary database configuration
    
  db-replica:
    image: postgres:17.2
    # Read replica configuration
    depends_on:
      - db-primary
```

### Performance Optimization

#### Database Optimization

```sql
-- Optimize database settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();

-- Add indexes for frequently queried columns
CREATE INDEX CONCURRENTLY idx_user_email ON auth_user(email);
CREATE INDEX CONCURRENTLY idx_audit_timestamp ON audit_auditlog(timestamp);
```

#### Application Optimization

```python
# config/settings/production.py
# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['OPTIONS'] = {
    'MAX_CONNS': 20,
    'MIN_CONNS': 5,
}

# Template caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Weekly Tasks

```bash
#!/bin/bash
# weekly_maintenance.sh

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean Docker system
docker system prune -f

# Rotate logs
sudo logrotate -f /etc/logrotate.d/financial-stronghold

# Check disk space
df -h

# Generate system report
./scripts/system_report.sh
```

#### Monthly Tasks

```bash
#!/bin/bash
# monthly_maintenance.sh

# Database maintenance
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "VACUUM ANALYZE;"

# Update Docker images
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml up -d

# Security scan
trivy image django-app:production

# Performance review
./scripts/performance_report.sh
```

### Update Procedures

#### Application Updates

```bash
# 1. Backup current state
./scripts/backup.sh

# 2. Pull latest code
git pull origin main

# 3. Update dependencies
docker compose -f docker-compose.production.yml build

# 4. Run database migrations
docker compose -f docker-compose.production.yml exec web python manage.py migrate

# 5. Rolling restart
for service in web celery; do
    docker compose -f docker-compose.production.yml restart $service
    sleep 30
done

# 6. Verify deployment
curl -f https://yourdomain.com/health/ || echo "Deployment verification failed"
```

## Troubleshooting

### Common Production Issues

#### High CPU Usage

```bash
# Identify resource-heavy containers
docker stats --no-stream | sort -k3 -nr

# Check application performance
docker compose -f docker-compose.production.yml exec web python manage.py shell -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
"
```

#### Database Connection Issues

```bash
# Check database connections
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Check database logs
docker compose -f docker-compose.production.yml logs db | tail -50

# Restart database if needed
docker compose -f docker-compose.production.yml restart db
```

#### SSL Certificate Issues

```bash
# Check certificate validity
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate files
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Restart nginx
docker compose -f docker-compose.production.yml restart nginx
```

### Emergency Procedures

#### Service Recovery

```bash
# Quick service restart
docker compose -f docker-compose.production.yml restart

# Emergency rollback
git checkout HEAD~1
docker compose -f docker-compose.production.yml up -d --build

# Database emergency stop
docker compose -f docker-compose.production.yml stop db
```

#### Data Recovery

```bash
# Restore from latest backup
./scripts/restore_backup.sh /var/backups/financial-stronghold/latest/

# Point-in-time recovery
# (Requires WAL archiving to be configured)
```

### Getting Help

- Check the [Complete Troubleshooting Guide](../troubleshooting/index.md)
- Review [Performance Optimization Guide](../operations/performance-tuning.md)
- Consult [Security Documentation](../../SECURITY_MODEL.md)
- Open a priority issue on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)