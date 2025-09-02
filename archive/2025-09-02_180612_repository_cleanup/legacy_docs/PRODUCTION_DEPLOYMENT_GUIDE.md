# 🚀 Production Deployment Guide

## 📋 **Complete Production Deployment Checklist**

This guide provides step-by-step instructions for deploying the Django 5 Financial Stronghold application to production.

---

## 🎯 **Pre-Deployment Requirements**

### **✅ Infrastructure Requirements**
- [ ] Docker 24.0.7+ installed and running
- [ ] Docker Compose 2.18.1+ installed
- [ ] PostgreSQL 17+ database server (or containerized)
- [ ] Memcached server (or containerized)
- [ ] RabbitMQ server (or containerized)
- [ ] SSL/TLS certificates for HTTPS
- [ ] Domain name configured with DNS

### **✅ Security Requirements**
- [ ] Generated secure SECRET_KEY (50+ characters)
- [ ] Database credentials configured
- [ ] Environment variables properly set
- [ ] Firewall rules configured
- [ ] SSL certificates installed
- [ ] Backup procedures tested

### **✅ Monitoring Requirements**
- [ ] Log aggregation system (optional but recommended)
- [ ] Application monitoring (optional but recommended)
- [ ] Alert notification system configured
- [ ] Backup monitoring configured

---

## 🔧 **Step 1: Environment Configuration**

### **1.1 Create Production Environment File**
```bash
# Copy template and configure
cp environments/.env.production.example environments/.env.production

# Generate secure secret key
python scripts/generate_secret_key.py

# Edit environment file with production values
nano environments/.env.production
```

### **1.2 Required Environment Variables**
```bash
# Django Configuration
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your_secure_50_character_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
POSTGRES_DB=financial_stronghold_prod
POSTGRES_USER=django_user
POSTGRES_PASSWORD=your_secure_database_password
POSTGRES_HOST=your_database_host
POSTGRES_PORT=5432

# Security Configuration
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn_for_error_tracking
```

### **1.3 Validate Configuration**
```bash
# Run configuration validation
python manage.py setup_production --validate-config
```

---

## 🗃️ **Step 2: Database Setup**

### **2.1 Database Preparation**
```bash
# Create production database
createdb financial_stronghold_prod

# Create database user
createuser django_user
psql -c "ALTER USER django_user WITH PASSWORD 'your_secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE financial_stronghold_prod TO django_user;"
```

### **2.2 Run Migrations**
```bash
# Set environment
export DJANGO_SETTINGS_MODULE=config.settings.production

# Run migrations
python manage.py migrate

# Verify migration status
python manage.py showmigrations
```

### **2.3 Set Up Initial Data**
```bash
# Set up RBAC system and create admin user
python manage.py setup_production --all

# Load any initial data (if needed)
python manage.py loaddata initial_data.json
```

---

## 🐳 **Step 3: Docker Deployment**

### **3.1 Build Production Images**
```bash
# Build multi-architecture images
docker buildx build --platform linux/amd64,linux/arm64 -t financial-stronghold:latest .

# Or use Docker Compose
docker-compose -f docker-compose.production.yml build
```

### **3.2 Deploy with Docker Compose**
```bash
# Start production environment
./scripts/deploy.sh production

# Or manually
docker-compose -f docker-compose.production.yml up -d
```

### **3.3 Verify Deployment**
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Check application logs
docker-compose -f docker-compose.production.yml logs web

# Run health check
python manage.py health_check --detailed
```

---

## 🏥 **Step 4: Health Checks and Validation**

### **4.1 Application Health**
```bash
# Basic health check
curl -f http://localhost:8000/api/v1/health/

# Detailed health check
curl -f http://localhost:8000/api/v1/health/detailed/

# Management command health check
python manage.py health_check --detailed --format=json
```

### **4.2 Database Health**
```bash
# Test database connectivity
python manage.py dbshell -c "SELECT version();"

# Check migration status
python manage.py showmigrations --plan

# Validate database constraints
python manage.py check --database default
```

### **4.3 Security Validation**
```bash
# Run security checks
python manage.py check --deploy

# Validate HTTPS configuration
curl -I https://yourdomain.com

# Test authentication
curl -X POST https://yourdomain.com/api-auth/login/
```

---

## 📊 **Step 5: Monitoring Setup**

### **5.1 Application Monitoring**
```bash
# Set up log monitoring (example with journald)
journalctl -u docker-compose-financial-stronghold -f

# Monitor application metrics
docker stats financial-stronghold_web_1

# Monitor database performance
docker exec -it financial-stronghold_db_1 psql -U postgres -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;"
```

### **5.2 Health Check Monitoring**
```bash
# Set up periodic health checks (crontab example)
# Add to crontab: */5 * * * * /path/to/health_check.sh

# Create health check script
cat > /usr/local/bin/health_check.sh << 'EOF'
#!/bin/bash
cd /opt/financial-stronghold
python manage.py health_check --format=json > /var/log/health_check.log
if [ $? -ne 0 ]; then
    echo "Health check failed at $(date)" | mail -s "Health Check Alert" admin@yourdomain.com
fi
EOF
chmod +x /usr/local/bin/health_check.sh
```

---

## 🔄 **Step 6: Backup and Recovery**

### **6.1 Database Backup Setup**
```bash
# Create backup script
cat > /usr/local/bin/backup_database.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/financial-stronghold"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql"

