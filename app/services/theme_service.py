"""
Theme service layer for business logic.
Handles theme management, validation, and application.

Created by: Team Beta (Blake & Bella)
Date: 2025-01-02
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

from ..models.theme_models import (
    UserThemePreference,
    ThemeTemplate,
    ThemeAuditLog,
    ThemeCategory,
    DEFAULT_THEME_DATA
)
from ..django_models import User

logger = logging.getLogger(__name__)


class ThemeValidationError(ValidationError):
    """Custom exception for theme validation errors."""
    pass


class ThemeService:
    """
    Service layer for theme management.
    Handles all business logic related to themes.
    """
    
    # CSS validation patterns
    COLOR_PATTERN = re.compile(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^rgba?\([\d\s,\.]+\)$|^hsla?\([\d\s,%\.]+\)$')
    FONT_FAMILY_PATTERN = re.compile(r'^[\w\s,\'\"-]+$')
    SIZE_PATTERN = re.compile(r'^\d+(\.\d+)?(px|rem|em|%|vh|vw)$')
    NUMERIC_PATTERN = re.compile(r'^\d+(\.\d+)?$')
    
    # Security: Maximum allowed values
    MAX_THEME_NAME_LENGTH = 100
    MAX_THEME_SIZE_KB = 100  # 100KB max theme size
    MAX_THEMES_PER_USER = 10
    
    # Cache settings
    CACHE_PREFIX = 'theme:'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    def __init__(self):
        self.logger = logger
    
    def get_active_theme(self, user: User) -> Optional[Dict[str, Any]]:
        """
        Get the active theme for a user.
        Returns compiled theme data ready for frontend use.
        """
        # Check cache first
        cache_key = f"{self.CACHE_PREFIX}active:{user.id}"
        cached_theme = cache.get(cache_key)
        if cached_theme:
            return cached_theme
        
        # Get from database
        theme_pref = UserThemePreference.objects.get_active_theme_for_user(user)
        
        if not theme_pref:
            # Return default theme
            compiled_theme = self._compile_theme(DEFAULT_THEME_DATA)
        else:
            compiled_theme = self._compile_theme(theme_pref.theme_data)
            compiled_theme['id'] = str(theme_pref.id)
            compiled_theme['name'] = theme_pref.name
        
        # Cache the result
        cache.set(cache_key, compiled_theme, self.CACHE_TIMEOUT)
        
        return compiled_theme
    
    def create_theme(self, user: User, name: str, theme_data: Dict[str, Any],
                    base_template_id: Optional[str] = None,
                    request_meta: Optional[Dict] = None) -> UserThemePreference:
        """
        Create a new theme for a user.
        """
        # Check user theme limit
        theme_count = UserThemePreference.objects.filter(user=user).count()
        if theme_count >= self.MAX_THEMES_PER_USER:
            raise ThemeValidationError(
                f"Maximum theme limit ({self.MAX_THEMES_PER_USER}) reached. "
                "Please delete some themes before creating new ones."
            )
        
        # Validate theme data
        self._validate_theme_data(theme_data)
        
        # Validate theme size
        theme_size = len(json.dumps(theme_data))
        if theme_size > self.MAX_THEME_SIZE_KB * 1024:
            raise ThemeValidationError(
                f"Theme data too large. Maximum size is {self.MAX_THEME_SIZE_KB}KB"
            )
        
        with transaction.atomic():
            # Create theme preference
            if base_template_id:
                template = ThemeTemplate.objects.get(id=base_template_id)
                theme_pref = template.create_user_preference(user, name)
                # Override with custom data
                theme_pref.theme_data.update(theme_data)
                theme_pref.save()
            else:
                theme_pref = UserThemePreference.objects.create(
                    user=user,
                    name=name,
                    theme_data=theme_data,
                    created_by=user,
                    updated_by=user
                )
            
            # Log the action
            self._log_theme_action(
                user=user,
                action='created',
                theme=theme_pref,
                request_meta=request_meta
            )
        
        return theme_pref
    
    def update_theme(self, user: User, theme_id: str, name: Optional[str] = None,
                    theme_data: Optional[Dict[str, Any]] = None,
                    request_meta: Optional[Dict] = None) -> UserThemePreference:
        """
        Update an existing theme.
        """
        theme_pref = UserThemePreference.objects.get(id=theme_id, user=user)
        
        if theme_data:
            self._validate_theme_data(theme_data)
            
            # Validate theme size
            theme_size = len(json.dumps(theme_data))
            if theme_size > self.MAX_THEME_SIZE_KB * 1024:
                raise ThemeValidationError(
                    f"Theme data too large. Maximum size is {self.MAX_THEME_SIZE_KB}KB"
                )
        
        with transaction.atomic():
            if name:
                theme_pref.name = name
            if theme_data:
                theme_pref.theme_data = theme_data
            
            theme_pref.updated_by = user
            theme_pref.save()
            
            # Clear cache if this is the active theme
            if theme_pref.is_active:
                self._clear_theme_cache(user)
            
            # Log the action
            self._log_theme_action(
                user=user,
                action='updated',
                theme=theme_pref,
                request_meta=request_meta
            )
        
        return theme_pref
    
    def activate_theme(self, user: User, theme_id: str,
                      request_meta: Optional[Dict] = None) -> UserThemePreference:
        """
        Activate a theme for a user.
        """
        theme_pref = UserThemePreference.objects.get(id=theme_id, user=user)
        
        with transaction.atomic():
            theme_pref.activate()
            
            # Clear cache
            self._clear_theme_cache(user)
            
            # Log the action
            self._log_theme_action(
                user=user,
                action='activated',
                theme=theme_pref,
                request_meta=request_meta
            )
        
        return theme_pref
    
    def delete_theme(self, user: User, theme_id: str,
                    request_meta: Optional[Dict] = None) -> None:
        """
        Delete a theme.
        """
        theme_pref = UserThemePreference.objects.get(id=theme_id, user=user)
        
        if theme_pref.is_active:
            raise ThemeValidationError("Cannot delete an active theme. Please activate another theme first.")
        
        with transaction.atomic():
            # Log before deletion
            self._log_theme_action(
                user=user,
                action='deleted',
                theme=theme_pref,
                request_meta=request_meta
            )
            
            theme_pref.delete()
    
    def import_theme(self, user: User, theme_json: str,
                    request_meta: Optional[Dict] = None) -> UserThemePreference:
        """
        Import a theme from JSON string.
        """
        try:
            theme_data = json.loads(theme_json)
        except json.JSONDecodeError as e:
            raise ThemeValidationError(f"Invalid JSON format: {str(e)}")
        
        # Extract name and data
        name = theme_data.get('name', 'Imported Theme')
        if 'theme_data' in theme_data:
            actual_theme_data = theme_data['theme_data']
        else:
            actual_theme_data = theme_data
        
        # Create the theme
        theme_pref = self.create_theme(user, name, actual_theme_data, request_meta=request_meta)
        
        # Log import action
        self._log_theme_action(
            user=user,
            action='imported',
            theme=theme_pref,
            request_meta=request_meta
        )
        
        return theme_pref
    
    def export_theme(self, user: User, theme_id: str,
                    request_meta: Optional[Dict] = None) -> str:
        """
        Export a theme to JSON string.
        """
        theme_pref = UserThemePreference.objects.get(id=theme_id, user=user)
        
        export_data = {
            'name': theme_pref.name,
            'version': theme_pref.version,
            'category': theme_pref.category,
            'exported_at': timezone.now().isoformat(),
            'theme_data': theme_pref.theme_data
        }
        
        # Log export action
        self._log_theme_action(
            user=user,
            action='exported',
            theme=theme_pref,
            request_meta=request_meta
        )
        
        return json.dumps(export_data, indent=2)
    
    def preview_theme(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a preview of theme data without saving.
        """
        self._validate_theme_data(theme_data)
        return self._compile_theme(theme_data)
    
    def get_theme_templates(self, category: Optional[str] = None) -> List[ThemeTemplate]:
        """
        Get available theme templates.
        """
        queryset = ThemeTemplate.objects.filter(is_public=True)
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-is_featured', '-usage_count', 'name')
    
    def _validate_theme_data(self, theme_data: Dict[str, Any]) -> None:
        """
        Validate theme data structure and values.
        """
        # Check required sections
        required_sections = ['colors', 'typography', 'spacing', 'borders']
        for section in required_sections:
            if section not in theme_data:
                raise ThemeValidationError(f"Missing required section: {section}")
        
        # Validate colors
        if 'colors' in theme_data:
            self._validate_colors(theme_data['colors'])
        
        # Validate typography
        if 'typography' in theme_data:
            self._validate_typography(theme_data['typography'])
        
        # Validate spacing
        if 'spacing' in theme_data:
            self._validate_spacing(theme_data['spacing'])
        
        # Validate borders
        if 'borders' in theme_data:
            self._validate_borders(theme_data['borders'])
    
    def _validate_colors(self, colors: Dict[str, str]) -> None:
        """Validate color values."""
        required_colors = ['primary', 'background', 'text-primary']
        
        for color_name in required_colors:
            if color_name not in colors:
                raise ThemeValidationError(f"Missing required color: {color_name}")
        
        for color_name, color_value in colors.items():
            if not isinstance(color_value, str):
                raise ThemeValidationError(f"Color value must be string: {color_name}")
            
            if not self.COLOR_PATTERN.match(color_value):
                raise ThemeValidationError(f"Invalid color format for {color_name}: {color_value}")
    
    def _validate_typography(self, typography: Dict[str, str]) -> None:
        """Validate typography settings."""
        for key, value in typography.items():
            if not isinstance(value, str):
                raise ThemeValidationError(f"Typography value must be string: {key}")
            
            if 'font-family' in key:
                if not self.FONT_FAMILY_PATTERN.match(value):
                    raise ThemeValidationError(f"Invalid font family: {value}")
            elif 'font-size' in key or 'line-height' in key:
                if not (self.SIZE_PATTERN.match(value) or self.NUMERIC_PATTERN.match(value)):
                    raise ThemeValidationError(f"Invalid size value for {key}: {value}")
    
    def _validate_spacing(self, spacing: Dict[str, Any]) -> None:
        """Validate spacing settings."""
        for key, value in spacing.items():
            if key == 'spacers' and isinstance(value, dict):
                for spacer_key, spacer_value in value.items():
                    if not isinstance(spacer_value, str):
                        raise ThemeValidationError(f"Spacer value must be string: {spacer_key}")
                    if spacer_value != '0' and not self.SIZE_PATTERN.match(spacer_value):
                        raise ThemeValidationError(f"Invalid spacer value: {spacer_value}")
            elif isinstance(value, str):
                if value != '0' and not self.SIZE_PATTERN.match(value):
                    raise ThemeValidationError(f"Invalid spacing value for {key}: {value}")
    
    def _validate_borders(self, borders: Dict[str, str]) -> None:
        """Validate border settings."""
        for key, value in borders.items():
            if not isinstance(value, str):
                raise ThemeValidationError(f"Border value must be string: {key}")
            
            if 'radius' in key:
                if not (self.SIZE_PATTERN.match(value) or value == '0'):
                    raise ThemeValidationError(f"Invalid border radius: {value}")
            elif key == 'width':
                if not self.SIZE_PATTERN.match(value):
                    raise ThemeValidationError(f"Invalid border width: {value}")
    
    def _compile_theme(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile theme data into CSS variables.
        """
        css_variables = {}
        
        # Compile colors
        if 'colors' in theme_data:
            for color_name, color_value in theme_data['colors'].items():
                css_variables[f'--theme-color-{color_name}'] = color_value
        
        # Compile typography
        if 'typography' in theme_data:
            for typo_key, typo_value in theme_data['typography'].items():
                css_key = typo_key.replace('_', '-')
                css_variables[f'--theme-{css_key}'] = typo_value
        
        # Compile spacing
        if 'spacing' in theme_data:
            for space_key, space_value in theme_data['spacing'].items():
                if space_key == 'spacers' and isinstance(space_value, dict):
                    for spacer_key, spacer_value in space_value.items():
                        css_variables[f'--theme-spacer-{spacer_key}'] = spacer_value
                else:
                    css_variables[f'--theme-spacing-{space_key}'] = space_value
        
        # Compile borders
        if 'borders' in theme_data:
            for border_key, border_value in theme_data['borders'].items():
                css_key = border_key.replace('_', '-')
                css_variables[f'--theme-border-{css_key}'] = border_value
        
        # Compile shadows
        if 'shadows' in theme_data:
            for shadow_key, shadow_value in theme_data['shadows'].items():
                css_variables[f'--theme-shadow-{shadow_key}'] = shadow_value
        
        # Compile components
        if 'components' in theme_data:
            for component_name, component_styles in theme_data['components'].items():
                if isinstance(component_styles, dict):
                    for style_key, style_value in component_styles.items():
                        css_key = style_key.replace('_', '-')
                        css_variables[f'--theme-{component_name}-{css_key}'] = style_value
        
        return {
            'css_variables': css_variables,
            'theme_data': theme_data,
            'compiled_at': timezone.now().isoformat()
        }
    
    def _clear_theme_cache(self, user: User) -> None:
        """Clear theme cache for a user."""
        cache_key = f"{self.CACHE_PREFIX}active:{user.id}"
        cache.delete(cache_key)
    
    def _log_theme_action(self, user: User, action: str, theme: Optional[UserThemePreference] = None,
                         request_meta: Optional[Dict] = None) -> None:
        """Log theme-related actions for audit."""
        details = {}
        
        if theme:
            details['theme_id'] = str(theme.id)
            details['theme_name'] = theme.name
        
        ip_address = None
        user_agent = ''
        
        if request_meta:
            ip_address = request_meta.get('REMOTE_ADDR')
            user_agent = request_meta.get('HTTP_USER_AGENT', '')
        
        ThemeAuditLog.objects.create(
            user=user,
            theme=theme,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )


# Singleton instance
theme_service = ThemeService()