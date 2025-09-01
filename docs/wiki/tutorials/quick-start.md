# Quick Start Tutorial

This tutorial will get you up and running with Financial Stronghold in under 10 minutes.

## What You'll Build

By the end of this tutorial, you'll have:
- A fully functional Financial Stronghold instance
- All services running in containers
- Access to the web interface and admin panel
- Basic understanding of the system architecture

## Prerequisites

Before starting, ensure you have:
- **Docker**: Version 24.0.7 or later
- **Docker Compose**: Version 2.18.1 or later
- **Git**: Any recent version
- **Terminal**: Command line access

### Verify Prerequisites

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.0.7, build ...

# Check Docker Compose version  
docker compose version
# Expected: Docker Compose version v2.18.1

# Check Git version
git --version
# Expected: git version 2.x.x
```

## Step 1: Get the Code

Clone the Financial Stronghold repository:

```bash
# Clone the repository
git clone https://github.com/nullroute-commits/financial_stronghold.git

# Navigate to the project directory
cd financial_stronghold

# Verify you're in the right directory
ls -la
# You should see files like: README.md, docker-compose.development.yml, manage.py
```

## Step 2: Start the Development Environment

Run the development startup script:

```bash
# Start all development services
./scripts/start-dev.sh
```

This script will:
1. Build the Docker images
2. Start all required services
3. Run database migrations
4. Create a default admin user
5. Load sample data

**Expected output:**
```
Building development environment...
Starting services...
Running migrations...
Creating superuser...
Development environment ready!
```

## Step 3: Verify the Installation

Check that all services are running:

```bash
# Check service status
docker compose -f docker-compose.development.yml ps
```

**Expected output:**
```
NAME                    COMMAND                  SERVICE     STATUS    PORTS
financial-stronghold-web-1       "python manage.py ru…"   web         running   0.0.0.0:8000->8000/tcp
financial-stronghold-db-1        "docker-entrypoint.s…"   db          running   5432/tcp
financial-stronghold-memcached-1 "docker-entrypoint.s…"   memcached   running   11211/tcp
financial-stronghold-rabbitmq-1  "docker-entrypoint.s…"   rabbitmq    running   5672/tcp, 15672/tcp
```

## Step 4: Access the Application

Now you can access the various interfaces:

### 1. Web Application
Open your browser and go to: **http://localhost:8000**

You should see the Financial Stronghold home page.

### 2. Admin Interface
Go to: **http://localhost:8000/admin**

Login with:
- **Username**: `admin`
- **Password**: `admin123`

### 3. Health Check
Test the health endpoint: **http://localhost:8000/health/**

You should see a JSON response:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "queue": "connected"
}
```

## Step 5: Explore Additional Services

### Database Administration
Go to: **http://localhost:8080**

This opens Adminer for database management:
- **System**: PostgreSQL
- **Server**: db
- **Username**: postgres
- **Password**: dev-password
- **Database**: django_app_dev

### Email Testing
Go to: **http://localhost:8025**

This opens Mailhog for testing email functionality.

### Message Queue Management
Go to: **http://localhost:15672**

This opens RabbitMQ Management interface:
- **Username**: guest
- **Password**: guest

## Step 6: Test Basic Functionality

### Create a Test User

1. Go to the admin interface: http://localhost:8000/admin
2. Click on "Users" under Authentication
3. Click "Add User"
4. Create a new user with username `testuser` and password `testpass123`
5. Save the user

### Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:8000/health/

# Test API (if available)
curl http://localhost:8000/api/
```

## Step 7: View Logs and Monitor

### Check Application Logs
```bash
# View web application logs
docker compose -f docker-compose.development.yml logs -f web

# View all service logs
docker compose -f docker-compose.development.yml logs -f
```

### Monitor Resource Usage
```bash
# Check container resource usage
docker stats
```

## What You've Accomplished

Congratulations! You now have:

✅ **Running Application**: Financial Stronghold is running locally
✅ **Database**: PostgreSQL with sample data
✅ **Caching**: Memcached for performance
✅ **Message Queue**: RabbitMQ for async processing
✅ **Admin Access**: Full administrative interface
✅ **Development Tools**: Database admin, email testing

## Next Steps

Now that you have Financial Stronghold running, explore these areas:

### For Developers
- Follow the [Development Setup Tutorial](development-setup.md)
- Learn about [Testing](testing-tutorial.md)
- Explore the [Database Management Tutorial](database-tutorial.md)

### For DevOps Engineers
- Try the [CI/CD Pipeline Tutorial](cicd-pipeline.md)
- Learn about [Production Deployment](production-deployment.md)
- Explore [Multi-Architecture Deployment](multi-arch-deployment.md)

### For System Administrators
- Review the [Production Deployment Tutorial](production-deployment.md)
- Learn about [Security Implementation](security-tutorial.md)
- Explore [Performance Optimization](performance-tutorial.md)

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process or change the port in docker-compose.development.yml
```

**Services Not Starting**
```bash
# Check Docker service status
sudo systemctl status docker

# Restart Docker if needed
sudo systemctl restart docker

# Try starting again
./scripts/start-dev.sh
```

**Database Connection Issues**
```bash
# Check database logs
docker compose -f docker-compose.development.yml logs db

# Restart database service
docker compose -f docker-compose.development.yml restart db
```

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](../troubleshooting/index.md)
2. Review the [Developer Guide](../user-guides/developer-guide.md)
3. Open an issue on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)

## Clean Up

When you're done testing, you can stop all services:

```bash
# Stop all services
docker compose -f docker-compose.development.yml down

# Remove all containers and volumes (optional)
docker compose -f docker-compose.development.yml down -v
```

---

**Next Tutorial**: Ready to dive deeper? Continue with the [Development Setup Tutorial](development-setup.md) to learn about the development workflow.