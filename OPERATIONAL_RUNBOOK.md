# 📚 Operational Runbook - Financial Stronghold

## 🎯 **Daily Operations Guide**

### **🌅 Daily Startup Checklist**
1. **System Health Check**
   ```bash
   python manage.py health_check --detailed
   ```

2. **Monitor Application Logs**
   ```bash
   tail -f logs/django.log
   tail -f logs/security.log
   ```

3. **Check Resource Usage**
   ```bash
   docker stats
   df -h
   free -h
   ```

4. **Verify Backup Status**
   ```bash
   ls -la /backups/financial-stronghold/ | tail -5
   ```

### **🌙 Daily Shutdown Checklist**
1. **Review Error Logs**
   ```bash
   grep ERROR logs/django_errors.log | tail -20
   ```

2. **Check Security Events**
   ```bash
   grep "security_event" logs/security.log | tail -10
   ```

3. **Verify Backup Completion**
   ```bash
   ls -la /backups/financial-stronghold/ | tail -1
   ```

---

## 🚨 **Emergency Response Procedures**

### **🔴 Critical Issues (Immediate Response)**

#### **Application Down**
1. **Check Container Status**
   ```bash
   docker-compose -f docker-compose.production.yml ps
   ```

2. **Restart Services**
   ```bash
   docker-compose -f docker-compose.production.yml restart web
   ```

3. **Check Logs**
   ```bash
   docker-compose -f docker-compose.production.yml logs web --tail=50
   ```

4. **Health Check**
   ```bash
   curl -f https://yourdomain.com/api/v1/health/
   ```

#### **Database Issues**
1. **Check Database Connectivity**
   ```bash
   python manage.py dbshell -c "SELECT version();"
   ```

2. **Check Database Logs**
   ```bash
   docker-compose -f docker-compose.production.yml logs db --tail=50
   ```

3. **Restart Database (Last Resort)**
   ```bash
   docker-compose -f docker-compose.production.yml restart db
   ```

#### **Performance Issues**
1. **Check Resource Usage**
   ```bash
   docker stats
   htop
   ```

2. **Check Slow Queries**
   ```bash
   python manage.py dbshell -c "
   SELECT query, calls, total_time, mean_time 
   FROM pg_stat_statements 
   ORDER BY total_time DESC LIMIT 10;"
   ```

3. **Clear Cache if Needed**
   ```bash
   python manage.py shell -c "
   from django.core.cache import cache
   cache.clear()
   print('Cache cleared')
   "
   ```

---

## 🔧 **Maintenance Procedures**

### **📅 Weekly Maintenance (Sundays 2 AM)**
```bash
#!/bin/bash
# Weekly maintenance script

echo "Starting weekly maintenance..."

# 1. Database maintenance
docker-compose -f docker-compose.production.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# 2. Log rotation and cleanup
find logs/ -name "*.log.*" -mtime +7 -delete

# 3. Docker cleanup
docker system prune -f
docker volume prune -f

# 4. Update database statistics
python manage.py dbshell -c "ANALYZE;"

# 5. Health check
python manage.py health_check --detailed

echo "Weekly maintenance completed"
```

### **📅 Monthly Maintenance (1st Sunday 2 AM)**
```bash
#!/bin/bash
# Monthly maintenance script

echo "Starting monthly maintenance..."

# 1. Full database backup
./scripts/backup_database.sh

# 2. Security audit
python manage.py check --deploy

# 3. Performance review
python manage.py shell << 'EOF'
from app.monitoring import performance_monitor
metrics = performance_monitor.get_performance_metrics()
print("Performance metrics:", metrics)
EOF

# 4. Update dependencies (if needed)
# pip-review --auto

# 5. SSL certificate renewal check
certbot renew --dry-run

echo "Monthly maintenance completed"
```

---

## 📊 **Monitoring and Alerting**

### **🎯 Key Metrics to Monitor**

#### **Application Metrics**
- Response time < 200ms (95th percentile)
- Error rate < 1%
- Uptime > 99.5%
- Memory usage < 80%
- CPU usage < 70%

