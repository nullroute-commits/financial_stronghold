# Operations Guide

This guide provides comprehensive information for operations teams maintaining the health, reliability, and performance of Financial Stronghold.

## Operations Overview

The operations team is responsible for:
- **System Health Monitoring**: Ensuring all services are running optimally
- **Performance Management**: Maintaining response times and throughput
- **Incident Response**: Handling system issues and outages
- **Capacity Planning**: Scaling resources based on demand
- **Backup and Recovery**: Protecting data and enabling disaster recovery
- **Security Monitoring**: Detecting and responding to security threats

## Daily Operations

### Morning Health Check

Start each day with a comprehensive system health check:

```bash
# 1. Check all services status
docker compose -f docker-compose.production.yml ps

# 2. Verify application health
curl -f https://yourdomain.com/health/ || echo "ALERT: Health check failed"

# 3. Check resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# 4. Review overnight logs
docker compose -f docker-compose.production.yml logs --since=24h | grep -i error

# 5. Check database health
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "SELECT count(*) FROM pg_stat_activity;"
```

### Key Metrics to Monitor

| Metric | Target | Warning | Critical | Action |
|--------|--------|---------|----------|--------|
| Response Time | <100ms | 200ms | 500ms | Investigate bottlenecks |
| CPU Usage | <70% | 80% | 90% | Scale or optimize |
| Memory Usage | <80% | 85% | 95% | Scale vertically |
| Disk Usage | <75% | 85% | 95% | Add storage |
| Database Connections | <70% | 80% | 95% | Increase pool size |
| Error Rate | <1% | 2% | 5% | Check logs, alert dev team |

### Service Health Monitoring

#### Application Health Checks

```bash
# Main application health
curl -H "Accept: application/json" https://yourdomain.com/health/

# Expected response:
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "queue": "connected",
  "timestamp": "2024-01-01T12:00:00Z"
}

# Individual component checks
curl https://yourdomain.com/health/db/
curl https://yourdomain.com/health/cache/
curl https://yourdomain.com/health/queue/
```

#### Database Health

```bash
# Check database connections
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "
SELECT 
  count(*) as active_connections,
  max(application_name) as max_app,
  state
FROM pg_stat_activity 
GROUP BY state;
"

# Check database size and growth
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "
SELECT 
  pg_size_pretty(pg_database_size('django_app_prod')) as db_size,
  pg_size_pretty(pg_total_relation_size('auth_user')) as user_table_size;
"

# Check for blocking queries
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.GRANTED;
"
```

#### Cache Health

```bash
# Check Memcached statistics
echo "stats" | nc localhost 11211

# Key metrics to monitor:
# - get_hits vs get_misses (hit ratio should be >80%)
# - bytes (memory usage)
# - curr_connections (active connections)
# - evictions (should be low)

# Cache hit ratio calculation
echo "stats" | nc localhost 11211 | awk '
/get_hits/ { hits = $3 }
/get_misses/ { misses = $3 }
/cmd_get/ { gets = $3 }
END { 
  if (gets > 0) {
    hit_ratio = (hits / gets) * 100
    printf "Cache hit ratio: %.2f%%\n", hit_ratio
  }
}'
```

#### Queue Health

```bash
# Check RabbitMQ status
docker compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl status

# Check queue depths
docker compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_queues name messages consumers

# Check exchanges
docker compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_exchanges

# Monitor queue performance
docker compose -f docker-compose.production.yml exec rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged
```

## Performance Monitoring

### Application Performance

#### Response Time Monitoring

```bash
# Create a response time monitoring script
cat > /opt/monitoring/check_response_times.sh << 'EOF'
#!/bin/bash

ENDPOINTS=(
  "https://yourdomain.com/"
  "https://yourdomain.com/health/"
  "https://yourdomain.com/admin/"
  "https://yourdomain.com/api/"
)

for endpoint in "${ENDPOINTS[@]}"; do
  response_time=$(curl -w "%{time_total}" -o /dev/null -s "$endpoint")
  echo "$(date): $endpoint - ${response_time}s"
  
  # Alert if response time > 1 second
  if (( $(echo "$response_time > 1.0" | bc -l) )); then
    echo "ALERT: Slow response time for $endpoint: ${response_time}s"
    # Send alert (implement your alerting mechanism)
  fi
done
EOF

chmod +x /opt/monitoring/check_response_times.sh

# Run every minute via cron
echo "* * * * * /opt/monitoring/check_response_times.sh >> /var/log/response_times.log" | crontab -
```