mkdir -p $BACKUP_DIR
docker-compose -f docker-compose.production.yml exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
EOF
chmod +x /usr/local/bin/backup_database.sh

# Add to crontab for daily backups
# 0 2 * * * /usr/local/bin/backup_database.sh
```

### **6.2 Recovery Procedures**
```bash
# Stop application
docker-compose -f docker-compose.production.yml down

# Restore database from backup
gunzip -c /backups/financial-stronghold/backup_YYYYMMDD_HHMMSS.sql.gz | \
docker-compose -f docker-compose.production.yml exec -T db psql -U $POSTGRES_USER $POSTGRES_DB

# Restart application
docker-compose -f docker-compose.production.yml up -d

# Verify restoration
python manage.py health_check --detailed
```

---

## 🔒 **Step 7: Security Hardening**

### **7.1 SSL/TLS Configuration**
```bash
# Install SSL certificates (example with Let's Encrypt)
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Update nginx configuration for SSL
# (See nginx/production.conf for example)
```

### **7.2 Firewall Configuration**
```bash
# Configure UFW firewall (Ubuntu example)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# For Docker deployments, ensure proper network isolation
docker network create --driver bridge financial_stronghold_network
```

### **7.3 Security Monitoring**
```bash
# Monitor security logs
tail -f logs/security.log

# Check for failed login attempts
grep "failed_login" logs/security.log | tail -20

# Monitor audit logs
tail -f logs/audit.log
```

---

## 📈 **Step 8: Performance Optimization**

### **8.1 Database Performance**
```bash
# Run database performance optimization
python manage.py migrate

# Check database indexes
python manage.py dbshell -c "
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
ORDER BY idx_tup_read DESC;"

# Analyze database statistics
python manage.py dbshell -c "ANALYZE;"
```

### **8.2 Cache Performance**
```bash
# Test cache performance
python manage.py shell << 'EOF'
from django.core.cache import cache
import time

start = time.time()
cache.set('test_key', 'test_value', 300)
value = cache.get('test_key')
end = time.time()

print(f"Cache operation took {(end - start) * 1000:.2f}ms")
print(f"Cache value: {value}")
EOF
```

---

## 🚨 **Step 9: Troubleshooting**

### **9.1 Common Issues**

#### **Application Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs web

# Check environment configuration
python manage.py check --deploy

# Verify database connectivity
python manage.py dbshell -c "SELECT 1;"
```

#### **Database Connection Issues**
```bash
# Test database connectivity
telnet $POSTGRES_HOST $POSTGRES_PORT

# Check database logs
docker-compose -f docker-compose.production.yml logs db

# Verify credentials
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT version();"
```

#### **Performance Issues**
```bash
# Check resource usage
docker stats

# Monitor database queries
python manage.py shell << 'EOF'
from django.db import connection
print(f"Database queries: {len(connection.queries)}")
for query in connection.queries[-5:]:
    print(f"Query: {query['sql'][:100]}... Time: {query['time']}s")
EOF

# Check cache performance
python manage.py shell << 'EOF'
from django.core.cache import cache
cache.set('test', 'value', 60)
print(f"Cache test: {cache.get('test')}")
EOF
```

---

## 📞 **Step 10: Support and Maintenance**

### **10.1 Regular Maintenance Tasks**
```bash
# Weekly maintenance script
cat > /usr/local/bin/weekly_maintenance.sh << 'EOF'
#!/bin/bash
echo "Starting weekly maintenance..."

# Database maintenance
docker-compose -f docker-compose.production.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# Clean up old logs
find /opt/financial-stronghold/logs -name "*.log.*" -mtime +7 -delete

# Clean up old Docker images
docker system prune -f

# Health check
python /opt/financial-stronghold/manage.py health_check

echo "Weekly maintenance completed"
EOF
chmod +x /usr/local/bin/weekly_maintenance.sh
```

### **10.2 Emergency Contacts**
- **Technical Lead**: [Contact Information]
- **Database Administrator**: [Contact Information]
- **Security Team**: [Contact Information]
- **DevOps Team**: [Contact Information]

### **10.3 Escalation Procedures**
1. **Critical Issues**: Immediate response required
2. **High Priority**: 4-hour response time
3. **Medium Priority**: 24-hour response time
4. **Low Priority**: Next business day

---

## 🎯 **Post-Deployment Validation**

### **✅ Final Checklist**
- [ ] Application accessible via HTTPS
- [ ] All health checks passing
- [ ] Database migrations completed
- [ ] Static files served correctly
- [ ] Admin interface accessible
- [ ] API endpoints responding
- [ ] Authentication working
- [ ] Monitoring configured
- [ ] Backups tested
- [ ] Performance acceptable
- [ ] Security hardening complete
- [ ] Team trained on procedures

### **🎉 Deployment Complete**

**Your Django 5 Financial Stronghold application is now production-ready!**

**Access Points**:
- **Web Interface**: https://yourdomain.com
- **API Documentation**: https://yourdomain.com/api/v1/
- **Admin Interface**: https://yourdomain.com/admin
- **Health Checks**: https://yourdomain.com/api/v1/health/

---

*Last updated: 2025-01-02 by Team Alpha (Infrastructure & DevOps)*