#### **Database Metrics**
- Connection pool usage < 80%
- Query response time < 100ms (average)
- Disk usage < 85%
- Backup success rate 100%

#### **Security Metrics**
- Failed login attempts
- Unusual access patterns
- Security event frequency
- SSL certificate expiry

### **🚨 Alert Thresholds**

#### **Critical Alerts (Immediate)**
- Application down (health check fails)
- Database connection lost
- Disk usage > 95%
- Memory usage > 95%
- SSL certificate expires in < 7 days

#### **Warning Alerts (4 hours)**
- Response time > 500ms
- Error rate > 5%
- Disk usage > 85%
- Memory usage > 85%
- Failed login attempts > 10/hour

### **📧 Alert Configuration**
```bash
# Example alert script
cat > /usr/local/bin/send_alert.sh << 'EOF'
#!/bin/bash
ALERT_TYPE=$1
MESSAGE=$2
RECIPIENT="admin@yourdomain.com"

case $ALERT_TYPE in
    critical)
        SUBJECT="🚨 CRITICAL: Financial Stronghold Alert"
        ;;
    warning)
        SUBJECT="⚠️ WARNING: Financial Stronghold Alert"
        ;;
    info)
        SUBJECT="ℹ️ INFO: Financial Stronghold Alert"
        ;;
esac

echo "$MESSAGE" | mail -s "$SUBJECT" $RECIPIENT
EOF
chmod +x /usr/local/bin/send_alert.sh
```

---

## 🔄 **Deployment Rollback Procedures**

### **🔙 Quick Rollback**
```bash
# 1. Stop current deployment
docker-compose -f docker-compose.production.yml down

# 2. Switch to previous image tag
docker-compose -f docker-compose.production.yml pull financial-stronghold:previous

# 3. Start previous version
docker-compose -f docker-compose.production.yml up -d

# 4. Verify rollback
curl -f https://yourdomain.com/api/v1/health/
```

### **🗃️ Database Rollback**
```bash
# 1. Stop application
docker-compose -f docker-compose.production.yml down

# 2. Restore database from backup
gunzip -c /backups/financial-stronghold/backup_YYYYMMDD_HHMMSS.sql.gz | \
docker-compose -f docker-compose.production.yml exec -T db psql -U $POSTGRES_USER $POSTGRES_DB

# 3. Restart application
docker-compose -f docker-compose.production.yml up -d
```

---

## 📞 **Contact Information**

### **🚨 Emergency Contacts**
- **Primary On-Call**: [Phone Number]
- **Secondary On-Call**: [Phone Number]
- **Team Lead**: [Email/Phone]

### **📧 Team Contacts**
- **Infrastructure Team**: devops@yourdomain.com
- **Development Team**: dev@yourdomain.com
- **Security Team**: security@yourdomain.com
- **Management**: management@yourdomain.com

### **🔗 Important Links**
- **Application**: https://yourdomain.com
- **Monitoring Dashboard**: [URL]
- **Documentation**: [URL]
- **Issue Tracker**: https://github.com/nullroute-commits/financial_stronghold/issues

---

## 📋 **Standard Operating Procedures**

### **🔄 Deployment SOP**
1. **Pre-deployment**: Run health checks and create backup
2. **Deployment**: Use automated deployment script
3. **Post-deployment**: Verify health checks and functionality
4. **Documentation**: Update deployment log

### **🛠️ Troubleshooting SOP**
1. **Identify Issue**: Check logs and monitoring
2. **Assess Impact**: Determine severity and user impact
3. **Immediate Action**: Apply quick fixes if available
4. **Escalation**: Contact appropriate team if needed
5. **Resolution**: Implement permanent fix
6. **Documentation**: Update runbook with lessons learned

### **🔒 Security Incident SOP**
1. **Detection**: Identify security event
2. **Assessment**: Determine scope and impact
3. **Containment**: Isolate affected systems
4. **Investigation**: Analyze logs and evidence
5. **Recovery**: Restore normal operations
6. **Documentation**: Document incident and response

---

*This runbook should be reviewed and updated monthly to reflect operational experience and system changes.*