"""
File import service for processing uploaded files.
Handles CSV, Excel, and PDF file import with comprehensive validation.

Created by Team Sigma (Data Processing & Import) - Sprint 7
"""

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
import hashlib
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone

from ..import_models import ImportJob, FileUpload, ImportedTransaction, ImportValidationError
from ..django_models import Account, Transaction

logger = logging.getLogger('import')


class FileImportService:
    """Main orchestrator for file import process."""
    
    def __init__(self, user):
        self.user = user
        self.csv_parser = CSVParserService()
        self.validator = ImportDataValidator()
        self.duplicate_detector = DuplicateDetectionService()
    
    async def process_file_upload(self, file_obj, import_settings=None):
        """Process uploaded file through complete import pipeline."""
        
        # 1. Create file upload record
        file_upload = await self._create_file_upload_record(file_obj)
        
        # 2. Validate file security
        if not file_upload.validate_file_security():
            raise ValueError("File failed security validation")
        
        # 3. Create import job
        import_job = await self._create_import_job(file_upload, import_settings)
        
        # 4. Process file based on type
        try:
            if file_upload.mime_type in ['text/csv', 'application/csv']:
                await self._process_csv_file(import_job, file_upload)
            elif 'excel' in file_upload.mime_type:
                await self._process_excel_file(import_job, file_upload)
            elif file_upload.mime_type == 'application/pdf':
                await self._process_pdf_file(import_job, file_upload)
            else:
                raise ValueError(f"Unsupported file type: {file_upload.mime_type}")
            
            import_job.mark_completed()
            
        except Exception as e:
            import_job.mark_failed(str(e))
            logger.error(f"Import job {import_job.id} failed: {str(e)}")
            raise
        
        return import_job
    
    async def _create_file_upload_record(self, file_obj):
        """Create file upload record with security validation."""
        
        # Calculate file hash
        file_obj.seek(0)
        file_content = file_obj.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_obj.seek(0)
        
        # Detect MIME type
        mime_type = magic.from_buffer(file_content[:1024], mime=True)
        
        file_upload = FileUpload.objects.create(
            user=self.user,
            file=file_obj,
            original_filename=file_obj.name,
            file_size=file_obj.size,
            file_hash=file_hash,
            mime_type=mime_type
        )
        
        logger.info(f"File upload created: {file_upload.id}", extra={
            'user_id': str(self.user.id),
            'filename': file_obj.name,
            'file_size': file_obj.size,
            'mime_type': mime_type
        })
        
        return file_upload
    
    async def _create_import_job(self, file_upload, import_settings):
        """Create import job for processing."""
        
        # Determine file type
        file_type_mapping = {
            'text/csv': ImportJob.FileType.CSV,
            'application/csv': ImportJob.FileType.CSV,
            'application/vnd.ms-excel': ImportJob.FileType.EXCEL,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ImportJob.FileType.EXCEL,
            'application/pdf': ImportJob.FileType.PDF,
        }
        
        file_type = file_type_mapping.get(file_upload.mime_type, ImportJob.FileType.CSV)
        
        import_job = ImportJob.objects.create(
            user=self.user,
            filename=file_upload.file.name,
            original_filename=file_upload.original_filename,
            file_type=file_type,
            file_size=file_upload.file_size,
            file_hash=file_upload.file_hash,
            import_settings=import_settings or {}
        )
        
        # Link file upload to import job
        file_upload.import_job = import_job
        file_upload.save(update_fields=['import_job'])
        
        logger.info(f"Import job created: {import_job.id}", extra={
            'user_id': str(self.user.id),
            'file_type': file_type,
            'file_size': file_upload.file_size
        })
        
        return import_job
    
    async def _process_csv_file(self, import_job, file_upload):
        """Process CSV file import."""
        import_job.mark_started()
        
        try:
            # Parse CSV file
            df = self.csv_parser.parse_csv_file(file_upload.file.path)
            import_job.total_rows = len(df)
            import_job.save(update_fields=['total_rows'])
            
            # Process each row
            for index, row in df.iterrows():
                await self._process_transaction_row(import_job, index + 1, row.to_dict())
                
                # Update progress every 100 rows
                if (index + 1) % 100 == 0:
                    import_job.update_progress(
                        processed_rows=index + 1,
                        successful_imports=import_job.successful_imports,
                        failed_imports=import_job.failed_imports
                    )
            
            # Final progress update
            import_job.update_progress(
                processed_rows=len(df),
                successful_imports=import_job.successful_imports,
                failed_imports=import_job.failed_imports
            )
            
        except Exception as e:
            logger.error(f"CSV processing failed for job {import_job.id}: {str(e)}")
            raise
    
    async def _process_excel_file(self, import_job, file_upload):
        """Process Excel file import (placeholder for Sprint 8)."""
        # Will be implemented in Sprint 8
        raise NotImplementedError("Excel import will be implemented in Sprint 8")
    
    async def _process_pdf_file(self, import_job, file_upload):
        """Process PDF file import (placeholder for Sprint 9)."""
        # Will be implemented in Sprint 9
        raise NotImplementedError("PDF import will be implemented in Sprint 9")
    
    async def _process_transaction_row(self, import_job, row_number, row_data):
        """Process individual transaction row."""
        try:
            # Validate row data
            validation_result = self.validator.validate_transaction_row(row_data, row_number)
            
            if validation_result['is_valid']:
                # Create imported transaction
                imported_transaction = ImportedTransaction.objects.create(
                    import_job=import_job,
                    row_number=row_number,
                    amount=validation_result['amount'],
                    currency=validation_result.get('currency', 'USD'),
                    date=validation_result['date'],
                    description=validation_result['description'],
                    raw_data=row_data,
                    validation_errors=validation_result.get('warnings', [])
                )
                
                # Check for duplicates
                duplicate_result = self.duplicate_detector.check_for_duplicate(
                    imported_transaction, self.user
                )
                
                if duplicate_result['is_duplicate']:
                    imported_transaction.mark_as_duplicate(
                        duplicate_result['existing_transaction'],
                        duplicate_result['confidence']
                    )
                
                import_job.successful_imports += 1
                
            else:
                # Create validation error records
                for error in validation_result['errors']:
                    ImportValidationError.objects.create(
                        import_job=import_job,
                        row_number=row_number,
                        field_name=error['field'],
                        severity=ImportValidationError.Severity.ERROR,
                        error_code=error['code'],
                        error_message=error['message'],
                        raw_value=error.get('value', ''),
                        suggested_fix=error.get('suggestion', '')
                    )
                
                import_job.failed_imports += 1
        
        except Exception as e:
            logger.error(f"Error processing row {row_number}: {str(e)}")
            import_job.failed_imports += 1


