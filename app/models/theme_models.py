"""
Theme models for user customization preferences.
Implements secure storage for user theme configurations.

Created by: Team Alpha (Atlas & Athena)
Date: 2025-01-02
"""

import uuid
import json
from typing import Dict, Any, Optional

from django.db import models
from django.core.validators import ValidationError
from django.contrib.postgres.fields import JSONField
from django.utils import timezone
from django.db import transaction

from ..django_models import BaseModel, User
from ..managers import TenantAwareManager


class ThemeManager(TenantAwareManager):
    """Custom manager for theme-related operations."""
    
    def get_active_theme_for_user(self, user: User) -> Optional['UserThemePreference']:
        """Get the currently active theme for a user."""
        return self.filter(user=user, is_active=True).first()
    
    def get_public_templates(self) -> models.QuerySet:
        """Get all public theme templates."""
        return self.model.objects.filter(is_public=True).order_by('-usage_count', 'name')


class ThemeCategory(models.TextChoices):
    """Theme category choices."""
    LIGHT = 'light', 'Light'
    DARK = 'dark', 'Dark'
    HIGH_CONTRAST = 'high_contrast', 'High Contrast'
    COLORFUL = 'colorful', 'Colorful'
    MINIMAL = 'minimal', 'Minimal'
    CUSTOM = 'custom', 'Custom'