#### Resource Usage Monitoring

```bash
# Create resource monitoring script
cat > /opt/monitoring/check_resources.sh << 'EOF'
#!/bin/bash

# Check Docker container resources
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" > /tmp/docker_stats.txt

# Check for high CPU usage
while read line; do
  if [[ $line =~ ([0-9]+\.[0-9]+)% ]]; then
    cpu_usage=${BASH_REMATCH[1]}
    if (( $(echo "$cpu_usage > 80" | bc -l) )); then
      echo "ALERT: High CPU usage detected: $line"
    fi
  fi
done < /tmp/docker_stats.txt

# Check system disk usage
df -h | awk '$5 > 80 { print "ALERT: High disk usage on " $6 ": " $5 }'

# Check system memory
free -m | awk 'NR==2{printf "Memory Usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2}'
EOF

chmod +x /opt/monitoring/check_resources.sh
```

### Database Performance

#### Query Performance Monitoring

```sql
-- Enable pg_stat_statements extension (run once)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Monitor slow queries
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  stddev_time,
  rows
FROM pg_stat_statements 
WHERE mean_time > 100  -- queries taking more than 100ms on average
ORDER BY mean_time DESC 
LIMIT 10;

-- Monitor query frequency
SELECT 
  query,
  calls,
  total_time,
  mean_time
FROM pg_stat_statements 
ORDER BY calls DESC 
LIMIT 10;

-- Check for queries that scan too many rows
SELECT 
  query,
  calls,
  rows,
  (rows/calls) as avg_rows_per_call
FROM pg_stat_statements 
WHERE rows > 10000
ORDER BY rows DESC;
```

#### Database Index Monitoring

```sql
-- Check for missing indexes (high sequential scans)
SELECT 
  schemaname,
  tablename,
  attname,
  n_distinct,
  correlation
FROM pg_stats 
WHERE schemaname = 'public' 
  AND n_distinct > 100;

-- Monitor index usage
SELECT 
  indexrelname,
  idx_tup_read,
  idx_tup_fetch,
  idx_scan
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT 
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```

## Incident Response

### Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P1 - Critical** | Complete service outage | 15 minutes | Site down, database unavailable |
| **P2 - High** | Major functionality affected | 1 hour | Login issues, data corruption |
| **P3 - Medium** | Minor functionality affected | 4 hours | Feature not working, slow response |
| **P4 - Low** | Cosmetic or minor issues | 24 hours | UI glitches, documentation errors |

### Incident Response Procedure

#### Immediate Response (0-15 minutes)

1. **Acknowledge the Incident**
   ```bash
   # Log incident start time
   echo "$(date): INCIDENT START - P1" >> /var/log/incidents.log
   ```

2. **Assess Impact**
   ```bash
   # Quick health check
   curl -f https://yourdomain.com/health/
   docker compose -f docker-compose.production.yml ps
   ```

3. **Identify Scope**
   - Is the entire site down?
   - Are specific services affected?
   - Is it affecting all users or a subset?

4. **Initial Communication**
   - Update status page
   - Notify stakeholders
   - Start incident communication channel

#### Investigation (15-60 minutes)

1. **Check Recent Changes**
   ```bash
   # Check recent deployments
   git log --oneline --since="24 hours ago"
   
   # Check Docker container changes
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.CreatedAt}}"
   ```

2. **Review Logs**
   ```bash
   # Application logs
   docker compose -f docker-compose.production.yml logs --since=1h | grep -i error
   
   # System logs
   journalctl --since="1 hour ago" --priority=err
   ```

3. **Resource Analysis**
   ```bash
   # Check resource usage
   docker stats --no-stream
   free -h
   df -h
   
   # Check for resource exhaustion
   dmesg | grep -i "killed process"
   ```

#### Resolution Actions

**Service Restart**
```bash
# Restart specific service
docker compose -f docker-compose.production.yml restart web

# Rolling restart (for zero downtime)
for i in {1..3}; do
  docker compose -f docker-compose.production.yml restart web_$i
  sleep 30
done
```