class CSVParserService:
    """Specialized CSV file parsing service."""
    
    def __init__(self):
        self.common_encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        self.date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%m-%d-%Y', '%d-%m-%Y', '%m/%d/%y', '%d/%m/%y',
            '%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y'
        ]
    
    def parse_csv_file(self, file_path):
        """Parse CSV file with robust encoding and format detection."""
        
        # Try different encodings
        for encoding in self.common_encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"CSV parsed successfully with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"CSV parsing failed with encoding {encoding}: {str(e)}")
                continue
        else:
            raise ValueError("Unable to parse CSV file with any supported encoding")
        
        # Detect and standardize column names
        df = self._standardize_column_names(df)
        
        # Validate CSV structure
        self._validate_csv_structure(df)
        
        return df
    
    def _standardize_column_names(self, df):
        """Standardize column names for easier mapping."""
        
        # Common column name mappings
        column_mappings = {
            # Date columns
            'date': ['date', 'transaction_date', 'trans_date', 'posting_date', 'value_date'],
            # Amount columns
            'amount': ['amount', 'transaction_amount', 'value', 'debit', 'credit'],
            # Description columns
            'description': ['description', 'transaction_description', 'memo', 'reference', 'details'],
            # Account columns
            'account': ['account', 'account_number', 'account_name'],
        }
        
        # Create reverse mapping
        reverse_mapping = {}
        for standard_name, variations in column_mappings.items():
            for variation in variations:
                reverse_mapping[variation.lower()] = standard_name
        
        # Rename columns
        new_columns = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in reverse_mapping:
                new_columns[col] = reverse_mapping[col_lower]
        
        if new_columns:
            df = df.rename(columns=new_columns)
            logger.info(f"Standardized column names: {new_columns}")
        
        return df
    
    def _validate_csv_structure(self, df):
        """Validate CSV file structure."""
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        if len(df.columns) < 3:
            raise ValueError("CSV file must have at least 3 columns (date, amount, description)")
        
        # Check for required columns
        required_columns = ['date', 'amount', 'description']
        missing_columns = []
        
        for req_col in required_columns:
            if req_col not in df.columns:
                # Try to find similar column names
                similar_cols = [col for col in df.columns if req_col in col.lower()]
                if not similar_cols:
                    missing_columns.append(req_col)
        
        if missing_columns:
            raise ValueError(f"CSV file missing required columns: {missing_columns}")
        
        logger.info(f"CSV structure validated: {len(df)} rows, {len(df.columns)} columns")
    
    def detect_column_types(self, df):
        """Automatically detect column data types."""
        
        column_types = {}
        
        for column in df.columns:
            sample_values = df[column].dropna().head(10).astype(str)
            
            # Detect date columns
            if self._is_date_column(sample_values):
                column_types[column] = 'date'
            # Detect amount columns
            elif self._is_amount_column(sample_values):
                column_types[column] = 'amount'
            # Detect description columns
            elif self._is_description_column(sample_values):
                column_types[column] = 'description'
            else:
                column_types[column] = 'text'
        
        return column_types
    
    def _is_date_column(self, sample_values):
        """Check if column contains date values."""
        date_indicators = 0
        
        for value in sample_values:
            # Try parsing with common date formats
            for date_format in self.date_formats:
                try:
                    datetime.strptime(value, date_format)
                    date_indicators += 1
                    break
                except ValueError:
                    continue
        
        return date_indicators >= len(sample_values) * 0.8  # 80% must be dates
    
    def _is_amount_column(self, sample_values):
        """Check if column contains monetary amounts."""
        amount_indicators = 0
        
        for value in sample_values:
            # Remove common currency symbols and formatting
            clean_value = value.replace('$', '').replace(',', '').replace('€', '').replace('£', '')
            clean_value = clean_value.replace('(', '-').replace(')', '').strip()
            
            try:
                float(clean_value)
                amount_indicators += 1
            except ValueError:
                continue
        
        return amount_indicators >= len(sample_values) * 0.8  # 80% must be numbers
    
    def _is_description_column(self, sample_values):
        """Check if column contains transaction descriptions."""
        # Description columns typically have varied text content
        unique_ratio = len(set(sample_values)) / len(sample_values)
        avg_length = sum(len(str(v)) for v in sample_values) / len(sample_values)
        
        # High uniqueness and reasonable length suggests descriptions
        return unique_ratio > 0.7 and avg_length > 10


