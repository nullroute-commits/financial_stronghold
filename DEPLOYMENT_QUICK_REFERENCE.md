# Financial Stronghold - Deployment Quick Reference

## 🚀 **Quick Start Commands**

### **Development Environment**
```bash
# Start development
docker-compose -f docker-compose.development.yml up -d

# Access web app
open http://localhost:8000

# View logs
docker-compose -f docker-compose.development.yml logs -f

# Stop development
docker-compose -f docker-compose.development.yml down
```

**Ports:** Web(8000), DB(5432), Cache(11211), Queue(5672), Adminer(8080), Mailhog(8025)

---

### **Testing Environment**
```bash
# Start testing
docker-compose -f docker-compose.testing.yml up -d

# Run tests
docker-compose -f docker-compose.testing.yml exec web python manage.py test

# View test logs
docker-compose -f docker-compose.testing.yml logs -f web

# Stop testing
docker-compose -f docker-compose.testing.yml down
```

**Ports:** Web(8001), DB(5433), Cache(11212), Queue(5673), Management(15673)

---

### **Staging Environment**
```bash
# Start staging
docker-compose -f docker-compose.staging.yml up -d

# Scale web services
docker-compose -f docker-compose.staging.yml up -d --scale web=3

# Run migrations
docker-compose -f docker-compose.staging.yml exec web python manage.py migrate

# Stop staging
docker-compose -f docker-compose.staging.yml down
```

**Ports:** Web(8003), Nginx(8080), DB(staging), Load Balanced(2+ replicas)

---

### **Production Environment**
```bash
# Start production
docker-compose -f docker-compose.production.yml up -d

# Scale services
docker-compose -f docker-compose.production.yml up -d --scale web=4

# Monitor resources
docker stats

# View production logs
docker-compose -f docker-compose.production.yml logs -f

# Stop production
docker-compose -f docker-compose.production.yml down
```

**Ports:** Web(8002), Nginx(80/443), DB(5434), Cache(11213), Queue(5674), Management(15674)

---

## 🔧 **Environment Comparison**

| Feature | Development | Testing | Staging | Production |
|---------|-------------|---------|---------|------------|
| **Debug Mode** | ✅ Enabled | ❌ Disabled | ❌ Disabled | ❌ Disabled |
| **Hot Reload** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Database** | `django_app_dev` | `django_app_test` | `django_app_staging` | `django_app_prod` |
| **Logging** | DEBUG | INFO | WARNING | WARNING |
| **Replicas** | 1 | 1 | 2 | 2+ |
| **Resource Limits** | ❌ None | ❌ None | ✅ Basic | ✅ Strict |
| **Health Checks** | ✅ Basic | ✅ Basic | ✅ Enhanced | ✅ Production |
| **Load Balancing** | ❌ No | ❌ No | ✅ Nginx | ✅ Nginx + HA |

---

## 📊 **Port Mapping Summary**

| Service | Development | Testing | Staging | Production |
|---------|-------------|---------|---------|------------|
| **Web App** | 8000 | 8001 | 8003 | 8002 |
| **Nginx** | - | - | 8080 | 80/443 |
| **Database** | 5432 | 5433 | - | 5434 |
| **Memcached** | 11211 | 11212 | - | 11213 |
| **RabbitMQ** | 5672 | 5673 | - | 5674 |
| **RabbitMQ Mgmt** | 15672 | 15673 | - | 15674 |
| **Adminer** | 8080 | - | - | - |
| **Mailhog** | 8025 | - | - | - |

---

## 🚀 **Docker Swarm Commands**

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.swarm.yml financial-stronghold

# Scale services
docker service scale financial-stronghold_web=5

# View services
docker service ls

# Update service
docker service update --image new-image financial-stronghold_web

# Remove stack
docker stack rm financial-stronghold
```

---

## 🧪 **CI/CD Pipeline Commands**

```bash
# Run full pipeline
docker-compose -f ci/docker-compose.ci.yml up

# Run specific stages
docker-compose -f ci/docker-compose.ci.yml run ci-runner lint
docker-compose -f ci/docker-compose.ci.yml run ci-runner test
docker-compose -f ci/docker-compose.ci.yml run ci-runner build

# Validate deployments
./ci/validate-deployment-l1-l7.sh development
./ci/validate-deployment-l1-l7.sh testing
./ci/validate-deployment-l1-l7.sh production
```

---

## 📚 **Web GUI Access**

| Feature | URL Path | Description |
|---------|----------|-------------|
| **Dashboard** | `/dashboard/` | Main financial overview |
| **Accounts** | `/accounts/` | Account management |
| **Transactions** | `/transactions/` | Transaction tracking |
| **Budgets** | `/budgets/` | Budget management |
| **Fees** | `/fees/` | Fee tracking |
| **Tags** | `/tags/` | Data tagging system |
| **Classification** | `/classification/` | Transaction classification |
| **Analytics Views** | `/analytics/views/` | Saved analytics views |
| **Anomaly Detection** | `/anomaly/` | Transaction anomaly detection |
| **Documentation** | `/docs/` | Built-in help system |

---

## 🔍 **Health Monitoring**

```bash
# Application health
curl -f http://localhost:8000/health/

# Database health
docker-compose exec db pg_isready -U postgres

# Cache health
docker-compose exec memcached echo "stats" | nc localhost 11211

# Queue health
docker-compose exec rabbitmq rabbitmqctl status

# Container stats
docker stats --no-stream

# System resources
docker system df
```

---

## 🎯 **Common Workflows**

### **Development Workflow**
1. `docker-compose -f docker-compose.development.yml up -d`
2. Access http://localhost:8000
3. Make code changes (auto-reload)
4. View logs: `docker-compose -f docker-compose.development.yml logs -f`
5. `docker-compose -f docker-compose.development.yml down`

### **Testing Workflow**
1. `docker-compose -f docker-compose.testing.yml up -d`
2. Run tests: `docker-compose -f docker-compose.testing.yml exec web python manage.py test`
3. View results and coverage
4. `docker-compose -f docker-compose.testing.yml down`

### **Staging Workflow**
1. `docker-compose -f docker-compose.staging.yml up -d`
2. Run migrations and collect static files
3. Test production-like functionality
4. Load test with multiple replicas
5. Validate deployment before production

### **Production Workflow**
1. `docker-compose -f docker-compose.production.yml up -d`
2. Run migrations and collect static files
3. Scale services based on load
4. Monitor health and performance
5. Set up monitoring and alerting

---

## ⚠️ **Important Notes**

- **Development**: Use for active development with hot reload
- **Testing**: Use for running test suites and CI/CD
- **Staging**: Use for pre-production validation and testing
- **Production**: Use for live traffic with high availability
- **All environments**: Use separate port ranges to avoid conflicts
- **Resource limits**: Only applied in staging and production
- **Health checks**: Enhanced in staging and production environments
- **Load balancing**: Available in staging and production with Nginx