**Database Issues**
```bash
# Check database connections
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Kill long-running queries
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

# Restart database (last resort)
docker compose -f docker-compose.production.yml restart db
```

**Cache Issues**
```bash
# Clear cache
docker compose -f docker-compose.production.yml exec web python manage.py clear_cache

# Restart cache service
docker compose -f docker-compose.production.yml restart memcached
```

### Post-Incident Activities

#### Incident Closure

1. **Verify Resolution**
   ```bash
   # Comprehensive health check
   ./scripts/health_check_comprehensive.sh
   ```

2. **Document Resolution**
   ```bash
   echo "$(date): INCIDENT RESOLVED - Duration: X minutes" >> /var/log/incidents.log
   ```

3. **Update Communications**
   - Update status page
   - Notify stakeholders of resolution
   - Close incident communication channel

#### Post-Mortem Process

1. **Gather Data**
   - Timeline of events
   - Actions taken
   - Root cause analysis
   - Impact assessment

2. **Create Post-Mortem Document**
   ```markdown
   # Incident Post-Mortem: [Date] - [Brief Description]
   
   ## Summary
   - Duration: X hours Y minutes
   - Impact: X users affected
   - Root Cause: [Description]
   
   ## Timeline
   - HH:MM - Incident detected
   - HH:MM - Initial response
   - HH:MM - Root cause identified
   - HH:MM - Resolution implemented
   - HH:MM - Service restored
   
   ## Root Cause
   [Detailed analysis]
   
   ## Action Items
   1. [Action 1] - Assigned to [Person] - Due [Date]
   2. [Action 2] - Assigned to [Person] - Due [Date]
   
   ## Lessons Learned
   [What we learned and how to prevent in future]
   ```

## Capacity Planning

### Growth Monitoring

#### User Growth Tracking

```sql
-- Monitor user registration trends
SELECT 
  DATE(date_joined) as registration_date,
  COUNT(*) as new_users
FROM auth_user 
WHERE date_joined >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(date_joined)
ORDER BY registration_date;

-- Monitor active user trends
SELECT 
  DATE(last_login) as login_date,
  COUNT(*) as active_users
FROM auth_user 
WHERE last_login >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(last_login)
ORDER BY login_date;
```

#### Resource Usage Trends

```bash
# Create capacity monitoring script
cat > /opt/monitoring/capacity_monitoring.sh << 'EOF'
#!/bin/bash

# Log resource usage for trend analysis
{
  echo "$(date),"
  docker stats --no-stream --format "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}"
  df -h / | tail -1 | awk '{print $5}'
  free | grep Mem | awk '{printf "%.2f", $3*100/$2}'
} | tr '\n' ',' | sed 's/,$//g' >> /var/log/capacity_metrics.csv
EOF

# Run every hour
echo "0 * * * * /opt/monitoring/capacity_monitoring.sh" | crontab -
```

### Scaling Triggers

#### Automatic Scaling Triggers

```bash
# Create auto-scaling script
cat > /opt/monitoring/auto_scale.sh << 'EOF'
#!/bin/bash

# Get current CPU usage
CPU_USAGE=$(docker stats --no-stream --format "{{.CPUPerc}}" web | sed 's/%//')

# Get current memory usage
MEM_USAGE=$(docker stats --no-stream --format "{{.MemPerc}}" web | sed 's/%//')

# Scale up if CPU > 80% or Memory > 85%
if (( $(echo "$CPU_USAGE > 80" | bc -l) )) || (( $(echo "$MEM_USAGE > 85" | bc -l) )); then
  echo "$(date): Scaling up due to high resource usage (CPU: $CPU_USAGE%, Mem: $MEM_USAGE%)"
  docker compose -f docker-compose.production.yml up -d --scale web=3
fi

# Scale down if CPU < 40% and Memory < 50% for 30 minutes
# (Implement more sophisticated logic as needed)
EOF
```

## Backup and Recovery

### Automated Backup System

#### Database Backup

