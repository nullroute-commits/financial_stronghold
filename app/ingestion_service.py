"""
Financial data ingestion service for processing various data sources.
Handles CSV, HTTPS endpoints, and API integrations.
"""

import csv
import json
import io
import re
import requests
import pandas as pd
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import UUID
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction as db_transaction
from sqlalchemy.orm import Session

from app.ingestion_models import (
    DataSource, IngestionJob, FieldMapping,
    DataSourceType, AuthenticationType, DataFormat,
    IngestionStatus
)
from app.financial_models import Transaction, Account
from app.services import TenantService
from app.core.db.connection import get_db_session
from app.core.tenant import TenantType
from app.transaction_classifier import TransactionClassifier
from app.tagging_service import TaggingService


class DataIngestionService:
    """Service for ingesting financial data from various sources."""
    
    def __init__(self, db: Session, tenant_type: str, tenant_id: str):
        self.db = db
        self.tenant_type = tenant_type
        self.tenant_id = tenant_id
        self.tenant_service = TenantService(db=db, model=Transaction)
        self.tagging_service = TaggingService(db=db)
        self.classifier = TransactionClassifier()
        
    def create_ingestion_job(self, data_source: DataSource, **kwargs) -> IngestionJob:
        """Create a new ingestion job."""
        job = IngestionJob(
            data_source=data_source,
            tenant_type=self.tenant_type,
            tenant_id=self.tenant_id,
            **kwargs
        )
        self.db.add(job)
        self.db.commit()
        return job
    
    def fetch_data_from_source(self, data_source: DataSource) -> Tuple[Any, str]:
        """Fetch data from the configured source."""
        if data_source.source_type == DataSourceType.CSV_URL:
            return self._fetch_csv_from_url(data_source)
        elif data_source.source_type == DataSourceType.HTTPS_ENDPOINT:
            return self._fetch_https_data(data_source)
        elif data_source.source_type == DataSourceType.API_ENDPOINT:
            return self._fetch_api_data(data_source)
        else:
            raise ValueError(f"Unsupported source type: {data_source.source_type}")
    
    def _fetch_csv_from_url(self, data_source: DataSource) -> Tuple[str, str]:
        """Fetch CSV data from URL."""
        headers = self._build_auth_headers(data_source)
        response = requests.get(
            data_source.source_url,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.text, 'csv'
    
    def _fetch_https_data(self, data_source: DataSource) -> Tuple[Any, str]:
        """Fetch data from HTTPS endpoint."""
        headers = self._build_auth_headers(data_source)
        response = requests.get(
            data_source.source_url,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        # Determine format from content type or configuration
        content_type = response.headers.get('Content-Type', '')
        if 'json' in content_type or data_source.data_format == DataFormat.JSON:
            return response.json(), 'json'
        elif 'xml' in content_type or data_source.data_format == DataFormat.XML:
            return response.text, 'xml'
        else:
            return response.text, 'csv'
    
    def _fetch_api_data(self, data_source: DataSource) -> Tuple[Any, str]:
        """Fetch data from API endpoint with pagination support."""
        headers = self._build_auth_headers(data_source)
        
        # Check if pagination is configured
        pagination_config = data_source.transform_config.get('pagination', {})
        if pagination_config:
            return self._fetch_paginated_data(data_source, headers, pagination_config)
        else:
            response = requests.get(
                data_source.source_url,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json(), 'json'
    
    def _fetch_paginated_data(self, data_source: DataSource, headers: Dict,
                             pagination_config: Dict) -> Tuple[List[Dict], str]:
        """Handle paginated API responses."""
        all_data = []
        page = pagination_config.get('start_page', 1)
        page_param = pagination_config.get('page_param', 'page')
        data_path = pagination_config.get('data_path', '')
        max_pages = pagination_config.get('max_pages', 100)
        
        while page <= max_pages:
            params = {page_param: page}
            response = requests.get(
                data_source.source_url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract data from nested path if configured
            if data_path:
                for key in data_path.split('.'):
                    data = data.get(key, [])
            
            if not data or not isinstance(data, list):
                break
                
            all_data.extend(data)
            page += 1
            
            # Check if we've reached the last page
            if len(data) < pagination_config.get('page_size', 100):
                break
        
        return all_data, 'json'
    
    def _build_auth_headers(self, data_source: DataSource) -> Dict[str, str]:
        """Build authentication headers based on auth type."""
        headers = {'User-Agent': 'FinancialStronghold/1.0'}
        
        if data_source.auth_type == AuthenticationType.NONE:
            return headers
            
        auth_config = data_source.auth_config or {}
        
        if data_source.auth_type == AuthenticationType.BEARER:
            token = auth_config.get('token')
            if token:
                headers['Authorization'] = f'Bearer {token}'
                
        elif data_source.auth_type == AuthenticationType.API_KEY:
            key_name = auth_config.get('key_name', 'X-API-Key')
            key_value = auth_config.get('key_value')
            if key_value:
                headers[key_name] = key_value
                
        elif data_source.auth_type == AuthenticationType.BASIC:
            import base64
            username = auth_config.get('username')
            password = auth_config.get('password')
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers['Authorization'] = f'Basic {credentials}'
                
        elif data_source.auth_type == AuthenticationType.CUSTOM_HEADER:
            custom_headers = auth_config.get('headers', {})
            headers.update(custom_headers)
        
        return headers
    
    def parse_data(self, raw_data: Any, data_format: str, 
                   field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse raw data into standardized format."""
        if data_format == 'csv':
            return self._parse_csv(raw_data, field_mapping)
        elif data_format == 'json':
            return self._parse_json(raw_data, field_mapping)
        elif data_format == 'xml':
            return self._parse_xml(raw_data, field_mapping)
        else:
            raise ValueError(f"Unsupported data format: {data_format}")
    
    def _parse_csv(self, csv_data: str, field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse CSV data."""
        reader = csv.DictReader(io.StringIO(csv_data))
        parsed_data = []
        
        for row in reader:
            mapped_row = {}
            for source_field, target_field in field_mapping.items():
                if source_field in row:
                    mapped_row[target_field] = row[source_field]
            parsed_data.append(mapped_row)
        
        return parsed_data
    
    def _parse_json(self, json_data: Union[List, Dict], 
                    field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse JSON data."""
        if isinstance(json_data, dict):
            # Single object, wrap in list
            json_data = [json_data]
        
        parsed_data = []
        for item in json_data:
            mapped_item = {}
            for source_field, target_field in field_mapping.items():
                # Support nested field access with dot notation
                value = self._get_nested_value(item, source_field)
                if value is not None:
                    mapped_item[target_field] = value
            parsed_data.append(mapped_item)
        
        return parsed_data
    
    def _parse_xml(self, xml_data: str, field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse XML data."""
        root = ET.fromstring(xml_data)
        parsed_data = []
        
        # Find all transaction elements (configurable)
        transaction_xpath = './/transaction'  # Default, can be configured
        for elem in root.findall(transaction_xpath):
            mapped_item = {}
            for source_field, target_field in field_mapping.items():
                value = elem.find(source_field)
                if value is not None and value.text:
                    mapped_item[target_field] = value.text
            parsed_data.append(mapped_item)
        
        return parsed_data
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def validate_data(self, data: List[Dict[str, Any]], 
                     validation_rules: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """Validate parsed data against rules."""
        valid_records = []
        invalid_records = []
        
        for idx, record in enumerate(data):
            errors = []
            
            # Check required fields
            required_fields = validation_rules.get('required_fields', [])
            for field in required_fields:
                if not record.get(field):
                    errors.append(f"Missing required field: {field}")
            
            # Validate data types
            type_rules = validation_rules.get('field_types', {})
            for field, expected_type in type_rules.items():
                if field in record and record[field]:
                    if not self._validate_type(record[field], expected_type):
                        errors.append(f"Invalid type for {field}: expected {expected_type}")
            
            # Custom validation rules
            custom_rules = validation_rules.get('custom_rules', [])
            for rule in custom_rules:
                if not self._apply_custom_rule(record, rule):
                    errors.append(rule.get('error_message', 'Custom validation failed'))
            
            if errors:
                invalid_records.append({
                    'index': idx,
                    'record': record,
                    'errors': errors
                })
            else:
                valid_records.append(record)
        
        return valid_records, invalid_records
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value matches expected type."""
        try:
            if expected_type == 'decimal':
                Decimal(str(value))
            elif expected_type == 'integer':
                int(value)
            elif expected_type == 'date':
                pd.to_datetime(value)
            elif expected_type == 'boolean':
                str(value).lower() in ('true', 'false', '1', '0', 'yes', 'no')
            return True
        except (ValueError, TypeError):
            return False
    
    def _apply_custom_rule(self, record: Dict, rule: Dict) -> bool:
        """Apply custom validation rule."""
        rule_type = rule.get('type')
        
        if rule_type == 'regex':
            field = rule.get('field')
            pattern = rule.get('pattern')
            if field in record and pattern:
                return bool(re.match(pattern, str(record[field])))
                
        elif rule_type == 'range':
            field = rule.get('field')
            min_val = rule.get('min')
            max_val = rule.get('max')
            if field in record:
                try:
                    value = float(record[field])
                    if min_val is not None and value < min_val:
                        return False
                    if max_val is not None and value > max_val:
                        return False
                    return True
                except (ValueError, TypeError):
                    return False
        
        return True
    
    def transform_data(self, data: List[Dict[str, Any]], 
                      transform_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply transformations to data."""
        transformed_data = []
        
        for record in data:
            transformed_record = record.copy()
            
            # Apply field transformations
            field_transforms = transform_config.get('field_transforms', {})
            for field, transform in field_transforms.items():
                if field in transformed_record:
                    transformed_record[field] = self._apply_transform(
                        transformed_record[field], transform
                    )
            
            # Apply calculated fields
            calculated_fields = transform_config.get('calculated_fields', {})
            for field_name, calculation in calculated_fields.items():
                transformed_record[field_name] = self._calculate_field(
                    transformed_record, calculation
                )
            
            transformed_data.append(transformed_record)
        
        return transformed_data
    
    def _apply_transform(self, value: Any, transform: Dict[str, Any]) -> Any:
        """Apply transformation to a value."""
        transform_type = transform.get('type')
        
        if transform_type == 'uppercase':
            return str(value).upper()
        elif transform_type == 'lowercase':
            return str(value).lower()
        elif transform_type == 'trim':
            return str(value).strip()
        elif transform_type == 'replace':
            pattern = transform.get('pattern', '')
            replacement = transform.get('replacement', '')
            return str(value).replace(pattern, replacement)
        elif transform_type == 'regex_replace':
            pattern = transform.get('pattern', '')
            replacement = transform.get('replacement', '')
            return re.sub(pattern, replacement, str(value))
        elif transform_type == 'date_format':
            input_format = transform.get('input_format')
            output_format = transform.get('output_format', '%Y-%m-%d')
            try:
                date_obj = pd.to_datetime(value, format=input_format)
                return date_obj.strftime(output_format)
            except:
                return value
        elif transform_type == 'decimal':
            decimal_places = transform.get('decimal_places', 2)
            try:
                return round(Decimal(str(value)), decimal_places)
            except:
                return value
        
        return value
    
    def _calculate_field(self, record: Dict[str, Any], calculation: Dict[str, Any]) -> Any:
        """Calculate a new field based on existing fields."""
        calc_type = calculation.get('type')
        
        if calc_type == 'concatenate':
            fields = calculation.get('fields', [])
            separator = calculation.get('separator', ' ')
            values = [str(record.get(f, '')) for f in fields]
            return separator.join(values)
            
        elif calc_type == 'arithmetic':
            expression = calculation.get('expression', '')
            # Safe evaluation with only arithmetic operations
            try:
                # Replace field names with values
                for field, value in record.items():
                    if field in expression:
                        expression = expression.replace(field, str(value))
                # Evaluate (be careful with security here)
                return eval(expression)
            except:
                return None
                
        elif calc_type == 'conditional':
            condition = calculation.get('condition', {})
            true_value = calculation.get('true_value')
            false_value = calculation.get('false_value')
            
            # Evaluate condition
            if self._evaluate_condition(record, condition):
                return true_value
            else:
                return false_value
        
        return None
    
    def _evaluate_condition(self, record: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate a condition."""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        if field not in record:
            return False
            
        record_value = record[field]
        
        if operator == 'equals':
            return str(record_value) == str(value)
        elif operator == 'not_equals':
            return str(record_value) != str(value)
        elif operator == 'contains':
            return str(value) in str(record_value)
        elif operator == 'greater_than':
            try:
                return float(record_value) > float(value)
            except:
                return False
        elif operator == 'less_than':
            try:
                return float(record_value) < float(value)
            except:
                return False
        
        return False
    
    def import_transactions(self, data: List[Dict[str, Any]], 
                          data_source: DataSource,
                          job: IngestionJob,
                          config: Dict[str, Any]) -> Dict[str, Any]:
        """Import validated and transformed data as transactions."""
        results = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }
        
        # Get default account if specified
        default_account = None
        if data_source.default_account_id:
            default_account = self.db.query(Account).filter_by(
                id=data_source.default_account_id,
                tenant_type=self.tenant_type,
                tenant_id=self.tenant_id
            ).first()
        
        for idx, record in enumerate(data):
            try:
                # Check for duplicates if configured
                if config.get('skip_duplicates', True):
                    if self._is_duplicate_transaction(record):
                        results['skipped'] += 1
                        continue
                
                # Create transaction
                transaction_data = self._prepare_transaction_data(
                    record, data_source, default_account, config
                )
                
                # Create or update transaction
                if config.get('update_existing', False):
                    existing = self._find_existing_transaction(record)
                    if existing:
                        for key, value in transaction_data.items():
                            setattr(existing, key, value)
                        results['updated'] += 1
                    else:
                        transaction = Transaction(**transaction_data)
                        self.db.add(transaction)
                        results['created'] += 1
                else:
                    transaction = Transaction(**transaction_data)
                    self.db.add(transaction)
                    results['created'] += 1
                
                # Apply tags
                if config.get('apply_default_tags', True) and data_source.default_tags:
                    # Apply default tags (implementation depends on tagging service)
                    pass
                
                # Auto-categorize if enabled
                if config.get('auto_categorize', True):
                    # Use transaction classifier
                    pass
                
                # Commit periodically for large imports
                if (idx + 1) % config.get('batch_size', 100) == 0:
                    self.db.commit()
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'index': idx,
                    'error': str(e),
                    'record': record
                })
        
        # Final commit
        self.db.commit()
        
        return results
    
    def _prepare_transaction_data(self, record: Dict[str, Any],
                                 data_source: DataSource,
                                 default_account: Optional[Account],
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare transaction data for creation."""
        # Map fields to transaction model
        transaction_data = {
            'tenant_type': self.tenant_type,
            'tenant_id': self.tenant_id,
        }
        
        # Standard field mappings
        field_map = {
            'date': 'date',
            'description': 'description',
            'amount': 'amount',
            'category': 'category',
            'account_id': 'account_id',
            'reference': 'reference_number',
            'notes': 'notes'
        }
        
        for record_field, trans_field in field_map.items():
            if record_field in record:
                value = record[record_field]
                
                # Special handling for different fields
                if trans_field == 'date':
                    value = pd.to_datetime(value).date()
                elif trans_field == 'amount':
                    value = Decimal(str(value))
                elif trans_field == 'account_id' and not value and default_account:
                    value = default_account.id
                    
                transaction_data[trans_field] = value
        
        # Set defaults
        if 'account_id' not in transaction_data and default_account:
            transaction_data['account_id'] = default_account.id
            
        return transaction_data
    
    def _is_duplicate_transaction(self, record: Dict[str, Any]) -> bool:
        """Check if transaction already exists."""
        # Simple duplicate check based on date, amount, and description
        # Can be enhanced with more sophisticated logic
        query = self.db.query(Transaction).filter_by(
            tenant_type=self.tenant_type,
            tenant_id=self.tenant_id,
            date=pd.to_datetime(record.get('date')).date(),
            amount=Decimal(str(record.get('amount', 0))),
            description=record.get('description')
        )
        
        return query.first() is not None
    
    def _find_existing_transaction(self, record: Dict[str, Any]) -> Optional[Transaction]:
        """Find existing transaction for update."""
        # Can use various strategies - reference number, date+amount+description, etc.
        reference = record.get('reference')
        if reference:
            return self.db.query(Transaction).filter_by(
                tenant_type=self.tenant_type,
                tenant_id=self.tenant_id,
                reference_number=reference
            ).first()
        
        return None
    
    def preview_data(self, data_source: DataSource, preview_rows: int = 10) -> Dict[str, Any]:
        """Preview data from source without importing."""
        try:
            # Fetch data
            raw_data, data_format = self.fetch_data_from_source(data_source)
            
            # Parse data
            parsed_data = self.parse_data(
                raw_data, data_format, 
                data_source.field_mapping or {}
            )
            
            # Get sample
            sample_data = parsed_data[:preview_rows]
            
            # Detect columns and types
            if sample_data:
                columns = list(sample_data[0].keys())
                data_types = {}
                
                for col in columns:
                    # Simple type detection
                    sample_values = [row.get(col) for row in sample_data if row.get(col)]
                    if sample_values:
                        data_types[col] = self._detect_data_type(sample_values)
                
                # Suggest mappings
                suggested_mappings = self._suggest_field_mappings(columns)
                
                return {
                    'columns': columns,
                    'data_types': data_types,
                    'sample_data': sample_data,
                    'total_rows': len(parsed_data),
                    'suggested_mappings': suggested_mappings
                }
            
            return {
                'columns': [],
                'data_types': {},
                'sample_data': [],
                'total_rows': 0,
                'suggested_mappings': {}
            }
            
        except Exception as e:
            raise Exception(f"Failed to preview data: {str(e)}")
    
    def _detect_data_type(self, values: List[Any]) -> str:
        """Detect data type from sample values."""
        # Try different type conversions
        all_decimal = True
        all_int = True
        all_date = True
        
        for value in values[:10]:  # Check first 10 values
            try:
                float(value)
            except:
                all_decimal = False
                all_int = False
                
            try:
                int(value)
            except:
                all_int = False
                
            try:
                pd.to_datetime(value)
            except:
                all_date = False
        
        if all_int:
            return 'integer'
        elif all_decimal:
            return 'decimal'
        elif all_date:
            return 'date'
        else:
            return 'string'
    
    def _suggest_field_mappings(self, columns: List[str]) -> Dict[str, str]:
        """Suggest field mappings based on column names."""
        suggestions = {}
        
        # Common patterns for transaction fields
        patterns = {
            'date': ['date', 'transaction_date', 'posted_date', 'trans_date'],
            'description': ['description', 'desc', 'memo', 'details', 'narrative'],
            'amount': ['amount', 'value', 'debit', 'credit', 'transaction_amount'],
            'category': ['category', 'type', 'classification', 'trans_type'],
            'reference': ['reference', 'ref', 'check_no', 'transaction_id'],
            'account': ['account', 'account_name', 'account_number']
        }
        
        for column in columns:
            column_lower = column.lower()
            for field, patterns_list in patterns.items():
                for pattern in patterns_list:
                    if pattern in column_lower:
                        suggestions[column] = field
                        break
        
        return suggestions