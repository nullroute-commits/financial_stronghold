"""
Django models for file import and transaction analysis system.
Foundation models for the import feature implementation.

Created by Team Sigma (Data Processing & Import) - Sprint 7
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from decimal import Decimal


class ImportJob(models.Model):
    """Track file import jobs and their progress."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class FileType(models.TextChoices):
        CSV = 'CSV', 'CSV File'
        EXCEL = 'EXCEL', 'Excel File'
        PDF = 'PDF', 'PDF File'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('app.User', on_delete=models.CASCADE, related_name='import_jobs')
    
    # File information
    filename = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    file_size = models.BigIntegerField()  # Size in bytes
    file_hash = models.CharField(max_length=64, blank=True)  # SHA256 hash
    
    # Processing status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    progress = models.IntegerField(default=0)  # 0-100 percentage
    
    # Processing statistics
    total_rows = models.IntegerField(null=True, blank=True)
    processed_rows = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)
    
    # Error tracking
    error_details = models.JSONField(default=dict, blank=True)
    validation_errors = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Import configuration
    column_mappings = models.JSONField(default=dict, blank=True)
    import_settings = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.status})"
    
    @property
    def duration(self):
        """Calculate processing duration."""
        if self.processing_started_at and self.processing_completed_at:
            return self.processing_completed_at - self.processing_started_at
        elif self.processing_started_at:
            return timezone.now() - self.processing_started_at
        return None
    
    @property
    def success_rate(self):
        """Calculate import success rate."""
        if self.processed_rows > 0:
            return (self.successful_imports / self.processed_rows) * 100
        return 0
    
    def mark_started(self):
        """Mark import job as started."""
        self.status = self.Status.PROCESSING
        self.processing_started_at = timezone.now()
        self.save(update_fields=['status', 'processing_started_at'])
    
    def mark_completed(self):
        """Mark import job as completed."""
        self.status = self.Status.COMPLETED
        self.processing_completed_at = timezone.now()
        self.progress = 100
        self.save(update_fields=['status', 'processing_completed_at', 'progress'])
    
    def mark_failed(self, error_message):
        """Mark import job as failed."""
        self.status = self.Status.FAILED
        self.processing_completed_at = timezone.now()
        self.error_details['failure_reason'] = error_message
        self.save(update_fields=['status', 'processing_completed_at', 'error_details'])
    
    def update_progress(self, processed_rows, successful_imports, failed_imports):
        """Update import progress."""
        self.processed_rows = processed_rows
        self.successful_imports = successful_imports
        self.failed_imports = failed_imports
        
        if self.total_rows:
            self.progress = min(100, int((processed_rows / self.total_rows) * 100))
        
        self.save(update_fields=[
            'processed_rows', 'successful_imports', 'failed_imports', 'progress'
        ])


