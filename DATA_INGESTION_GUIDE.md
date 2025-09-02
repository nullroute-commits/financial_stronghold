# Financial Data Ingestion Feature Guide

## Overview

The Financial Data Ingestion feature enables users to import financial transactions from various data sources including CSV files, HTTPS endpoints, and API integrations. This comprehensive system supports automated scheduling, data transformation, validation, and duplicate detection.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Data Ingestion Architecture                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Data Sources                                    │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ CSV Upload  │  │  CSV URL    │  │HTTPS Endpoint│ │ API Endpoint    │    │
│  │   Files     │  │   Fetch     │  │   (REST)     │ │ (Paginated)     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Ingestion Pipeline                                  │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │   Fetch     │→ │   Parse     │→ │  Validate   │→ │   Transform     │    │
│  │   Data      │  │   Data      │  │   Data      │  │    Data         │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Import & Storage                                    │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐    │
│  │ Duplicate   │  │Transaction  │  │   Apply     │  │   Store in      │    │
│  │ Detection   │→ │  Creation   │→ │   Tags      │→ │   Database      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

### 1. Multiple Data Source Types

#### CSV Upload
- Direct file upload through web interface
- Drag-and-drop support
- Automatic encoding detection

#### CSV from URL
- Fetch CSV files from HTTPS URLs
- Scheduled fetching support
- Authentication support

#### HTTPS Endpoints
- REST API integration
- JSON/XML data format support
- Custom header configuration

#### API Endpoints
- Full API integration
- Pagination support
- OAuth2, Bearer token, API key authentication

### 2. Authentication Methods

- **None**: No authentication required
- **Basic Authentication**: Username/password
- **Bearer Token**: JWT or other bearer tokens
- **API Key**: Custom header API keys
- **OAuth 2.0**: Full OAuth2 flow support
- **Custom Headers**: Any custom authentication headers

### 3. Data Formats Supported

- **CSV**: Comma-separated values
- **JSON**: JavaScript Object Notation
- **XML**: Extensible Markup Language
- **XLSX**: Microsoft Excel
- **OFX**: Open Financial Exchange
- **QIF**: Quicken Interchange Format

### 4. Field Mapping System

The field mapping system allows flexible mapping between source data fields and transaction fields:

```json
{
  "source_date": "date",
  "merchant_name": "description",
  "debit_amount": "amount",
  "trans_category": "category",
  "reference_no": "reference"
}
```

### 5. Data Transformation

#### Built-in Transformations
- **Text**: uppercase, lowercase, trim, replace
- **Date**: format conversion, timezone adjustment
- **Number**: decimal precision, currency conversion
- **Regex**: pattern-based replacements

#### Calculated Fields
- Concatenation of multiple fields
- Arithmetic operations
- Conditional logic

### 6. Validation Rules

- **Required Fields**: Ensure critical fields are present
- **Data Type Validation**: Verify correct data types
- **Range Validation**: Min/max values for amounts
- **Pattern Matching**: Regex validation
- **Custom Rules**: Business logic validation

### 7. Import Configuration

- **Skip Duplicates**: Prevent duplicate transactions
- **Update Existing**: Update matching transactions
- **Dry Run**: Preview without importing
- **Batch Size**: Control processing chunks
- **Auto-categorization**: Apply ML classification
- **Default Tags**: Apply tags automatically

### 8. Scheduling

- **Manual**: On-demand imports
- **Hourly**: Every hour
- **Daily**: Once per day at specified time
- **Weekly**: Specific days of the week
- **Monthly**: Specific day of month
- **Custom**: Cron expression support

## API Endpoints

### Data Source Management

```
POST   /financial/data-ingestion/sources              # Create data source
GET    /financial/data-ingestion/sources              # List data sources
GET    /financial/data-ingestion/sources/{id}         # Get data source
PUT    /financial/data-ingestion/sources/{id}         # Update data source
DELETE /financial/data-ingestion/sources/{id}         # Delete data source
```

### Data Operations

```
POST   /financial/data-ingestion/sources/{id}/preview # Preview data
POST   /financial/data-ingestion/sources/{id}/import  # Import data
POST   /financial/data-ingestion/sources/{id}/upload  # Upload file
POST   /financial/data-ingestion/preview              # Preview without source
```

### Job Management

