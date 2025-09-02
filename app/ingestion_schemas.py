"""
Pydantic schemas for data ingestion feature.
"""

from datetime import datetime, time
from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator, HttpUrl
from decimal import Decimal


# Enums matching the model choices
class DataSourceTypeEnum(str, Enum):
    CSV_UPLOAD = 'csv_upload'
    CSV_URL = 'csv_url'
    HTTPS_ENDPOINT = 'https_endpoint'
    API_ENDPOINT = 'api_endpoint'
    FTP = 'ftp'
    SFTP = 'sftp'


class AuthenticationTypeEnum(str, Enum):
    NONE = 'none'
    BASIC = 'basic'
    BEARER = 'bearer'
    API_KEY = 'api_key'
    OAUTH2 = 'oauth2'
    CUSTOM_HEADER = 'custom_header'


class DataFormatEnum(str, Enum):
    CSV = 'csv'
    JSON = 'json'
    XML = 'xml'
    XLSX = 'xlsx'
    OFX = 'ofx'
    QIF = 'qif'


class IngestionStatusEnum(str, Enum):
    PENDING = 'pending'
    VALIDATING = 'validating'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PARTIAL = 'partial'
    CANCELLED = 'cancelled'


class ScheduleFrequencyEnum(str, Enum):
    MANUAL = 'manual'
    HOURLY = 'hourly'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    CUSTOM = 'custom'


# Field Mapping Schemas
class FieldMappingCreate(BaseModel):
    """Schema for creating field mappings."""
    source_field: str = Field(..., description="Field name in source data")
    source_field_type: str = Field(..., description="Data type in source")
    target_field: str = Field(..., description="Field name in system")
    target_model: str = Field(default='Transaction', description="Target model")
    transform_function: Optional[str] = Field(None, description="Transformation function")
    transform_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_required: bool = Field(default=False, description="Is field required")
    validation_regex: Optional[str] = Field(None, description="Validation pattern")
    default_value: Optional[str] = Field(None, description="Default if empty")


class FieldMappingRead(FieldMappingCreate):
    """Schema for reading field mappings."""
    id: UUID
    created_at: datetime
    updated_at: datetime


# Data Source Schemas
class DataSourceBase(BaseModel):
    """Base schema for data sources."""
    name: str = Field(..., max_length=255, description="Data source name")
    description: Optional[str] = Field(None, description="Description")
    source_type: DataSourceTypeEnum = Field(..., description="Type of data source")
    source_url: Optional[HttpUrl] = Field(None, description="URL for HTTPS/API endpoints")
    auth_type: AuthenticationTypeEnum = Field(default=AuthenticationTypeEnum.NONE)
    data_format: DataFormatEnum = Field(default=DataFormatEnum.CSV)
    default_account_id: Optional[UUID] = Field(None, description="Default account")
    default_tags: List[str] = Field(default_factory=list, description="Default tags")
    schedule_enabled: bool = Field(default=False)
    schedule_frequency: ScheduleFrequencyEnum = Field(default=ScheduleFrequencyEnum.MANUAL)
    is_active: bool = Field(default=True)


class DataSourceCreate(DataSourceBase):
    """Schema for creating a data source."""
    auth_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Authentication configuration"
    )
    field_mapping: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Field mappings"
    )
    transform_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Transformation rules"
    )
    validation_rules: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Validation rules"
    )
    schedule_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Schedule configuration"
    )
    
    @validator('source_url')
    def validate_source_url(cls, v, values):
        """Validate URL is required for certain source types."""
        if values.get('source_type') in ['csv_url', 'https_endpoint', 'api_endpoint'] and not v:
            raise ValueError('Source URL is required for this source type')
        return v


