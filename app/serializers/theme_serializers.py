"""
Serializers for theme-related models.
Handles data validation and transformation for API.

Created by: Team Beta (Blake & Bella)
Date: 2025-01-02
"""

import json
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from ..models.theme_models import (
    UserThemePreference,
    ThemeTemplate,
    ThemeAuditLog,
    ThemeCategory
)
from ..services.theme_service import ThemeValidationError


class ThemeDataField(serializers.JSONField):
    """Custom field for theme data validation."""
    
    def to_internal_value(self, data):
        """Validate theme data structure."""
        value = super().to_internal_value(data)
        
        # Ensure it's a dictionary
        if not isinstance(value, dict):
            raise serializers.ValidationError("Theme data must be a dictionary")
        
        # Check required sections
        required_sections = ['colors', 'typography', 'spacing', 'borders']
        missing_sections = [s for s in required_sections if s not in value]
        if missing_sections:
            raise serializers.ValidationError(
                f"Missing required sections: {', '.join(missing_sections)}"
            )
        
        return value


class UserThemePreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserThemePreference model."""
    
    theme_data = ThemeDataField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserThemePreference
        fields = [
            'id', 'user', 'user_email', 'name', 'description', 'category',
            'is_active', 'is_default', 'theme_data', 'version',
            'created_at', 'updated_at', 'last_modified'
        ]
        read_only_fields = [
            'id', 'user', 'user_email', 'is_active', 'is_default',
            'created_at', 'updated_at', 'last_modified'
        ]


class ThemeCreateSerializer(serializers.Serializer):
    """Serializer for creating themes."""
    
    name = serializers.CharField(max_length=100, min_length=1)
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    category = serializers.ChoiceField(
        choices=ThemeCategory.choices,
        default=ThemeCategory.CUSTOM,
        required=False
    )
    theme_data = ThemeDataField()
    base_template_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_name(self, value):
        """Validate theme name."""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Theme name cannot be empty")
        return value.strip()


class ThemeUpdateSerializer(serializers.Serializer):
    """Serializer for updating themes."""
    
    name = serializers.CharField(
        max_length=100,
        min_length=1,
        required=False
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    theme_data = ThemeDataField(required=False)
    
    def validate_name(self, value):
        """Validate theme name."""
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError("Theme name cannot be empty")
        return value.strip() if value else value


class ThemeImportSerializer(serializers.Serializer):
    """Serializer for importing themes."""
    
    theme_json = serializers.CharField()
    name = serializers.CharField(
        max_length=100,
        min_length=1,
        required=False
    )
    
    def validate_theme_json(self, value):
        """Validate JSON format."""
        try:
            theme_data = json.loads(value)
            if not isinstance(theme_data, dict):
                raise serializers.ValidationError("Theme JSON must be an object")
            return value
        except json.JSONDecodeError as e:
            raise serializers.ValidationError(f"Invalid JSON format: {str(e)}")


class ThemePreviewSerializer(serializers.Serializer):
    """Serializer for theme preview."""
    
    theme_data = ThemeDataField()


class CompiledThemeSerializer(serializers.Serializer):
    """Serializer for compiled theme response."""
    
    id = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    css_variables = serializers.DictField(
        child=serializers.CharField()
    )
    theme_data = serializers.DictField()
    compiled_at = serializers.CharField()


class ThemeTemplateSerializer(serializers.ModelSerializer):
    """Serializer for ThemeTemplate model."""
    
    created_by_email = serializers.EmailField(
        source='created_by.email',
        read_only=True
    )
    
    class Meta:
        model = ThemeTemplate
        fields = [
            'id', 'name', 'description', 'category', 'theme_data',
            'preview_image', 'is_public', 'is_featured', 'usage_count',
            'version', 'tags', 'created_at', 'updated_at',
            'created_by', 'created_by_email'
        ]
        read_only_fields = [
            'id', 'usage_count', 'created_at', 'updated_at',
            'created_by', 'created_by_email'
        ]


class ThemeAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for ThemeAuditLog model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    theme_name = serializers.CharField(source='theme.name', read_only=True)
    
    class Meta:
        model = ThemeAuditLog
        fields = [
            'id', 'user', 'user_email', 'theme', 'theme_name',
            'action', 'details', 'ip_address', 'user_agent',
            'created_at'
        ]
        read_only_fields = fields