class ImportDataValidator:
    """Validate imported transaction data."""
    
    def __init__(self):
        self.date_formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%m-%d-%Y', '%d-%m-%Y', '%m/%d/%y', '%d/%m/%y',
            '%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y'
        ]
    
    def validate_transaction_row(self, row_data, row_number):
        """Validate individual transaction row."""
        
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'amount': None,
            'date': None,
            'description': None,
            'currency': 'USD'
        }
        
        # Validate amount
        amount_result = self._validate_amount(row_data.get('amount'), row_number)
        if amount_result['error']:
            result['errors'].append(amount_result['error'])
            result['is_valid'] = False
        else:
            result['amount'] = amount_result['value']
        
        # Validate date
        date_result = self._validate_date(row_data.get('date'), row_number)
        if date_result['error']:
            result['errors'].append(date_result['error'])
            result['is_valid'] = False
        else:
            result['date'] = date_result['value']
        
        # Validate description
        desc_result = self._validate_description(row_data.get('description'), row_number)
        if desc_result['error']:
            result['errors'].append(desc_result['error'])
            result['is_valid'] = False
        else:
            result['description'] = desc_result['value']
        
        # Validate currency (optional)
        if 'currency' in row_data:
            currency_result = self._validate_currency(row_data.get('currency'), row_number)
            if currency_result['warning']:
                result['warnings'].append(currency_result['warning'])
            result['currency'] = currency_result['value']
        
        return result
    
    def _validate_amount(self, amount_value, row_number):
        """Validate transaction amount."""
        result = {'value': None, 'error': None}
        
        if not amount_value:
            result['error'] = {
                'field': 'amount',
                'code': 'MISSING_AMOUNT',
                'message': 'Transaction amount is required',
                'value': amount_value
            }
            return result
        
        # Clean amount value
        clean_amount = str(amount_value).strip()
        
        # Handle negative amounts in parentheses (accounting format)
        if clean_amount.startswith('(') and clean_amount.endswith(')'):
            clean_amount = '-' + clean_amount[1:-1]
        
        # Remove currency symbols and formatting
        clean_amount = clean_amount.replace('$', '').replace(',', '')
        clean_amount = clean_amount.replace('€', '').replace('£', '').replace('¥', '')
        
        try:
            amount = Decimal(clean_amount)
            
            # Business rule validation
            if amount == 0:
                result['error'] = {
                    'field': 'amount',
                    'code': 'ZERO_AMOUNT',
                    'message': 'Transaction amount cannot be zero',
                    'value': amount_value
                }
            elif abs(amount) > Decimal('10000000'):  # $10M limit
                result['error'] = {
                    'field': 'amount',
                    'code': 'AMOUNT_TOO_LARGE',
                    'message': 'Transaction amount exceeds maximum limit ($10,000,000)',
                    'value': amount_value,
                    'suggestion': 'Verify amount is correct'
                }
            else:
                result['value'] = amount
                
        except (InvalidOperation, ValueError):
            result['error'] = {
                'field': 'amount',
                'code': 'INVALID_AMOUNT_FORMAT',
                'message': 'Invalid amount format',
                'value': amount_value,
                'suggestion': 'Amount must be a valid number (e.g., 123.45)'
            }
        
        return result
    
    def _validate_date(self, date_value, row_number):
        """Validate transaction date."""
        result = {'value': None, 'error': None}
        
        if not date_value:
            result['error'] = {
                'field': 'date',
                'code': 'MISSING_DATE',
                'message': 'Transaction date is required',
                'value': date_value
            }
            return result
        
        # Try parsing with different formats
        date_str = str(date_value).strip()
        
        for date_format in self.date_formats:
            try:
                parsed_date = datetime.strptime(date_str, date_format).date()
                
                # Business rule validation
                if parsed_date > date.today():
                    result['error'] = {
                        'field': 'date',
                        'code': 'FUTURE_DATE',
                        'message': 'Transaction date cannot be in the future',
                        'value': date_value,
                        'suggestion': 'Verify date is correct'
                    }
                elif parsed_date < date(1900, 1, 1):
                    result['error'] = {
                        'field': 'date',
                        'code': 'DATE_TOO_OLD',
                        'message': 'Transaction date is too old (before 1900)',
                        'value': date_value
                    }
                else:
                    result['value'] = parsed_date
                
                break
                
            except ValueError:
                continue
        else:
            result['error'] = {
                'field': 'date',
                'code': 'INVALID_DATE_FORMAT',
                'message': 'Invalid date format',
                'value': date_value,
                'suggestion': 'Use format like YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY'
            }
        
        return result
    
    def _validate_description(self, description_value, row_number):
        """Validate transaction description."""
        result = {'value': None, 'error': None}
        
        if not description_value:
            result['error'] = {
                'field': 'description',
                'code': 'MISSING_DESCRIPTION',
                'message': 'Transaction description is required',
                'value': description_value
            }
            return result
        
        description = str(description_value).strip()
        
        # Length validation
        if len(description) > 500:
            result['error'] = {
                'field': 'description',
                'code': 'DESCRIPTION_TOO_LONG',
                'message': 'Description too long (maximum 500 characters)',
                'value': description_value,
                'suggestion': 'Truncate description to 500 characters'
            }
        elif len(description) < 2:
            result['error'] = {
                'field': 'description',
                'code': 'DESCRIPTION_TOO_SHORT',
                'message': 'Description too short (minimum 2 characters)',
                'value': description_value
            }
        else:
            result['value'] = description
        
        return result
    
    def _validate_currency(self, currency_value, row_number):
        """Validate currency code."""
        result = {'value': 'USD', 'warning': None}
        
        if not currency_value:
            return result  # Default to USD
        
        currency = str(currency_value).strip().upper()
        
        # Supported currencies
        supported_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
        
        if currency in supported_currencies:
            result['value'] = currency
        else:
            result['warning'] = {
                'field': 'currency',
                'code': 'UNSUPPORTED_CURRENCY',
                'message': f'Unsupported currency: {currency}, defaulting to USD',
                'value': currency_value
            }
        
        return result


