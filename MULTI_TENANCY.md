# Multi-Tenancy Implementation for Financial Stronghold

This document describes the comprehensive multi-tenancy system implemented for the Financial Stronghold application.

## Overview

The multi-tenancy system supports two distinct tenant types:
- **User Tenants**: Individual user accounts with personal financial data
- **Organization Tenants**: Company/team accounts with shared financial data and role-based access control

## Key Features

### 1. Strict Data Isolation
- Every financial entity (Account, Transaction, Fee, Budget) includes tenant scoping
- Automatic filtering ensures users can only access data belonging to their tenant
- Multi-tenant aware service layer with built-in isolation

### 2. Flexible Tenant Types
- **User Mode**: Personal financial management for individual users
- **Organization Mode**: Shared financial management for teams/companies

### 3. Role-Based Permissions
Within organizations, users can have different roles:
- **Owner**: Full access to all organization data and settings
- **Admin**: Administrative access to financial data
- **Member**: Read/write access to financial data

### 4. Automatic Tenant Resolution
- JWT tokens carry tenant context (`tenant_type`, `tenant_id`)
- Automatic validation of user membership in organizations
- Seamless switching between personal and organization contexts

## Architecture

### Database Schema

#### Core Tenant Models
- `Organization`: Top-level container for groups of users
- `UserOrganizationLink`: Association table linking users to organizations with roles
- `TenantMixin`: Mixin class adding tenant scoping to all financial models

#### Financial Models (All tenant-scoped)
- `Account`: Financial accounts (checking, savings, business, etc.)
- `Transaction`: Financial transactions with full audit trail
- `Fee`: Fee tracking (monthly, transaction, overdraft, etc.)
- `Budget`: Budget management with alerts and categorization

### Service Layer

#### TenantService
Base service class providing tenant-aware CRUD operations:
- Automatic filtering by tenant
- Type-safe operations with proper isolation
- Support for pagination and advanced queries

```python
# Example usage
service = TenantService(db=db, model=Account)
accounts = service.get_all(
    tenant_type="user", 
    tenant_id="user-123"
)
```

### Authentication & Authorization

#### JWT Token Structure
```json
{
  "sub": "user-uuid",
  "tenant_type": "organization", 
  "tenant_id": "org-456",
  "exp": 1234567890
}
```

#### Dependency Injection
- `get_current_user()`: Extracts and validates tenant context from JWT
- `get_tenant_context()`: Provides convenient access to tenant information
- `require_role()`: Enforces role-based permissions for organization operations

## API Endpoints

### Financial Operations

All endpoints automatically scope data to the current tenant:

- `POST /financial/accounts` - Create account
- `GET /financial/accounts` - List accounts
- `GET /financial/accounts/{id}` - Get account
- `PUT /financial/accounts/{id}` - Update account
- `DELETE /financial/accounts/{id}` - Delete account (admin required for orgs)

- `POST /financial/transactions` - Create transaction
- `GET /financial/transactions` - List transactions
- `GET /financial/transactions/{id}` - Get transaction
- `DELETE /financial/transactions/{id}` - Delete transaction (admin required for orgs)

- `POST /financial/fees` - Create fee
- `GET /financial/fees` - List fees

- `POST /financial/budgets` - Create budget
- `GET /financial/budgets` - List budgets

### Tenant Information

- `GET /tenant/info` - Get current tenant context

## Usage Examples

### 1. Personal Financial Management (User Tenant)

```bash
# Create JWT token for user tenant
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Create personal account
curl -X POST "http://localhost:8000/financial/accounts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Personal Checking",
    "account_type": "checking",
    "balance": 1500.00,
    "currency": "USD"
  }'

# List personal accounts
curl -X GET "http://localhost:8000/financial/accounts" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Organization Financial Management

```bash
# Create JWT token for organization tenant
ORG_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Create business account
curl -X POST "http://localhost:8000/financial/accounts" \
  -H "Authorization: Bearer $ORG_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Business Checking",
    "account_type": "business",
    "balance": 25000.00,
    "currency": "USD"
  }'

# Create transaction
curl -X POST "http://localhost:8000/financial/transactions" \
  -H "Authorization: Bearer $ORG_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 500.00,
    "currency": "USD",
    "description": "Office supplies",
    "transaction_type": "debit",
    "category": "business_expense"
  }'
```

## Security Considerations

### 1. Data Isolation
- All queries automatically include tenant filters
- Cross-tenant data access is impossible through the API
- Database-level constraints prevent data leakage

### 2. Authentication
- JWT tokens are validated on every request
- Organization membership is verified for org tenants
- Invalid or expired tokens result in 401 Unauthorized

### 3. Authorization
- Role-based permissions for sensitive operations
- Admin/Owner roles required for deletion operations in organizations
- Fine-grained access control based on user roles

## Testing

### Unit Tests
- Tenant logic validation
- Service layer isolation testing
- Data scoping verification

### Integration Tests
- End-to-end API testing
- Multi-tenant scenarios
- Role-based permission testing

Run tests:
```bash
# Run all tests
python -m pytest

# Run tenant-specific tests
python -m pytest tests/test_tenant_logic.py -v

# Run with coverage
python -m pytest --cov=app
```

## Migration Path

### From Single-Tenant to Multi-Tenant

1. **Add tenant columns** to existing financial tables:
   ```sql
   ALTER TABLE accounts ADD COLUMN tenant_type VARCHAR(20) DEFAULT 'user';
   ALTER TABLE accounts ADD COLUMN tenant_id VARCHAR(50);
   ```

2. **Migrate existing data** to user tenant:
   ```sql
   UPDATE accounts SET tenant_id = user_id::text WHERE tenant_id IS NULL;
   ```

3. **Add constraints** for data integrity:
   ```sql
   ALTER TABLE accounts ALTER COLUMN tenant_type SET NOT NULL;
   ALTER TABLE accounts ALTER COLUMN tenant_id SET NOT NULL;
   CREATE INDEX idx_accounts_tenant ON accounts(tenant_type, tenant_id);
   ```

## Performance Considerations

### 1. Indexing
- Compound indexes on (tenant_type, tenant_id) for all financial tables
- Additional indexes on frequently queried fields

### 2. Query Optimization
- Tenant filters are applied at the query level
- Efficient pagination with limit/offset
- Selective field loading to reduce data transfer

### 3. Caching
- Tenant context caching to reduce JWT parsing overhead
- Organization membership caching
- Query result caching for frequently accessed data

## Deployment

### Environment Variables
```env
SECRET_KEY=your-jwt-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
```

### Docker Deployment
```dockerfile
FROM python:3.12
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Running the Application
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Future Enhancements

1. **Audit Logging**: Integration with existing audit system for tenant operations
2. **Organization Management**: APIs for managing organization settings and membership
3. **Billing**: Per-tenant usage tracking and billing
4. **Analytics**: Tenant-scoped reporting and analytics
5. **Data Export**: Tenant-specific data export capabilities