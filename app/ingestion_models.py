"""
Financial data ingestion models for managing data sources and import jobs.
Supports CSV files, HTTPS endpoints, and API integrations.

Created: 2025-01-03
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import URLValidator
from django.utils import timezone

from app.django_models import BaseModel, User


class DataSourceType(models.TextChoices):
    """Types of data sources supported."""
    CSV_UPLOAD = 'csv_upload', 'CSV File Upload'
    CSV_URL = 'csv_url', 'CSV from URL'
    HTTPS_ENDPOINT = 'https_endpoint', 'HTTPS Endpoint'
    API_ENDPOINT = 'api_endpoint', 'API Endpoint'
    FTP = 'ftp', 'FTP Server'
    SFTP = 'sftp', 'SFTP Server'


class AuthenticationType(models.TextChoices):
    """Authentication methods for data sources."""
    NONE = 'none', 'No Authentication'
    BASIC = 'basic', 'Basic Authentication'
    BEARER = 'bearer', 'Bearer Token'
    API_KEY = 'api_key', 'API Key'
    OAUTH2 = 'oauth2', 'OAuth 2.0'
    CUSTOM_HEADER = 'custom_header', 'Custom Header'


class DataFormat(models.TextChoices):
    """Supported data formats."""
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'
    XML = 'xml', 'XML'
    XLSX = 'xlsx', 'Excel (XLSX)'
    OFX = 'ofx', 'Open Financial Exchange'
    QIF = 'qif', 'Quicken Interchange Format'


class IngestionStatus(models.TextChoices):
    """Status of ingestion jobs."""
    PENDING = 'pending', 'Pending'
    VALIDATING = 'validating', 'Validating'
    PROCESSING = 'processing', 'Processing'
    COMPLETED = 'completed', 'Completed'
    FAILED = 'failed', 'Failed'
    PARTIAL = 'partial', 'Partially Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class ScheduleFrequency(models.TextChoices):
    """Frequency options for scheduled ingestion."""
    MANUAL = 'manual', 'Manual Only'
    HOURLY = 'hourly', 'Every Hour'
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    MONTHLY = 'monthly', 'Monthly'
    CUSTOM = 'custom', 'Custom Schedule'


class DataSource(BaseModel):
    """
    Represents a configured data source for financial data ingestion.
    """
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Descriptive name for the data source")
    description = models.TextField(blank=True, help_text="Detailed description of the data source")
    source_type = models.CharField(
        max_length=50, 
        choices=DataSourceType.choices,
        help_text="Type of data source"
    )
    
    # Connection Details
    source_url = models.URLField(
        max_length=500, 
        blank=True,
        validators=[URLValidator()],
        help_text="URL for HTTPS/API endpoints"
    )
    
    # Authentication
    auth_type = models.CharField(
        max_length=50,
        choices=AuthenticationType.choices,
        default=AuthenticationType.NONE,
        help_text="Authentication method"
    )
    auth_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Authentication configuration (encrypted in production)"
    )
    
    # Data Format Configuration
    data_format = models.CharField(
        max_length=20,
        choices=DataFormat.choices,
        default=DataFormat.CSV,
        help_text="Format of the data"
    )
    
    # Field Mapping Configuration
    field_mapping = models.JSONField(
        default=dict,
        help_text="Maps source fields to system fields"
    )
    
    # Transform Configuration
    transform_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data transformation rules"
    )
    
    # Validation Rules
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom validation rules for imported data"
    )
    
    # Default Values
    default_account_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Default account for imported transactions"
    )
    default_tags = ArrayField(
        models.CharField(max_length=100),
        default=list,
        blank=True,
        help_text="Default tags to apply to imported data"
    )
    
    # Scheduling
    schedule_enabled = models.BooleanField(
        default=False,
        help_text="Enable automatic scheduled ingestion"
    )
    schedule_frequency = models.CharField(
        max_length=20,
        choices=ScheduleFrequency.choices,
        default=ScheduleFrequency.MANUAL
    )
    schedule_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Scheduling configuration (cron expression, time, etc.)"
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful synchronization"
    )
    next_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Next scheduled synchronization"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this data source is active"
    )
    
    # Tenant fields
    tenant_type = models.CharField(max_length=50, default='user')
    tenant_id = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'data_sources'
        indexes = [
            models.Index(fields=['tenant_type', 'tenant_id']),
            models.Index(fields=['source_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['next_sync']),
        ]
        unique_together = [['name', 'tenant_type', 'tenant_id']]
    
    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class IngestionJob(BaseModel):
    """
    Represents a single data ingestion job execution.
    """
    
    # Link to data source
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='ingestion_jobs'
    )
    
    # Job Information
    job_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique job identifier"
    )
    status = models.CharField(
        max_length=20,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING
    )
    
    # Execution Details
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the job started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the job completed"
    )
    
    # File Information (for uploads)
    file_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename for uploads"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Storage path for uploaded files"
    )
    
    # Processing Statistics
    total_records = models.IntegerField(
        default=0,
        help_text="Total records in the source"
    )
    processed_records = models.IntegerField(
        default=0,
        help_text="Records successfully processed"
    )
    failed_records = models.IntegerField(
        default=0,
        help_text="Records that failed processing"
    )
    skipped_records = models.IntegerField(
        default=0,
        help_text="Records skipped (duplicates, etc.)"
    )
    
    # Import Summary
    transactions_created = models.IntegerField(
        default=0,
        help_text="New transactions created"
    )
    transactions_updated = models.IntegerField(
        default=0,
        help_text="Existing transactions updated"
    )
    
    # Error Tracking
    error_summary = models.JSONField(
        default=dict,
        blank=True,
        help_text="Summary of errors by type"
    )
    error_details = models.JSONField(
        default=list,
        blank=True,
        help_text="Detailed error information"
    )
    
    # Processing Log
    processing_log = models.TextField(
        blank=True,
        help_text="Detailed processing log"
    )
    
    # Tenant fields
    tenant_type = models.CharField(max_length=50, default='user')
    tenant_id = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'ingestion_jobs'
        indexes = [
            models.Index(fields=['job_id']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['tenant_type', 'tenant_id']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job {self.job_id} - {self.data_source.name}"
    
    @property
    def duration(self) -> Optional[int]:
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_records > 0:
            return (self.processed_records / self.total_records) * 100
        return 0.0


class FieldMapping(BaseModel):
    """
    Defines field mappings for a data source.
    """
    
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='field_mappings'
    )
    
    # Source Field
    source_field = models.CharField(
        max_length=255,
        help_text="Field name in the source data"
    )
    source_field_type = models.CharField(
        max_length=50,
        help_text="Data type in source"
    )
    
    # Target Field
    target_field = models.CharField(
        max_length=255,
        help_text="Field name in the system"
    )
    target_model = models.CharField(
        max_length=50,
        default='Transaction',
        help_text="Target model (Transaction, Account, etc.)"
    )
    
    # Transformation
    transform_function = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transformation function to apply"
    )
    transform_params = models.JSONField(
        default=dict,
        blank=True,
        help_text="Parameters for transformation"
    )
    
    # Validation
    is_required = models.BooleanField(
        default=False,
        help_text="Whether this field is required"
    )
    validation_regex = models.CharField(
        max_length=500,
        blank=True,
        help_text="Regex pattern for validation"
    )
    
    # Defaults
    default_value = models.CharField(
        max_length=500,
        blank=True,
        help_text="Default value if source field is empty"
    )
    
    class Meta:
        db_table = 'field_mappings'
        unique_together = [['data_source', 'source_field']]
    
    def __str__(self):
        return f"{self.source_field} -> {self.target_field}"


class IngestionSchedule(BaseModel):
    """
    Manages scheduled ingestion jobs.
    """
    
    data_source = models.OneToOneField(
        DataSource,
        on_delete=models.CASCADE,
        related_name='schedule'
    )
    
    # Schedule Configuration
    is_active = models.BooleanField(default=True)
    cron_expression = models.CharField(
        max_length=100,
        blank=True,
        help_text="Cron expression for custom schedules"
    )
    
    # Time Windows
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Daily start time for ingestion window"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Daily end time for ingestion window"
    )
    
    # Days of Week (for weekly schedules)
    days_of_week = ArrayField(
        models.IntegerField(),
        default=list,
        blank=True,
        help_text="Days of week (0=Monday, 6=Sunday)"
    )
    
    # Day of Month (for monthly schedules)
    day_of_month = models.IntegerField(
        null=True,
        blank=True,
        help_text="Day of month (1-31)"
    )
    
    # Retry Configuration
    retry_on_failure = models.BooleanField(
        default=True,
        help_text="Retry failed ingestions"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum retry attempts"
    )
    retry_delay_minutes = models.IntegerField(
        default=30,
        help_text="Delay between retries"
    )
    
    # Notifications
    notify_on_success = models.BooleanField(default=False)
    notify_on_failure = models.BooleanField(default=True)
    notification_emails = ArrayField(
        models.EmailField(),
        default=list,
        blank=True
    )
    
    class Meta:
        db_table = 'ingestion_schedules'
    
    def __str__(self):
        return f"Schedule for {self.data_source.name}"