class DuplicateDetectionService:
    """Detect duplicate transactions during import."""
    
    def __init__(self):
        self.similarity_threshold = 0.85
    
    def check_for_duplicate(self, imported_transaction, user):
        """Check if imported transaction is a duplicate."""
        
        # Get existing transactions for comparison
        existing_transactions = Transaction.objects.filter(
            account__created_by=user,
            date__range=[
                imported_transaction.date - timezone.timedelta(days=3),
                imported_transaction.date + timezone.timedelta(days=3)
            ]
        )
        
        best_match = None
        highest_similarity = 0
        
        for existing in existing_transactions:
            similarity = self._calculate_similarity(imported_transaction, existing)
            
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = existing
        
        is_duplicate = highest_similarity >= self.similarity_threshold
        
        return {
            'is_duplicate': is_duplicate,
            'confidence': highest_similarity,
            'existing_transaction': best_match if is_duplicate else None
        }
    
    def _calculate_similarity(self, imported_transaction, existing_transaction):
        """Calculate similarity between transactions."""
        
        # Date similarity (exact match = 1.0, 1 day off = 0.8, etc.)
        date_diff = abs((imported_transaction.date - existing_transaction.date).days)
        date_similarity = max(0, 1.0 - (date_diff * 0.2))
        
        # Amount similarity (exact match = 1.0)
        amount_diff = abs(imported_transaction.amount - existing_transaction.amount)
        amount_similarity = 1.0 if amount_diff == 0 else max(0, 1.0 - float(amount_diff) / float(abs(imported_transaction.amount)))
        
        # Description similarity (using simple text similarity)
        desc_similarity = self._text_similarity(
            imported_transaction.description,
            existing_transaction.description
        )
        
        # Weighted average
        total_similarity = (
            date_similarity * 0.3 +      # 30% weight on date
            amount_similarity * 0.5 +    # 50% weight on amount
            desc_similarity * 0.2        # 20% weight on description
        )
        
        return total_similarity
    
    def _text_similarity(self, text1, text2):
        """Calculate text similarity using simple algorithm."""
        if not text1 or not text2:
            return 0.0
        
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)