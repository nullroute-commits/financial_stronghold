"""
Django REST Framework serializers for import functionality.
Handles serialization of import-related models and data.

Created by Team Sigma (Data Processing & Import) - Sprint 7
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models.import_models import (
    ImportJob, FileUpload, ImportedTransaction,
    ImportTemplate, ImportValidationError, TransactionCategory
)
from ..django_models import Account

User = get_user_model()


class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer for file upload management."""
    
    file_size_mb = serializers.SerializerMethodField()
    validation_status = serializers.CharField(source='status', read_only=True)
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'original_filename', 'file_size', 'file_size_mb',
            'file_hash', 'mime_type', 'validation_status', 'validation_results',
            'security_scan_results', 'created_at'
        ]
        read_only_fields = [
            'id', 'file_hash', 'mime_type', 'validation_results',
            'security_scan_results', 'created_at'
        ]
    
    def get_file_size_mb(self, obj):
        """Get file size in MB for display."""
        return round(obj.file_size / (1024 * 1024), 2)
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # File size validation
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size {value.size} bytes exceeds maximum {max_size} bytes"
            )
        
        # File extension validation
        allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf']
        file_ext = value.name.lower().split('.')[-1]
        if f'.{file_ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File extension .{file_ext} not allowed. Allowed: {allowed_extensions}"
            )
        
        return value


class ImportJobSerializer(serializers.ModelSerializer):
    """Serializer for import job management."""
    
    file_size_mb = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    
    class Meta:
        model = ImportJob
        fields = [
            'id', 'original_filename', 'file_type', 'file_type_display',
            'file_size', 'file_size_mb', 'status', 'status_display',
            'progress', 'total_rows', 'processed_rows', 'successful_imports',
            'failed_imports', 'duplicate_count', 'error_details',
            'created_at', 'processing_started_at', 'processing_completed_at',
            'duration_seconds', 'success_rate'
        ]
        read_only_fields = [
            'id', 'file_size', 'status', 'progress', 'total_rows',
            'processed_rows', 'successful_imports', 'failed_imports',
            'duplicate_count', 'error_details', 'created_at',
            'processing_started_at', 'processing_completed_at'
        ]
    
    def get_file_size_mb(self, obj):
        """Get file size in MB."""
        return round(obj.file_size / (1024 * 1024), 2)
    
    def get_duration_seconds(self, obj):
        """Get processing duration in seconds."""
        if obj.duration:
            return obj.duration.total_seconds()
        return None
    
    def get_success_rate(self, obj):
        """Get import success rate percentage."""
        return obj.success_rate