class UserThemePreference(BaseModel):
    """
    Model to store user theme preferences.
    Each user can have multiple themes but only one active at a time.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='theme_preferences'
    )
    name = models.CharField(
        max_length=100,
        help_text="User-friendly name for the theme"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the theme"
    )
    category = models.CharField(
        max_length=20,
        choices=ThemeCategory.choices,
        default=ThemeCategory.CUSTOM
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Whether this theme is currently active for the user"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the user's default theme"
    )
    theme_data = JSONField(
        default=dict,
        help_text="JSON structure containing theme configuration"
    )
    
    # Metadata
    version = models.CharField(
        max_length=10,
        default='1.0',
        help_text="Theme version for compatibility"
    )
    last_modified = models.DateTimeField(auto_now=True)
    
    objects = ThemeManager()
    
    class Meta:
        db_table = 'user_theme_preferences'
        ordering = ['-is_active', '-is_default', '-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['user', 'name']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_theme_name_per_user'
            ),
            models.UniqueConstraint(
                fields=['user', 'is_active'],
                condition=models.Q(is_active=True),
                name='one_active_theme_per_user'
            ),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def activate(self):
        """Activate this theme for the user."""
        with transaction.atomic():
            # Deactivate all other themes for this user
            UserThemePreference.objects.filter(
                user=self.user,
                is_active=True
            ).exclude(id=self.id).update(is_active=False)
            
            # Activate this theme
            self.is_active = True
            self.save(update_fields=['is_active', 'updated_at'])
    
    def validate_theme_data(self):
        """Validate the theme data structure."""
        required_keys = ['colors', 'typography', 'spacing', 'borders']
        
        if not isinstance(self.theme_data, dict):
            raise ValidationError("Theme data must be a dictionary")
        
        for key in required_keys:
            if key not in self.theme_data:
                raise ValidationError(f"Theme data must contain '{key}' section")
        
        # Validate color format
        if 'colors' in self.theme_data:
            for color_key, color_value in self.theme_data['colors'].items():
                if not isinstance(color_value, str) or not color_value.startswith('#'):
                    raise ValidationError(f"Invalid color format for {color_key}: {color_value}")
    
    def clean(self):
        """Validate model before saving."""
        super().clean()
        self.validate_theme_data()
    
    def save(self, *args, **kwargs):
        """Override save to ensure data validation."""
        self.full_clean()
        super().save(*args, **kwargs)


class ThemeTemplate(BaseModel):
    """
    Pre-defined theme templates that users can use as starting points.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Template name"
    )
    description = models.TextField(
        help_text="Description of the theme template"
    )
    category = models.CharField(
        max_length=20,
        choices=ThemeCategory.choices,
        default=ThemeCategory.LIGHT
    )
    theme_data = JSONField(
        default=dict,
        help_text="JSON structure containing theme configuration"
    )
    preview_image = models.URLField(
        blank=True,
        null=True,
        help_text="URL to theme preview image"
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Whether this template is available to all users"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether to feature this template"
    )
    usage_count = models.IntegerField(
        default=0,
        help_text="Number of times this template has been used"
    )
    
    # Metadata
    version = models.CharField(
        max_length=10,
        default='1.0'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated tags for searching"
    )
    
    objects = ThemeManager()
    
    class Meta:
        db_table = 'theme_templates'
        ordering = ['-is_featured', '-usage_count', 'name']
        indexes = [
            models.Index(fields=['category', 'is_public']),
            models.Index(fields=['is_featured', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    def increment_usage(self):
        """Increment the usage counter."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def create_user_preference(self, user: User, name: Optional[str] = None) -> UserThemePreference:
        """Create a user theme preference from this template."""
        theme_name = name or f"{self.name} (Copy)"
        
        preference = UserThemePreference.objects.create(
            user=user,
            name=theme_name,
            description=f"Based on {self.name} template",
            category=self.category,
            theme_data=self.theme_data.copy(),
            version=self.version
        )
        
        self.increment_usage()
        return preference


class ThemeAuditLog(BaseModel):
    """
    Audit log for theme-related actions.
    Tracks all theme modifications for security and debugging.
    """
    
    ACTION_CHOICES = [
        ('created', 'Theme Created'),
        ('updated', 'Theme Updated'),
        ('activated', 'Theme Activated'),
        ('deactivated', 'Theme Deactivated'),
        ('deleted', 'Theme Deleted'),
        ('imported', 'Theme Imported'),
        ('exported', 'Theme Exported'),
        ('shared', 'Theme Shared'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='theme_audit_logs'
    )
    theme = models.ForeignKey(
        UserThemePreference,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    details = JSONField(
        default=dict,
        help_text="Additional details about the action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        blank=True
    )
    
    class Meta:
        db_table = 'theme_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.created_at}"


# Default theme configuration
DEFAULT_THEME_DATA = {
    "name": "Financial Stronghold Default",
    "version": "1.0",
    "category": "light",
    "colors": {
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#0dcaf0",
        "light": "#f8f9fa",
        "dark": "#212529",
        "background": "#ffffff",
        "surface": "#f5f5f5",
        "text-primary": "#212529",
        "text-secondary": "#6c757d",
        "border": "#dee2e6",
        "shadow": "rgba(0, 0, 0, 0.1)"
    },
    "typography": {
        "font-family-base": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font-family-monospace": "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
        "font-size-base": "1rem",
        "font-size-sm": "0.875rem",
        "font-size-lg": "1.125rem",
        "font-weight-light": "300",
        "font-weight-normal": "400",
        "font-weight-bold": "700",
        "line-height-base": "1.5",
        "headings-font-family": "inherit",
        "headings-font-weight": "500",
        "headings-line-height": "1.2"
    },
    "spacing": {
        "spacer": "1rem",
        "spacers": {
            "0": "0",
            "1": "0.25rem",
            "2": "0.5rem",
            "3": "1rem",
            "4": "1.5rem",
            "5": "3rem"
        },
        "container-padding": "1.5rem",
        "grid-gutter": "1.5rem"
    },
    "borders": {
        "width": "1px",
        "style": "solid",
        "radius": "0.375rem",
        "radius-sm": "0.25rem",
        "radius-lg": "0.5rem",
        "radius-pill": "50rem"
    },
    "shadows": {
        "sm": "0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)",
        "default": "0 0.5rem 1rem rgba(0, 0, 0, 0.15)",
        "lg": "0 1rem 3rem rgba(0, 0, 0, 0.175)",
        "inset": "inset 0 1px 2px rgba(0, 0, 0, 0.075)"
    },
    "components": {
        "card": {
            "bg": "#ffffff",
            "border-width": "1px",
            "border-color": "rgba(0, 0, 0, 0.125)",
            "border-radius": "0.375rem",
            "box-shadow": "0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)",
            "header-bg": "rgba(0, 0, 0, 0.03)",
            "header-border-color": "rgba(0, 0, 0, 0.125)"
        },
        "button": {
            "border-radius": "0.375rem",
            "border-width": "1px",
            "padding-x": "0.75rem",
            "padding-y": "0.375rem",
            "font-weight": "400",
            "box-shadow": "inset 0 1px 0 rgba(255, 255, 255, 0.15), 0 1px 1px rgba(0, 0, 0, 0.075)",
            "disabled-opacity": "0.65",
            "transition": "color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out"
        },
        "input": {
            "bg": "#ffffff",
            "border-color": "#ced4da",
            "border-radius": "0.375rem",
            "border-width": "1px",
            "color": "#212529",
            "padding-x": "0.75rem",
            "padding-y": "0.375rem",
            "font-size": "1rem",
            "line-height": "1.5",
            "focus-border-color": "#86b7fe",
            "focus-box-shadow": "0 0 0 0.25rem rgba(13, 110, 253, 0.25)"
        },
        "navbar": {
            "bg": "#f8f9fa",
            "border-color": "#dee2e6",
            "height": "56px",
            "padding-x": "1rem",
            "padding-y": "0.5rem"
        },
        "sidebar": {
            "bg": "#f8f9fa",
            "width": "250px",
            "border-color": "#dee2e6",
            "item-padding-x": "1rem",
            "item-padding-y": "0.5rem",
            "item-hover-bg": "rgba(0, 0, 0, 0.05)",
            "item-active-bg": "#e9ecef",
            "item-active-color": "#0d6efd"
        }
    },
    "transitions": {
        "base": "all 0.2s ease-in-out",
        "fade": "opacity 0.15s linear",
        "collapse": "height 0.35s ease"
    },
    "z-index": {
        "dropdown": "1000",
        "sticky": "1020",
        "fixed": "1030",
        "modal-backdrop": "1040",
        "modal": "1050",
        "popover": "1060",
        "tooltip": "1070"
    }
}