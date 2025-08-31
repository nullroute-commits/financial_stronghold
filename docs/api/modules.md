# Modules

## Core Modules

### app
The main Django application module providing core functionality for user authentication, role-based access control, and comprehensive audit logging.

### app.core
Provides the core application functionality including models, RBAC system, audit logging, database connection management, caching, and queue integration.

### app.core.models
Core models for the application including SQLAlchemy models for User, Role, Permission, and audit logging.

### app.core.rbac
Role-Based Access Control (RBAC) system providing comprehensive access control functionality for the application.

### app.core.audit
Comprehensive audit logging system that tracks all system activities for security and compliance.

### app.core.db
Database connection management, SQLAlchemy configuration, and database utilities for the Django application.

### app.core.cache
Caching functionality using Memcached for improved application performance.

### app.core.queue
Message queue functionality using RabbitMQ for asynchronous task processing.