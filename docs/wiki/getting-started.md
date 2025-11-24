# Getting Started Guide

Welcome to Financial Stronghold! This guide will help you get up and running quickly with our Django 5 Multi-Architecture CI/CD Pipeline application.

## Quick Start

### For Developers

1. **Prerequisites Check**
   ```bash
   # Verify you have the required tools
   docker --version    # Should be 24.0.7+
   docker compose version  # Should be 2.18.1+
   git --version
   ```

2. **Clone and Setup**
   ```bash
   git clone https://github.com/nullroute-commits/financial_stronghold.git
   cd financial_stronghold
   ```

3. **Start Development Environment**
   ```bash
   ./scripts/start-dev.sh
   ```

4. **Access the Application**
   - **Web Application**: http://localhost:8000
   - **Admin Panel**: http://localhost:8000/admin (admin/admin123)
   - **Database Admin**: http://localhost:8080 (Adminer)
   - **Email Testing**: http://localhost:8025 (Mailhog)
   - **Message Queue** (optional): http://localhost:15672 (RabbitMQ Management - not actively used)

### For DevOps/Operations

1. **Validate Deployment Configuration**
   ```bash
   ./ci/validate-deployment-demo.sh all
   ```

2. **Run Full CI/CD Pipeline**
   ```bash
   # Start CI environment
   docker compose -f ci/docker-compose.ci.yml up
   ```

3. **Deploy to Different Environments**
   ```bash
   # Deploy to staging
   ./ci/deploy.sh staging
   
   # Deploy to production (requires approval)
   ./ci/deploy.sh production
   ```

### For System Administrators

1. **Production Deployment**
   ```bash
   # Configure production environment
   cp environments/.env.production.example environments/.env.production
   # Edit with your production values
   
   # Deploy to production
   ./scripts/start-prod.sh
   ```

2. **Monitor System Health**
   ```bash
   # Check all services
   docker compose -f docker-compose.production.yml ps
   
   # View logs
   docker compose -f docker-compose.production.yml logs -f
   ```

## What's Next?

- [User Guides](user-guides/index.md) - Detailed guides for different user types
- [Tutorials](tutorials/index.md) - Step-by-step tutorials
- [Architecture](../ARCHITECTURE.md) - System architecture documentation
- [API Reference](../api/overview.md) - Complete API documentation
- [Troubleshooting](troubleshooting/index.md) - Common issues and solutions

## Need Help?

- Check our [FAQ](faq.md)
- Review [Troubleshooting Guide](troubleshooting/index.md)
- See [Architecture Documentation](../ARCHITECTURE.md)
- Open an issue on [GitHub](https://github.com/nullroute-commits/financial_stronghold/issues)