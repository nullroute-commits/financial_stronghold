"""
Unit tests for theme service layer.

Created by: Team Epsilon (Echo)
Date: 2025-01-02
"""

import json
from unittest.mock import patch, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError

from app.services.theme_service import ThemeService, ThemeValidationError
from app.models.theme_models import (
    UserThemePreference,
    ThemeTemplate,
    ThemeAuditLog,
    ThemeCategory,
    DEFAULT_THEME_DATA
)

User = get_user_model()


class ThemeServiceTest(TestCase):
    """Test cases for ThemeService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = ThemeService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.valid_theme_data = {
            'colors': {
                'primary': '#0d6efd',
                'secondary': '#6c757d',
                'background': '#ffffff',
                'text-primary': '#212529'
            },
            'typography': {
                'font-family-base': 'Arial, sans-serif',
                'font-size-base': '16px',
                'line-height-base': '1.5'
            },
            'spacing': {
                'spacer': '1rem',
                'container-padding': '1.5rem'
            },
            'borders': {
                'radius': '0.375rem',
                'width': '1px'
            }
        }
        
        # Clear cache before each test
        cache.clear()
    
    def test_get_active_theme_default(self):
        """Test getting active theme returns default when no theme exists."""
        theme = self.service.get_active_theme(self.user)
        
        self.assertIsNotNone(theme)
        self.assertIn('css_variables', theme)
        self.assertIn('theme_data', theme)
        self.assertIn('compiled_at', theme)
        self.assertNotIn('id', theme)  # Default theme has no ID
    
    def test_get_active_theme_from_database(self):
        """Test getting active theme from database."""
        # Create active theme
        user_theme = UserThemePreference.objects.create(
            user=self.user,
            name='My Theme',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        theme = self.service.get_active_theme(self.user)
        
        self.assertEqual(theme['id'], str(user_theme.id))
        self.assertEqual(theme['name'], 'My Theme')
        self.assertIn('css_variables', theme)
        self.assertIn('--theme-color-primary', theme['css_variables'])
        self.assertEqual(theme['css_variables']['--theme-color-primary'], '#0d6efd')
    
    def test_get_active_theme_caching(self):
        """Test that active theme is cached."""
        # Create active theme
        UserThemePreference.objects.create(
            user=self.user,
            name='Cached Theme',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        # First call should hit database
        with self.assertNumQueries(1):
            theme1 = self.service.get_active_theme(self.user)
        
        # Second call should use cache
        with self.assertNumQueries(0):
            theme2 = self.service.get_active_theme(self.user)
        
        self.assertEqual(theme1, theme2)
    
    def test_create_theme_success(self):
        """Test successful theme creation."""
        theme = self.service.create_theme(
            user=self.user,
            name='New Theme',
            theme_data=self.valid_theme_data
        )
        
        self.assertEqual(theme.user, self.user)
        self.assertEqual(theme.name, 'New Theme')
        self.assertEqual(theme.theme_data, self.valid_theme_data)
        self.assertFalse(theme.is_active)
        
        # Check audit log created
        audit_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='created',
            theme=theme
        ).first()
        self.assertIsNotNone(audit_log)
    
    def test_create_theme_from_template(self):
        """Test creating theme from template."""
        # Create template
        template = ThemeTemplate.objects.create(
            name='Base Template',
            description='Test template',
            theme_data=DEFAULT_THEME_DATA,
            created_by=self.user
        )
        
        theme = self.service.create_theme(
            user=self.user,
            name='From Template',
            theme_data={'colors': {'primary': '#ff0000'}},
            base_template_id=str(template.id)
        )
        
        # Should have template data with overrides
        self.assertEqual(theme.theme_data['colors']['primary'], '#ff0000')
        self.assertEqual(theme.theme_data['colors']['secondary'], DEFAULT_THEME_DATA['colors']['secondary'])
        
        # Template usage count should increase
        template.refresh_from_db()
        self.assertEqual(template.usage_count, 1)
    
    def test_create_theme_max_limit(self):
        """Test theme creation respects max limit."""
        # Create max number of themes
        for i in range(self.service.MAX_THEMES_PER_USER):
            UserThemePreference.objects.create(
                user=self.user,
                name=f'Theme {i}',
                theme_data=self.valid_theme_data
            )
        
        # Try to create one more
        with self.assertRaises(ThemeValidationError) as context:
            self.service.create_theme(
                user=self.user,
                name='One Too Many',
                theme_data=self.valid_theme_data
            )
        
        self.assertIn('Maximum theme limit', str(context.exception))
    
    def test_create_theme_size_limit(self):
        """Test theme creation respects size limit."""
        # Create huge theme data
        huge_theme_data = self.valid_theme_data.copy()
        huge_theme_data['huge_data'] = 'x' * (self.service.MAX_THEME_SIZE_KB * 1024)
        
        with self.assertRaises(ThemeValidationError) as context:
            self.service.create_theme(
                user=self.user,
                name='Huge Theme',
                theme_data=huge_theme_data
            )
        
        self.assertIn('too large', str(context.exception))
    
    def test_update_theme_success(self):
        """Test successful theme update."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='Original Name',
            theme_data=self.valid_theme_data
        )
        
        new_theme_data = self.valid_theme_data.copy()
        new_theme_data['colors']['primary'] = '#ff0000'
        
        updated_theme = self.service.update_theme(
            user=self.user,
            theme_id=str(theme.id),
            name='Updated Name',
            theme_data=new_theme_data
        )
        
        self.assertEqual(updated_theme.name, 'Updated Name')
        self.assertEqual(updated_theme.theme_data['colors']['primary'], '#ff0000')
        
        # Check audit log
        audit_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='updated',
            theme=theme
        ).exists()
        self.assertTrue(audit_log)
    
    def test_update_active_theme_clears_cache(self):
        """Test updating active theme clears cache."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='Active Theme',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        # Cache the theme
        self.service.get_active_theme(self.user)
        
        # Update the theme
        with patch.object(self.service, '_clear_theme_cache') as mock_clear:
            self.service.update_theme(
                user=self.user,
                theme_id=str(theme.id),
                name='Updated Active Theme'
            )
            mock_clear.assert_called_once_with(self.user)
    
    def test_activate_theme(self):
        """Test theme activation."""
        theme1 = UserThemePreference.objects.create(
            user=self.user,
            name='Theme 1',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        theme2 = UserThemePreference.objects.create(
            user=self.user,
            name='Theme 2',
            theme_data=self.valid_theme_data,
            is_active=False
        )
        
        activated = self.service.activate_theme(
            user=self.user,
            theme_id=str(theme2.id)
        )
        
        self.assertEqual(activated, theme2)
        
        # Check themes status
        theme1.refresh_from_db()
        theme2.refresh_from_db()
        
        self.assertFalse(theme1.is_active)
        self.assertTrue(theme2.is_active)
        
        # Check audit log
        audit_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='activated',
            theme=theme2
        ).exists()
        self.assertTrue(audit_log)
    
    def test_delete_theme_success(self):
        """Test successful theme deletion."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='To Delete',
            theme_data=self.valid_theme_data,
            is_active=False
        )
        
        self.service.delete_theme(
            user=self.user,
            theme_id=str(theme.id)
        )
        
        # Theme should be deleted
        self.assertFalse(
            UserThemePreference.objects.filter(id=theme.id).exists()
        )
        
        # Audit log should exist
        audit_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='deleted'
        ).exists()
        self.assertTrue(audit_log)
    
    def test_delete_active_theme_fails(self):
        """Test cannot delete active theme."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='Active Theme',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        with self.assertRaises(ThemeValidationError) as context:
            self.service.delete_theme(
                user=self.user,
                theme_id=str(theme.id)
            )
        
        self.assertIn('Cannot delete an active theme', str(context.exception))
    
    def test_import_theme(self):
        """Test importing theme from JSON."""
        theme_json = json.dumps({
            'name': 'Imported Theme',
            'version': '1.0',
            'theme_data': self.valid_theme_data
        })
        
        theme = self.service.import_theme(
            user=self.user,
            theme_json=theme_json
        )
        
        self.assertEqual(theme.name, 'Imported Theme')
        self.assertEqual(theme.theme_data, self.valid_theme_data)
        
        # Check audit logs
        create_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='created',
            theme=theme
        ).exists()
        import_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='imported',
            theme=theme
        ).exists()
        
        self.assertTrue(create_log)
        self.assertTrue(import_log)
    
    def test_import_theme_invalid_json(self):
        """Test importing invalid JSON fails."""
        with self.assertRaises(ThemeValidationError) as context:
            self.service.import_theme(
                user=self.user,
                theme_json='not valid json'
            )
        
        self.assertIn('Invalid JSON format', str(context.exception))
    
    def test_export_theme(self):
        """Test exporting theme to JSON."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='Export Me',
            theme_data=self.valid_theme_data,
            category=ThemeCategory.DARK
        )
        
        exported = self.service.export_theme(
            user=self.user,
            theme_id=str(theme.id)
        )
        
        # Parse exported JSON
        data = json.loads(exported)
        
        self.assertEqual(data['name'], 'Export Me')
        self.assertEqual(data['version'], '1.0')
        self.assertEqual(data['category'], ThemeCategory.DARK)
        self.assertEqual(data['theme_data'], self.valid_theme_data)
        self.assertIn('exported_at', data)
        
        # Check audit log
        audit_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='exported',
            theme=theme
        ).exists()
        self.assertTrue(audit_log)
    
    def test_preview_theme(self):
        """Test theme preview without saving."""
        preview_data = self.valid_theme_data.copy()
        preview_data['colors']['primary'] = '#ff00ff'
        
        result = self.service.preview_theme(preview_data)
        
        self.assertIn('css_variables', result)
        self.assertIn('theme_data', result)
        self.assertEqual(result['css_variables']['--theme-color-primary'], '#ff00ff')
        
        # Ensure no theme was created
        self.assertEqual(UserThemePreference.objects.count(), 0)
    
    def test_validate_colors(self):
        """Test color validation."""
        # Valid colors
        valid_colors = {
            'primary': '#0d6efd',
            'background': '#fff',
            'text-primary': 'rgba(0, 0, 0, 0.87)',
            'accent': 'hsl(200, 100%, 50%)'
        }
        
        # Should not raise
        self.service._validate_colors(valid_colors)
        
        # Invalid color format
        invalid_colors = {
            'primary': 'not-a-color',
            'background': '#ffffff',
            'text-primary': '#000'
        }
        
        with self.assertRaises(ThemeValidationError) as context:
            self.service._validate_colors(invalid_colors)
        
        self.assertIn('Invalid color format', str(context.exception))
        
        # Missing required color
        missing_colors = {
            'primary': '#0d6efd',
            'background': '#ffffff'
            # Missing text-primary
        }
        
        with self.assertRaises(ThemeValidationError) as context:
            self.service._validate_colors(missing_colors)
        
        self.assertIn('Missing required color', str(context.exception))
    
    def test_validate_typography(self):
        """Test typography validation."""
        # Valid typography
        valid_typography = {
            'font-family-base': 'Arial, sans-serif',
            'font-size-base': '16px',
            'line-height-base': '1.5',
            'font-weight-normal': '400'
        }
        
        # Should not raise
        self.service._validate_typography(valid_typography)
        
        # Invalid font family
        invalid_typography = {
            'font-family-base': 'Arial<script>alert(1)</script>'
        }
        
        with self.assertRaises(ThemeValidationError) as context:
            self.service._validate_typography(invalid_typography)
        
        self.assertIn('Invalid font family', str(context.exception))
    
    def test_compile_theme(self):
        """Test theme compilation to CSS variables."""
        result = self.service._compile_theme(self.valid_theme_data)
        
        self.assertIn('css_variables', result)
        self.assertIn('theme_data', result)
        self.assertIn('compiled_at', result)
        
        # Check CSS variable format
        css_vars = result['css_variables']
        self.assertEqual(css_vars['--theme-color-primary'], '#0d6efd')
        self.assertEqual(css_vars['--theme-font-family-base'], 'Arial, sans-serif')
        self.assertEqual(css_vars['--theme-spacing-spacer'], '1rem')
        self.assertEqual(css_vars['--theme-border-radius'], '0.375rem')
    
    def test_get_theme_templates(self):
        """Test getting theme templates."""
        admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass'
        )
        
        # Create templates
        template1 = ThemeTemplate.objects.create(
            name='Light Template',
            description='Test',
            category=ThemeCategory.LIGHT,
            theme_data=self.valid_theme_data,
            created_by=admin,
            is_featured=True
        )
        
        template2 = ThemeTemplate.objects.create(
            name='Dark Template',
            description='Test',
            category=ThemeCategory.DARK,
            theme_data=self.valid_theme_data,
            created_by=admin
        )
        
        # Get all templates
        all_templates = self.service.get_theme_templates()
        self.assertEqual(all_templates.count(), 2)
        
        # Get by category
        dark_templates = self.service.get_theme_templates(category=ThemeCategory.DARK)
        self.assertEqual(dark_templates.count(), 1)
        self.assertEqual(dark_templates.first(), template2)