```
GET    /financial/data-ingestion/jobs                 # List import jobs
GET    /financial/data-ingestion/jobs/{id}            # Get job details
POST   /financial/data-ingestion/jobs/{id}/cancel     # Cancel running job
```

## Web GUI Interface

### Data Sources Page (`/data-sources/`)
- List all configured data sources
- Create new data sources with wizard
- View source configuration
- Trigger manual imports
- Monitor source status

### Upload Page (`/upload/`)
- Drag-and-drop file upload
- Select data source configuration
- Preview data before import
- Configure import options
- View import progress

### Import Jobs Page (`/import-jobs/`)
- List all import jobs
- Filter by status, source, date
- View job details and errors
- Cancel running jobs

## Usage Examples

### 1. Create CSV Upload Source

```python
# Using API
data_source = {
    "name": "Bank Statement CSV",
    "source_type": "csv_upload",
    "data_format": "csv",
    "field_mapping": {
        "Date": "date",
        "Description": "description",
        "Amount": "amount",
        "Category": "category"
    },
    "default_account_id": "123e4567-e89b-12d3-a456-426614174000",
    "default_tags": ["imported", "bank-statement"]
}
```

### 2. Create API Endpoint Source

```python
# API endpoint with pagination
data_source = {
    "name": "Banking API",
    "source_type": "api_endpoint",
    "source_url": "https://api.bank.com/v1/transactions",
    "auth_type": "bearer",
    "auth_config": {
        "token": "your-api-token"
    },
    "data_format": "json",
    "field_mapping": {
        "transaction_date": "date",
        "merchant": "description",
        "amount": "amount",
        "type": "category"
    },
    "transform_config": {
        "pagination": {
            "page_param": "page",
            "page_size": 100,
            "data_path": "data.transactions"
        }
    }
}
```

### 3. Configure Field Transformations

```python
transform_config = {
    "field_transforms": {
        "description": {
            "type": "uppercase"
        },
        "amount": {
            "type": "decimal",
            "decimal_places": 2
        }
    },
    "calculated_fields": {
        "full_description": {
            "type": "concatenate",
            "fields": ["merchant", "location"],
            "separator": " - "
        }
    }
}
```

## Best Practices

### 1. Data Source Configuration
- Use descriptive names for data sources
- Document field mappings clearly
- Test with preview before full import
- Enable scheduling for regular imports

### 2. Authentication Security
- Store credentials securely
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use OAuth2 when available

### 3. Data Quality
- Validate data formats before import
- Set up appropriate validation rules
- Handle missing or invalid data gracefully
- Monitor import job success rates

### 4. Performance
- Use appropriate batch sizes
- Schedule imports during off-peak hours
- Enable duplicate detection to avoid redundancy
- Clean up old import jobs periodically

### 5. Error Handling
- Review failed imports promptly
- Check error logs for patterns
- Adjust validation rules as needed
- Use dry run for testing

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify credentials are correct
   - Check API endpoint URLs
   - Ensure tokens haven't expired

2. **Field Mapping Errors**
   - Verify source field names match exactly
   - Check for case sensitivity
   - Ensure data types are compatible

3. **Duplicate Detection**
   - Review duplicate detection logic
   - Check date/amount/description matching
   - Consider using reference numbers

4. **Performance Issues**
   - Reduce batch size for large imports
   - Schedule during low-usage periods
   - Check network connectivity

### Debug Tips

1. Use preview to test data source configuration
2. Start with dry run before actual import
3. Check import job logs for detailed errors
4. Test with small data sets first

## Security Considerations

1. **Data Encryption**
   - All credentials stored encrypted
   - HTTPS required for all endpoints
   - Secure file upload handling

2. **Access Control**
   - User-level data isolation
   - Role-based permissions
   - Audit logging for all operations

3. **Data Privacy**
   - PII handling compliance
   - Data retention policies
   - Right to deletion support

## Future Enhancements

1. **Additional Data Sources**
   - FTP/SFTP support
   - Email attachment processing
   - Direct bank connections

2. **Advanced Features**
   - Machine learning for mapping suggestions
   - Automatic error correction
   - Real-time streaming data

3. **Integration Improvements**
   - Webhook support for real-time updates
   - Third-party service integrations
   - Mobile app support

## Conclusion

The Financial Data Ingestion feature provides a comprehensive solution for importing financial data from various sources. With support for multiple formats, authentication methods, and advanced transformation capabilities, it enables efficient and reliable data import workflows for financial management.