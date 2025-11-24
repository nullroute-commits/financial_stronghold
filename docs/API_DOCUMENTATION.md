# API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:8000/api/v1/`  
**Authentication:** JWT Token or Session Authentication

---

## Table of Contents

1. [Authentication](#authentication)
2. [File Import API](#file-import-api)
3. [Transaction API](#transaction-api)
4. [Account API](#account-api)
5. [Budget API](#budget-api)
6. [Dashboard API](#dashboard-api)
7. [User Management API](#user-management-api)
8. [Error Handling](#error-handling)

---

## Authentication

All API endpoints require authentication. The application supports both JWT token and session-based authentication.

### Login

**Endpoint:** `POST /api/v1/auth/login/`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "roles": ["user", "analyst"]
  }
}
```

### Using Authentication

Include the JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Or use session cookies for session-based authentication.

---

## File Import API

The File Import API provides endpoints for uploading, validating, and processing transaction files (CSV, Excel, PDF).

### Upload File

**Endpoint:** `POST /api/v1/import/uploads/`

**Content-Type:** `multipart/form-data`

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/import/uploads/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@transactions.csv" \
  -F "description=Monthly bank transactions"
```

**Response (201 Created):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "transactions.csv",
  "original_filename": "transactions.csv",
  "mime_type": "text/csv",
  "file_size": 102400,
  "file_hash": "sha256_hash_here",
  "status": "PENDING",
  "created_at": "2025-11-24T05:00:00Z",
  "validation_results": {}
}
```

**Supported File Types:**
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- PDF (`.pdf`)

**File Size Limits:**
- Maximum file size: 50 MB
- Recommended: < 10 MB for optimal performance

### Validate File

**Endpoint:** `POST /api/v1/import/uploads/{id}/validate_file/`

**Request:**
```json
{}
```

**Response (200 OK):**
```json
{
  "is_valid": true,
  "validation_results": {
    "format_valid": true,
    "encoding_valid": true,
    "structure_valid": true,
    "security_scan_passed": true,
    "column_count": 8,
    "row_count": 1500,
    "detected_columns": [
      "date",
      "description",
      "amount",
      "category",
      "account",
      "type",
      "balance",
      "notes"
    ]
  },
  "status": "VALIDATED"
}
```

### Start Import

**Endpoint:** `POST /api/v1/import/uploads/{id}/start_import/`

**Request:**
```json
{
  "import_settings": {
    "skip_duplicates": true,
    "auto_categorize": true,
    "date_format": "YYYY-MM-DD",
    "column_mappings": {
      "date": "Transaction Date",
      "description": "Description",
      "amount": "Amount",
      "category": "Category"
    }
  }
}
```

**Response (202 Accepted):**
```json
{
  "import_job_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "status": "PROCESSING",
  "message": "Import started successfully"
}
```

### List Import Jobs

**Endpoint:** `GET /api/v1/import/jobs/`

**Query Parameters:**
- `status` - Filter by status (PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED)
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20, max: 100)

**Response (200 OK):**
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/import/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "filename": "transactions.csv",
      "original_filename": "transactions.csv",
      "file_type": "CSV",
      "file_size": 102400,
      "status": "COMPLETED",
      "progress": 100,
      "total_rows": 1500,
      "processed_rows": 1500,
      "successful_imports": 1450,
      "failed_imports": 50,
      "duplicate_count": 25,
      "success_rate": 96.67,
      "created_at": "2025-11-24T05:00:00Z",
      "processing_started_at": "2025-11-24T05:00:30Z",
      "processing_completed_at": "2025-11-24T05:02:15Z",
      "duration": "0:01:45",
      "error_details": {},
      "validation_errors": []
    }
  ]
}
```

### Get Import Job Details

**Endpoint:** `GET /api/v1/import/jobs/{id}/`

**Response (200 OK):**
```json
{
  "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "filename": "transactions.csv",
  "original_filename": "transactions.csv",
  "file_type": "CSV",
  "file_size": 102400,
  "file_hash": "sha256_hash_here",
  "status": "COMPLETED",
  "progress": 100,
  "total_rows": 1500,
  "processed_rows": 1500,
  "successful_imports": 1450,
  "failed_imports": 50,
  "duplicate_count": 25,
  "success_rate": 96.67,
  "created_at": "2025-11-24T05:00:00Z",
  "processing_started_at": "2025-11-24T05:00:30Z",
  "processing_completed_at": "2025-11-24T05:02:15Z",
  "duration": "0:01:45",
  "error_details": {},
  "validation_errors": [],
  "column_mappings": {
    "date": "Transaction Date",
    "description": "Description",
    "amount": "Amount"
  },
  "import_settings": {
    "skip_duplicates": true,
    "auto_categorize": true
  }
}
```

### Get Imported Transactions

**Endpoint:** `GET /api/v1/import/transactions/`

**Query Parameters:**
- `import_job` - Filter by import job ID
- `status` - Filter by status (PENDING, APPROVED, REJECTED, DUPLICATE)
- `category` - Filter by category
- `page` - Page number
- `page_size` - Results per page

**Response (200 OK):**
```json
{
  "count": 1450,
  "next": "http://localhost:8000/api/v1/import/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "import_job": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "row_number": 1,
      "transaction_date": "2025-11-01",
      "description": "Grocery Store Purchase",
      "amount": "-125.50",
      "category": "Groceries",
      "account_name": "Checking Account",
      "transaction_type": "DEBIT",
      "status": "APPROVED",
      "confidence_score": 0.92,
      "suggested_category": "Groceries",
      "auto_categorized": true,
      "is_duplicate": false,
      "duplicate_of": null,
      "created_at": "2025-11-24T05:01:00Z",
      "approved_at": "2025-11-24T05:10:00Z",
      "raw_data": {
        "original_amount": "125.50",
        "original_category": "Shopping"
      }
    }
  ]
}
```

### Approve/Reject Imported Transactions

**Endpoint:** `POST /api/v1/import/transactions/{id}/approve/`

**Request:**
```json
{
  "category": "Groceries",
  "notes": "Confirmed category"
}
```

**Response (200 OK):**
```json
{
  "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "status": "APPROVED",
  "approved_at": "2025-11-24T05:10:00Z",
  "message": "Transaction approved successfully"
}
```

**Reject Endpoint:** `POST /api/v1/import/transactions/{id}/reject/`

---

## Transaction API

### List Transactions

**Endpoint:** `GET /api/v1/transactions/`

**Query Parameters:**
- `account` - Filter by account ID
- `category` - Filter by category
- `type` - Filter by type (DEBIT, CREDIT)
- `date_from` - Start date (YYYY-MM-DD)
- `date_to` - End date (YYYY-MM-DD)
- `search` - Search in description
- `page` - Page number
- `page_size` - Results per page

**Response (200 OK):**
```json
{
  "count": 2500,
  "next": "http://localhost:8000/api/v1/transactions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "d4e5f6a7-b8c9-0123-def0-234567890123",
      "account": {
        "id": "account-uuid",
        "name": "Checking Account",
        "type": "CHECKING"
      },
      "date": "2025-11-23",
      "description": "Monthly Rent Payment",
      "amount": "-1500.00",
      "category": "Housing",
      "type": "DEBIT",
      "balance_after": "3250.50",
      "tags": ["rent", "housing", "monthly"],
      "notes": "",
      "created_at": "2025-11-23T10:00:00Z",
      "updated_at": "2025-11-23T10:00:00Z"
    }
  ]
}
```

### Create Transaction

**Endpoint:** `POST /api/v1/transactions/`

**Request:**
```json
{
  "account": "account-uuid",
  "date": "2025-11-24",
  "description": "Coffee Shop",
  "amount": "-5.50",
  "category": "Dining",
  "type": "DEBIT",
  "tags": ["coffee", "breakfast"],
  "notes": "Morning coffee"
}
```

**Response (201 Created):**
```json
{
  "id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
  "account": {
    "id": "account-uuid",
    "name": "Checking Account",
    "type": "CHECKING"
  },
  "date": "2025-11-24",
  "description": "Coffee Shop",
  "amount": "-5.50",
  "category": "Dining",
  "type": "DEBIT",
  "balance_after": "3245.00",
  "tags": ["coffee", "breakfast"],
  "notes": "Morning coffee",
  "created_at": "2025-11-24T08:00:00Z",
  "updated_at": "2025-11-24T08:00:00Z"
}
```

### Update Transaction

**Endpoint:** `PATCH /api/v1/transactions/{id}/`

**Request:**
```json
{
  "category": "Food & Drink",
  "tags": ["coffee", "breakfast", "regular"]
}
```

**Response (200 OK):** Returns updated transaction object.

### Delete Transaction

**Endpoint:** `DELETE /api/v1/transactions/{id}/`

**Response (204 No Content)**

---

## Account API

### List Accounts

**Endpoint:** `GET /api/v1/accounts/`

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "account-uuid-1",
      "name": "Checking Account",
      "type": "CHECKING",
      "balance": "3245.00",
      "currency": "USD",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "last_transaction_date": "2025-11-24T08:00:00Z"
    }
  ]
}
```

### Get Account Details

**Endpoint:** `GET /api/v1/accounts/{id}/`

**Response (200 OK):**
```json
{
  "id": "account-uuid-1",
  "name": "Checking Account",
  "type": "CHECKING",
  "balance": "3245.00",
  "currency": "USD",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "last_transaction_date": "2025-11-24T08:00:00Z",
  "transaction_count": 2500,
  "average_monthly_inflow": "4500.00",
  "average_monthly_outflow": "3200.00"
}
```

---

## Budget API

### List Budgets

**Endpoint:** `GET /api/v1/budgets/`

**Query Parameters:**
- `category` - Filter by category
- `period` - Filter by period (MONTHLY, QUARTERLY, YEARLY)
- `active` - Filter active budgets (true/false)

**Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": "budget-uuid-1",
      "category": "Groceries",
      "amount": "600.00",
      "period": "MONTHLY",
      "start_date": "2025-11-01",
      "end_date": "2025-11-30",
      "spent": "425.75",
      "remaining": "174.25",
      "percentage_used": 70.96,
      "is_exceeded": false,
      "alert_threshold": 0.8,
      "is_active": true
    }
  ]
}
```

---

## Dashboard API

### Get Dashboard Summary

**Endpoint:** `GET /api/v1/dashboard/summary/`

**Query Parameters:**
- `period` - Time period (week, month, quarter, year)

**Response (200 OK):**
```json
{
  "period": "month",
  "date_range": {
    "start": "2025-11-01",
    "end": "2025-11-30"
  },
  "total_income": "4500.00",
  "total_expenses": "3250.75",
  "net_savings": "1249.25",
  "savings_rate": 27.76,
  "account_balances": {
    "total": "8450.50",
    "checking": "3245.00",
    "savings": "5205.50"
  },
  "top_categories": [
    {
      "category": "Housing",
      "amount": "1500.00",
      "percentage": 46.15
    },
    {
      "category": "Groceries",
      "amount": "425.75",
      "percentage": 13.10
    }
  ],
  "budget_status": {
    "on_track": 8,
    "at_risk": 2,
    "exceeded": 0
  }
}
```

### Get Spending Trends

**Endpoint:** `GET /api/v1/dashboard/trends/`

**Response (200 OK):**
```json
{
  "monthly_trends": [
    {
      "month": "2025-11",
      "income": "4500.00",
      "expenses": "3250.75",
      "net": "1249.25"
    }
  ],
  "category_trends": [
    {
      "category": "Groceries",
      "values": [425.75, 450.20, 398.50]
    }
  ]
}
```

---

## User Management API

### Get Current User

**Endpoint:** `GET /api/v1/users/me/`

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "roles": ["user", "analyst"],
  "permissions": ["view_transactions", "create_transactions"],
  "is_active": true,
  "date_joined": "2025-01-01T00:00:00Z",
  "last_login": "2025-11-24T05:00:00Z"
}
```

### Update Profile

**Endpoint:** `PATCH /api/v1/users/me/`

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith"
}
```

**Response (200 OK):** Returns updated user object.

---

## Error Handling

All API errors follow a consistent format:

### Error Response Format

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {
    "field": ["Specific validation error"]
  },
  "code": "ERROR_CODE",
  "timestamp": "2025-11-24T05:00:00Z"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `202 Accepted` - Request accepted for processing
- `204 No Content` - Request successful, no content to return
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation failed
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Example Error Responses

**401 Unauthorized:**
```json
{
  "error": "Unauthorized",
  "message": "Authentication credentials were not provided.",
  "code": "NOT_AUTHENTICATED"
}
```

**400 Bad Request:**
```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": {
    "amount": ["This field is required."],
    "date": ["Invalid date format. Expected YYYY-MM-DD."]
  },
  "code": "VALIDATION_ERROR"
}
```

**429 Too Many Requests:**
```json
{
  "error": "Rate Limit Exceeded",
  "message": "You have exceeded the rate limit. Please try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```

---

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Anonymous users:** 100 requests per hour
- **Authenticated users:** 1000 requests per hour
- **File uploads:** 50 uploads per hour
- **Import processing:** 10 concurrent jobs per user

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1700812800
```

---

## Pagination

List endpoints support pagination with the following query parameters:

- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20, max: 100)

Pagination information is included in the response:

```json
{
  "count": 2500,
  "next": "http://localhost:8000/api/v1/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Filtering and Searching

Most list endpoints support filtering and searching:

### Query Parameters

- **Filtering:** Use field names as query parameters
  - Example: `?category=Groceries&type=DEBIT`

- **Searching:** Use the `search` parameter
  - Example: `?search=coffee`

- **Date Ranges:** Use `_from` and `_to` suffixes
  - Example: `?date_from=2025-11-01&date_to=2025-11-30`

- **Sorting:** Use the `ordering` parameter
  - Example: `?ordering=-created_at` (descending)
  - Example: `?ordering=amount` (ascending)

---

## Webhooks

The application can send webhooks for important events:

### Available Events

- `import.completed` - Import job completed
- `import.failed` - Import job failed
- `budget.exceeded` - Budget threshold exceeded
- `transaction.created` - New transaction created

### Webhook Payload Format

```json
{
  "event": "import.completed",
  "timestamp": "2025-11-24T05:00:00Z",
  "data": {
    "import_job_id": "uuid",
    "status": "COMPLETED",
    "successful_imports": 1450
  }
}
```

---

## API Versioning

The API uses URL-based versioning:

- **Current version:** `/api/v1/`
- **Deprecated versions:** Will be supported for 6 months after new version release
- **Version header:** `API-Version: 1.0`

---

## Testing the API

### Using cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# List transactions
curl -X GET http://localhost:8000/api/v1/transactions/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Upload file
curl -X POST http://localhost:8000/api/v1/import/uploads/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@transactions.csv"
```

### Using Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/v1/auth/login/',
    json={'email': 'user@example.com', 'password': 'password'}
)
token = response.json()['token']

# List transactions
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'http://localhost:8000/api/v1/transactions/',
    headers=headers
)
transactions = response.json()
```

---

**Last Updated:** 2025-11-24  
**API Version:** 1.0  
**Django Version:** 5.1.13  
**Python Version:** 3.12.3