```bash
# Create comprehensive backup script
cat > /opt/backups/backup_system.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/var/backups/financial-stronghold"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Starting database backup..."
docker compose -f docker-compose.production.yml exec -T db pg_dump -U django_user django_app_prod | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Application data backup
echo "Backing up media files..."
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

# Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
  environments/ \
  nginx/ \
  docker-compose.production.yml \
  .env.production

# System state backup
echo "Capturing system state..."
{
  echo "# Backup created: $(date)"
  echo "# Git commit: $(git rev-parse HEAD)"
  echo "# Docker images:"
  docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}"
  echo "# Running containers:"
  docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
} > $BACKUP_DIR/system_state_$DATE.txt

# Cleanup old backups
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.txt" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"

# Test backup integrity
echo "Testing backup integrity..."
gunzip -t $BACKUP_DIR/db_backup_$DATE.sql.gz && echo "Database backup OK" || echo "Database backup CORRUPTED"
tar -tzf $BACKUP_DIR/media_backup_$DATE.tar.gz > /dev/null && echo "Media backup OK" || echo "Media backup CORRUPTED"
EOF

chmod +x /opt/backups/backup_system.sh

# Schedule daily backups at 2 AM
echo "0 2 * * * /opt/backups/backup_system.sh >> /var/log/backup.log 2>&1" | crontab -
```

#### Disaster Recovery Testing

```bash
# Create disaster recovery test script
cat > /opt/backups/test_recovery.sh << 'EOF'
#!/bin/bash

# Test recovery procedure monthly
TEST_DIR="/tmp/recovery_test_$(date +%Y%m%d)"
mkdir -p $TEST_DIR

echo "Starting disaster recovery test..."

# Create test environment
cd $TEST_DIR
git clone https://github.com/nullroute-commits/financial_stronghold.git .

# Restore latest backup
LATEST_DB_BACKUP=$(ls -t /var/backups/financial-stronghold/db_backup_*.sql.gz | head -1)
LATEST_MEDIA_BACKUP=$(ls -t /var/backups/financial-stronghold/media_backup_*.tar.gz | head -1)

# Test database restore
echo "Testing database restore..."
gunzip -c "$LATEST_DB_BACKUP" | head -100 > /dev/null && echo "Database backup readable" || echo "FAILED: Database backup corrupted"

# Test media restore
echo "Testing media restore..."
tar -tzf "$LATEST_MEDIA_BACKUP" > /dev/null && echo "Media backup readable" || echo "FAILED: Media backup corrupted"

# Cleanup test environment
cd /
rm -rf $TEST_DIR

echo "Disaster recovery test completed: $(date)"
EOF

# Run monthly disaster recovery tests
echo "0 3 1 * * /opt/backups/test_recovery.sh >> /var/log/recovery_test.log 2>&1" | crontab -
```

## Security Operations

### Security Monitoring

#### Log Analysis for Security Events

```bash
# Create security monitoring script
cat > /opt/security/security_monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/security_events.log"

# Monitor failed login attempts
docker compose -f docker-compose.production.yml logs nginx | grep "401\|403" | tail -10 >> $LOG_FILE

# Monitor for SQL injection attempts
docker compose -f docker-compose.production.yml logs web | grep -i "union\|select\|insert\|drop\|delete" | tail -10 >> $LOG_FILE

# Monitor for unusual user agents
docker compose -f docker-compose.production.yml logs nginx | grep -E "(sqlmap|nikto|nmap|masscan)" >> $LOG_FILE

# Alert on excessive failed logins
FAILED_LOGINS=$(docker compose -f docker-compose.production.yml logs --since=1h nginx | grep "401" | wc -l)
if [ $FAILED_LOGINS -gt 50 ]; then
  echo "$(date): SECURITY ALERT - Excessive failed logins: $FAILED_LOGINS" >> $LOG_FILE
fi

# Check for privilege escalation attempts
docker compose -f docker-compose.production.yml logs web | grep -i "admin\|superuser\|root" | tail -5 >> $LOG_FILE
EOF

chmod +x /opt/security/security_monitor.sh

# Run every 15 minutes
echo "*/15 * * * * /opt/security/security_monitor.sh" | crontab -
```

#### Vulnerability Scanning