class DataSourceRead(DataSourceBase):
    """Schema for reading data sources."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    field_mappings: List[FieldMappingRead] = Field(default_factory=list)


class DataSourceUpdate(BaseModel):
    """Schema for updating data sources."""
    name: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    auth_type: Optional[AuthenticationTypeEnum] = None
    auth_config: Optional[Dict[str, Any]] = None
    data_format: Optional[DataFormatEnum] = None
    field_mapping: Optional[Dict[str, str]] = None
    transform_config: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_account_id: Optional[UUID] = None
    default_tags: Optional[List[str]] = None
    schedule_enabled: Optional[bool] = None
    schedule_frequency: Optional[ScheduleFrequencyEnum] = None
    schedule_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


# Ingestion Job Schemas
class IngestionJobCreate(BaseModel):
    """Schema for creating an ingestion job."""
    data_source_id: UUID = Field(..., description="Data source ID")
    file_name: Optional[str] = Field(None, description="Filename for uploads")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class IngestionJobRead(BaseModel):
    """Schema for reading ingestion jobs."""
    id: UUID
    job_id: UUID
    data_source_id: UUID
    data_source_name: str
    status: IngestionStatusEnum
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    transactions_created: int = 0
    transactions_updated: int = 0
    error_summary: Dict[str, Any] = Field(default_factory=dict)
    duration: Optional[float] = None
    success_rate: float = 0.0


class IngestionJobUpdate(BaseModel):
    """Schema for updating ingestion job status."""
    status: Optional[IngestionStatusEnum] = None
    total_records: Optional[int] = None
    processed_records: Optional[int] = None
    failed_records: Optional[int] = None
    skipped_records: Optional[int] = None
    error_summary: Optional[Dict[str, Any]] = None


# File Upload Schema
class FileUploadRequest(BaseModel):
    """Schema for file upload requests."""
    data_source_id: UUID = Field(..., description="Data source to use")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")


# Preview Schemas
class DataPreviewRequest(BaseModel):
    """Request to preview data from a source."""
    source_type: DataSourceTypeEnum
    source_url: Optional[HttpUrl] = None
    auth_type: Optional[AuthenticationTypeEnum] = AuthenticationTypeEnum.NONE
    auth_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    data_format: DataFormatEnum = DataFormatEnum.CSV
    preview_rows: int = Field(default=10, ge=1, le=100)


class DataPreviewResponse(BaseModel):
    """Response with data preview."""
    columns: List[str] = Field(..., description="Column names detected")
    data_types: Dict[str, str] = Field(..., description="Detected data types")
    sample_data: List[Dict[str, Any]] = Field(..., description="Sample rows")
    total_rows: Optional[int] = Field(None, description="Total rows if available")
    suggested_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Suggested field mappings"
    )


# Validation Schemas
class ValidationRuleCreate(BaseModel):
    """Schema for creating validation rules."""
    field_name: str = Field(..., description="Field to validate")
    rule_type: str = Field(..., description="Type of validation")
    rule_config: Dict[str, Any] = Field(..., description="Rule configuration")
    error_message: str = Field(..., description="Error message on failure")


class ValidationResult(BaseModel):
    """Result of data validation."""
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)


# Schedule Schemas
class ScheduleConfigCreate(BaseModel):
    """Schema for creating schedule configuration."""
    frequency: ScheduleFrequencyEnum
    cron_expression: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: Optional[List[int]] = Field(None, description="0=Monday, 6=Sunday")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    retry_on_failure: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_minutes: int = Field(default=30, ge=1)
    notify_on_success: bool = False
    notify_on_failure: bool = True
    notification_emails: List[str] = Field(default_factory=list)


# Import Configuration Schema
class ImportConfigRequest(BaseModel):
    """Configuration for import process."""
    data_source_id: UUID
    skip_duplicates: bool = True
    update_existing: bool = False
    dry_run: bool = False
    batch_size: int = Field(default=100, ge=1, le=1000)
    apply_default_tags: bool = True
    auto_categorize: bool = True
    date_format: Optional[str] = Field(None, description="Custom date format")
    decimal_separator: str = Field(default=".", description="Decimal separator")
    thousands_separator: str = Field(default=",", description="Thousands separator")


# Import Result Schema
class ImportResult(BaseModel):
    """Result of import operation."""
    job_id: UUID
    status: IngestionStatusEnum
    total_records: int
    processed_records: int
    created_records: int
    updated_records: int
    skipped_records: int
    failed_records: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time: float
    dry_run: bool = False