class ImportedTransactionSerializer(serializers.ModelSerializer):
    """Serializer for imported transaction management."""
    
    account_name = serializers.CharField(source='account.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    ml_predicted_category_name = serializers.CharField(
        source='ml_predicted_category.name', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duplicate_transaction_id = serializers.UUIDField(source='duplicate_of.id', read_only=True)
    
    class Meta:
        model = ImportedTransaction
        fields = [
            'id', 'row_number', 'account', 'account_name', 'amount', 'currency',
            'date', 'description', 'category', 'category_name',
            'ml_predicted_category', 'ml_predicted_category_name', 'ml_confidence',
            'status', 'status_display', 'raw_data', 'duplicate_of',
            'duplicate_transaction_id', 'duplicate_confidence',
            'validation_errors', 'has_warnings', 'created_at'
        ]
        read_only_fields = [
            'id', 'row_number', 'raw_data', 'ml_predicted_category',
            'ml_confidence', 'duplicate_of', 'duplicate_confidence',
            'validation_errors', 'has_warnings', 'created_at'
        ]
    
    def validate_account(self, value):
        """Validate account belongs to current user."""
        if value and value.created_by != self.context['request'].user:
            raise serializers.ValidationError("Account does not belong to current user")
        return value


class ImportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for import template management."""
    
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    
    class Meta:
        model = ImportTemplate
        fields = [
            'id', 'name', 'description', 'file_type', 'file_type_display',
            'column_mappings', 'data_transformations', 'validation_rules',
            'is_default', 'is_public', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate template name uniqueness for user."""
        user = self.context['request'].user
        
        # Check for existing template with same name
        existing = ImportTemplate.objects.filter(
            user=user,
            name=value
        ).exclude(id=self.instance.id if self.instance else None)
        
        if existing.exists():
            raise serializers.ValidationError("Template with this name already exists")
        
        return value
    
    def validate_column_mappings(self, value):
        """Validate column mappings structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Column mappings must be a dictionary")
        
        # Required transaction fields
        required_fields = ['date', 'amount', 'description']
        mapped_fields = set(value.values())
        
        missing_fields = set(required_fields) - mapped_fields
        if missing_fields:
            raise serializers.ValidationError(
                f"Missing required field mappings: {list(missing_fields)}"
            )
        
        return value


class ImportValidationErrorSerializer(serializers.ModelSerializer):
    """Serializer for import validation errors."""
    
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = ImportValidationError
        fields = [
            'id', 'row_number', 'column_name', 'field_name',
            'severity', 'severity_display', 'error_code', 'error_message',
            'suggested_fix', 'raw_value', 'is_resolved', 'resolution_action',
            'resolved_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TransactionCategorySerializer(serializers.ModelSerializer):
    """Serializer for transaction categories."""
    
    parent_category_name = serializers.CharField(source='parent_category.name', read_only=True)
    subcategory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'name', 'description', 'color', 'icon', 'parent_category',
            'parent_category_name', 'keywords', 'ml_confidence_threshold',
            'is_system_category', 'is_income_category', 'is_expense_category',
            'usage_count', 'last_used', 'subcategory_count', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'last_used', 'created_at']
    
    def get_subcategory_count(self, obj):
        """Get count of subcategories."""
        return TransactionCategory.objects.filter(parent_category=obj).count()
    
    def validate_name(self, value):
        """Validate category name uniqueness."""
        user = self.context['request'].user
        
        existing = TransactionCategory.objects.filter(
            user=user,
            name=value
        ).exclude(id=self.instance.id if self.instance else None)
        
        if existing.exists():
            raise serializers.ValidationError("Category with this name already exists")
        
        return value
    
    def validate_color(self, value):
        """Validate hex color format."""
        import re
        
        if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
            raise serializers.ValidationError("Color must be a valid hex color (e.g., #FF5733)")
        
        return value


class ImportSummarySerializer(serializers.Serializer):
    """Serializer for import summary data."""
    
    total_imports = serializers.IntegerField()
    successful_imports = serializers.IntegerField()
    failed_imports = serializers.IntegerField()
    pending_imports = serializers.IntegerField()
    processing_imports = serializers.IntegerField()
    total_transactions_imported = serializers.IntegerField()
    success_rate = serializers.FloatField()
    average_processing_time = serializers.FloatField(allow_null=True)
    file_type_breakdown = serializers.ListField()
    time_period = serializers.CharField()


class ColumnMappingSerializer(serializers.Serializer):
    """Serializer for column mapping configuration."""
    
    csv_column = serializers.CharField(max_length=100)
    transaction_field = serializers.ChoiceField(choices=[
        ('date', 'Date'),
        ('amount', 'Amount'),
        ('description', 'Description'),
        ('category', 'Category'),
        ('account', 'Account'),
        ('currency', 'Currency'),
        ('reference', 'Reference'),
        ('ignore', 'Ignore')
    ])
    data_type = serializers.ChoiceField(choices=[
        ('date', 'Date'),
        ('decimal', 'Decimal Number'),
        ('text', 'Text'),
        ('currency', 'Currency Code'),
    ])
    is_required = serializers.BooleanField(default=False)
    transformation_rule = serializers.CharField(max_length=200, required=False, allow_blank=True)


class FilePreviewSerializer(serializers.Serializer):
    """Serializer for file preview data."""
    
    filename = serializers.CharField()
    file_type = serializers.CharField()
    total_rows = serializers.IntegerField()
    detected_columns = serializers.ListField()
    sample_data = serializers.ListField()
    suggested_mappings = serializers.DictField()
    data_quality_score = serializers.FloatField()
    warnings = serializers.ListField()
    errors = serializers.ListField()