class ImportTemplate(models.Model):
    """Reusable templates for file import column mappings."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('app.User', on_delete=models.CASCADE, related_name='import_templates')
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file_type = models.CharField(max_length=10, choices=ImportJob.FileType.choices)
    
    # Template configuration
    column_mappings = models.JSONField()  # {csv_column: transaction_field}
    data_transformations = models.JSONField(default=dict)  # Field transformation rules
    validation_rules = models.JSONField(default=dict)  # Custom validation rules
    
    # Template metadata
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)  # Can be shared with other users
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-usage_count', 'name']
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'file_type']),
            models.Index(fields=['file_type', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.file_type})"
    
    def increment_usage(self):
        """Increment usage counter."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class ImportValidationError(models.Model):
    """Track validation errors during import process."""
    
    class Severity(models.TextChoices):
        ERROR = 'ERROR', 'Error'
        WARNING = 'WARNING', 'Warning'
        INFO = 'INFO', 'Info'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='validation_errors')
    
    # Error details
    row_number = models.IntegerField()
    column_name = models.CharField(max_length=100, blank=True)
    field_name = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    
    # Error information
    error_code = models.CharField(max_length=50)
    error_message = models.TextField()
    suggested_fix = models.TextField(blank=True)
    raw_value = models.TextField(blank=True)  # Original problematic value
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolution_action = models.CharField(max_length=100, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['row_number', 'severity']
        indexes = [
            models.Index(fields=['import_job', 'severity']),
            models.Index(fields=['import_job', 'row_number']),
        ]
    
    def __str__(self):
        return f"Row {self.row_number}: {self.error_message}"
    
    def resolve(self, action):
        """Mark validation error as resolved."""
        self.is_resolved = True
        self.resolution_action = action
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolution_action', 'resolved_at'])


class TransactionCategory(models.Model):
    """Enhanced transaction categories for ML categorization."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('app.User', on_delete=models.CASCADE, related_name='transaction_categories', null=True, blank=True)
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color for UI
    icon = models.CharField(max_length=50, blank=True)  # Bootstrap icon name
    
    # Category hierarchy
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    
    # ML categorization support
    keywords = models.JSONField(default=list)  # Keywords for auto-categorization
    ml_confidence_threshold = models.FloatField(default=0.8)
    
    # Category metadata
    is_system_category = models.BooleanField(default=False)  # Built-in categories
    is_income_category = models.BooleanField(default=False)
    is_expense_category = models.BooleanField(default=True)
    
    # Usage statistics
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']
        indexes = [
            models.Index(fields=['user', 'is_system_category']),
            models.Index(fields=['is_system_category', 'name']),
        ]
    
    def __str__(self):
        return self.name
    
    def increment_usage(self):
        """Increment usage counter and update last used."""
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class ImportedTransaction(models.Model):
    """Track imported transactions before they become actual transactions."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        DUPLICATE = 'DUPLICATE', 'Duplicate'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_job = models.ForeignKey(ImportJob, on_delete=models.CASCADE, related_name='imported_transactions')
    
    # Transaction data
    row_number = models.IntegerField()
    account = models.ForeignKey('Account', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    date = models.DateField()
    description = models.TextField()
    
    # Categorization
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    ml_predicted_category = models.ForeignKey(
        TransactionCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ml_predictions'
    )
    ml_confidence = models.FloatField(null=True, blank=True)
    
    # Import metadata
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    raw_data = models.JSONField()  # Original CSV row data
    
    # Duplicate detection
    duplicate_of = models.ForeignKey(
        'django_models.Transaction', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='import_duplicates'
    )
    duplicate_confidence = models.FloatField(null=True, blank=True)
    
    # Validation
    validation_errors = models.JSONField(default=list, blank=True)
    has_warnings = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['row_number']
        indexes = [
            models.Index(fields=['import_job', 'status']),
            models.Index(fields=['import_job', 'row_number']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Row {self.row_number}: {self.description[:50]}"
    
    def approve_and_create_transaction(self):
        """Approve imported transaction and create actual transaction."""
        if self.status != self.Status.PENDING:
            raise ValueError("Can only approve pending transactions")
        
        if not self.account:
            raise ValueError("Account must be assigned before approval")
        
        # Create actual transaction
        from ..django_models import Transaction
        
        transaction = Transaction.objects.create(
            account=self.account,
            amount=self.amount,
            currency=self.currency,
            date=self.date,
            description=self.description,
            category=self.category.name if self.category else '',
            created_by=self.import_job.user
        )
        
        # Update status
        self.status = self.Status.APPROVED
        self.save(update_fields=['status'])
        
        # Update import job statistics
        self.import_job.successful_imports += 1
        self.import_job.save(update_fields=['successful_imports'])
        
        return transaction
    
    def reject_with_reason(self, reason):
        """Reject imported transaction with reason."""
        self.status = self.Status.REJECTED
        self.validation_errors.append({
            'type': 'REJECTION',
            'message': reason,
            'timestamp': timezone.now().isoformat()
        })
        self.save(update_fields=['status', 'validation_errors'])
        
        # Update import job statistics
        self.import_job.failed_imports += 1
        self.import_job.save(update_fields=['failed_imports'])
    
    def mark_as_duplicate(self, existing_transaction, confidence=1.0):
        """Mark as duplicate of existing transaction."""
        self.status = self.Status.DUPLICATE
        self.duplicate_of = existing_transaction
        self.duplicate_confidence = confidence
        self.save(update_fields=['status', 'duplicate_of', 'duplicate_confidence'])
        
        # Update import job statistics
        self.import_job.duplicate_count += 1
        self.import_job.save(update_fields=['duplicate_count'])


class FileUpload(models.Model):
    """Track uploaded files before processing."""
    
    class Status(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        VALIDATED = 'VALIDATED', 'Validated'
        REJECTED = 'REJECTED', 'Rejected'
        PROCESSED = 'PROCESSED', 'Processed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('app.User', on_delete=models.CASCADE, related_name='file_uploads')
    
    # File information
    file = models.FileField(
        upload_to='imports/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xlsx', 'xls', 'pdf'])]
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_hash = models.CharField(max_length=64)  # SHA256 hash
    mime_type = models.CharField(max_length=100)
    
    # Validation results
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPLOADED)
    validation_results = models.JSONField(default=dict, blank=True)
    security_scan_results = models.JSONField(default=dict, blank=True)
    
    # Processing reference
    import_job = models.OneToOneField(
        ImportJob, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='file_upload'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.status})"
    
    def validate_file_security(self):
        """Validate file security and safety."""
        import hashlib
        import magic
        
        # Calculate file hash
        self.file.seek(0)
        file_content = self.file.read()
        self.file_hash = hashlib.sha256(file_content).hexdigest()
        self.file.seek(0)
        
        # Validate MIME type
        self.mime_type = magic.from_buffer(file_content[:1024], mime=True)
        
        # Security validation results
        validation_results = {
            'file_size_ok': self.file_size <= 50 * 1024 * 1024,  # 50MB limit
            'mime_type_allowed': self.mime_type in [
                'text/csv', 'application/csv',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/pdf'
            ],
            'file_hash': self.file_hash,
            'scan_timestamp': timezone.now().isoformat()
        }
        
        # Basic malware check (placeholder - implement with ClamAV in production)
        validation_results['malware_scan'] = 'CLEAN'  # Would be actual scan result
        
        self.validation_results = validation_results
        
        # Determine status
        if all([
            validation_results['file_size_ok'],
            validation_results['mime_type_allowed'],
            validation_results['malware_scan'] == 'CLEAN'
        ]):
            self.status = self.Status.VALIDATED
        else:
            self.status = self.Status.REJECTED
        
        self.save(update_fields=['file_hash', 'mime_type', 'validation_results', 'status'])
        
        return self.status == self.Status.VALIDATED


class MLModel(models.Model):
    """Track ML models for transaction categorization."""
    
    class ModelType(models.TextChoices):
        CATEGORIZATION = 'CATEGORIZATION', 'Transaction Categorization'
        PATTERN_ANALYSIS = 'PATTERN_ANALYSIS', 'Pattern Analysis'
        ANOMALY_DETECTION = 'ANOMALY_DETECTION', 'Anomaly Detection'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=ModelType.choices)
    version = models.CharField(max_length=20)
    
    # Model metadata
    accuracy_score = models.FloatField(null=True, blank=True)
    training_data_size = models.IntegerField(default=0)
    features_used = models.JSONField(default=list)
    hyperparameters = models.JSONField(default=dict)
    
    # Model file storage
    model_file_path = models.CharField(max_length=500, blank=True)
    model_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Status and usage
    is_active = models.BooleanField(default=False)
    is_production_ready = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    # Performance metrics
    performance_metrics = models.JSONField(default=dict)
    last_training_date = models.DateTimeField(null=True, blank=True)
    last_evaluation_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'version']
        indexes = [
            models.Index(fields=['model_type', 'is_active']),
            models.Index(fields=['is_active', 'accuracy_score']),
        ]
    
    def __str__(self):
        return f"{self.name} v{self.version} ({self.model_type})"
    
    def activate(self):
        """Activate this model version."""
        # Deactivate other models of the same type
        MLModel.objects.filter(
            model_type=self.model_type,
            is_active=True
        ).update(is_active=False)
        
        # Activate this model
        self.is_active = True
        self.save(update_fields=['is_active'])
    
    def record_usage(self):
        """Record model usage."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def update_performance_metrics(self, metrics):
        """Update model performance metrics."""
        self.performance_metrics.update(metrics)
        self.last_evaluation_date = timezone.now()
        self.save(update_fields=['performance_metrics', 'last_evaluation_date'])