```bash
# Weekly vulnerability scan
cat > /opt/security/vuln_scan.sh << 'EOF'
#!/bin/bash

echo "Starting weekly vulnerability scan..."

# Scan Docker images
trivy image django-app:production --severity HIGH,CRITICAL > /var/log/vuln_scan_$(date +%Y%m%d).log

# Scan application dependencies
docker compose -f docker-compose.production.yml exec web pip-audit >> /var/log/vuln_scan_$(date +%Y%m%d).log

# Scan for secrets in code (if truffleHog is available)
# trufflehog --regex --entropy=False /path/to/code >> /var/log/vuln_scan_$(date +%Y%m%d).log

echo "Vulnerability scan completed: $(date)"
EOF

# Run weekly vulnerability scans
echo "0 4 * * 0 /opt/security/vuln_scan.sh" | crontab -
```

## Maintenance Windows

### Planned Maintenance

#### Pre-Maintenance Checklist

```bash
# Create pre-maintenance checklist script
cat > /opt/maintenance/pre_maintenance.sh << 'EOF'
#!/bin/bash

echo "=== Pre-Maintenance Checklist ==="

# 1. Create full backup
echo "Creating full backup..."
/opt/backups/backup_system.sh

# 2. Test backup integrity
echo "Testing backup integrity..."
/opt/backups/test_recovery.sh

# 3. Document current system state
echo "Documenting system state..."
{
  echo "# Pre-maintenance system state: $(date)"
  echo "# Current git commit: $(git rev-parse HEAD)"
  echo "# Running containers:"
  docker ps
  echo "# Resource usage:"
  docker stats --no-stream
  echo "# Disk usage:"
  df -h
} > /var/log/pre_maintenance_$(date +%Y%m%d_%H%M%S).log

# 4. Notify users
echo "Update status page about upcoming maintenance"

# 5. Check for running processes
echo "Checking for long-running processes..."
docker compose -f docker-compose.production.yml exec db psql -U django_user -d django_app_prod -c "SELECT pid, query_start, query FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"

echo "Pre-maintenance checklist completed"
EOF
```

#### Post-Maintenance Checklist

```bash
# Create post-maintenance checklist script
cat > /opt/maintenance/post_maintenance.sh << 'EOF'
#!/bin/bash

echo "=== Post-Maintenance Checklist ==="

# 1. Verify all services are running
echo "Verifying services..."
docker compose -f docker-compose.production.yml ps

# 2. Run health checks
echo "Running health checks..."
curl -f https://yourdomain.com/health/ || echo "FAILED: Health check failed"

# 3. Test key functionality
echo "Testing key functionality..."
# Add specific tests for your application

# 4. Check performance
echo "Checking performance..."
curl -w "Response time: %{time_total}s\n" -o /dev/null -s https://yourdomain.com/

# 5. Review logs for errors
echo "Checking for errors in logs..."
docker compose -f docker-compose.production.yml logs --since=10m | grep -i error

# 6. Update status page
echo "Update status page - maintenance completed"

# 7. Send completion notification
echo "Send notification to stakeholders"

echo "Post-maintenance checklist completed"
EOF
```

## Getting Help and Escalation

### Escalation Procedures

1. **Level 1 - Operations Team**
   - Initial response and basic troubleshooting
   - Follow standard operating procedures
   - Escalate after 30 minutes if unresolved

2. **Level 2 - Senior Operations/DevOps**
   - Advanced troubleshooting
   - Infrastructure changes
   - Escalate after 1 hour if unresolved

3. **Level 3 - Development Team**
   - Application-specific issues
   - Code-related problems
   - Database schema issues

4. **Level 4 - Management/External Vendors**
   - Major infrastructure failures
   - Vendor-specific issues
   - Business continuity decisions

### Contact Information

- **Operations Team**: ops@yourdomain.com
- **Development Team**: dev@yourdomain.com  
- **Security Team**: security@yourdomain.com
- **Management**: management@yourdomain.com
- **Emergency Hotline**: +1-XXX-XXX-XXXX

### Documentation References

- [System Architecture](../architecture/index.md)
- [Troubleshooting Guide](../troubleshooting/index.md)
- [Security Model](../../SECURITY_MODEL.md)
- [CI/CD Pipeline](../../CI_CD_PIPELINE.md)

---

**Remember**: Document all actions taken during incidents for post-mortem analysis and knowledge sharing.