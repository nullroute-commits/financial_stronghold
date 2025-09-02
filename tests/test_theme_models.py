"""
Unit tests for theme models.

Created by: Team Epsilon (Echo)
Date: 2025-01-02
"""

import uuid
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from app.models.theme_models import (
    UserThemePreference,
    ThemeTemplate,
    ThemeAuditLog,
    ThemeCategory,
    DEFAULT_THEME_DATA
)

User = get_user_model()


class UserThemePreferenceModelTest(TestCase):
    """Test cases for UserThemePreference model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.valid_theme_data = {
            'colors': {
                'primary': '#0d6efd',
                'background': '#ffffff',
                'text-primary': '#212529'
            },
            'typography': {
                'font-family-base': 'Arial, sans-serif',
                'font-size-base': '16px'
            },
            'spacing': {
                'spacer': '1rem'
            },
            'borders': {
                'radius': '0.375rem',
                'width': '1px'
            }
        }
    
    def test_create_theme_preference(self):
        """Test creating a theme preference."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='My Custom Theme',
            description='A test theme',
            theme_data=self.valid_theme_data
        )
        
        self.assertEqual(theme.user, self.user)
        self.assertEqual(theme.name, 'My Custom Theme')
        self.assertEqual(theme.category, ThemeCategory.CUSTOM)
        self.assertFalse(theme.is_active)
        self.assertFalse(theme.is_default)
        self.assertEqual(theme.version, '1.0')
    
    def test_unique_theme_name_per_user(self):
        """Test that theme names must be unique per user."""
        UserThemePreference.objects.create(
            user=self.user,
            name='Duplicate Theme',
            theme_data=self.valid_theme_data
        )
        
        with self.assertRaises(IntegrityError):
            UserThemePreference.objects.create(
                user=self.user,
                name='Duplicate Theme',
                theme_data=self.valid_theme_data
            )
    
    def test_only_one_active_theme_per_user(self):
        """Test that only one theme can be active per user."""
        theme1 = UserThemePreference.objects.create(
            user=self.user,
            name='Theme 1',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        # Creating another active theme should fail
        with self.assertRaises(IntegrityError):
            UserThemePreference.objects.create(
                user=self.user,
                name='Theme 2',
                theme_data=self.valid_theme_data,
                is_active=True
            )
    
    def test_activate_theme(self):
        """Test activating a theme."""
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
        
        # Activate theme2
        theme2.activate()
        
        # Refresh from database
        theme1.refresh_from_db()
        theme2.refresh_from_db()
        
        self.assertFalse(theme1.is_active)
        self.assertTrue(theme2.is_active)
    
    def test_theme_data_validation(self):
        """Test theme data validation."""
        # Missing required section
        invalid_data = {
            'colors': {'primary': '#0d6efd'},
            'typography': {},
            'spacing': {}
            # Missing 'borders' section
        }
        
        theme = UserThemePreference(
            user=self.user,
            name='Invalid Theme',
            theme_data=invalid_data
        )
        
        with self.assertRaises(ValidationError) as context:
            theme.full_clean()
        
        self.assertIn('borders', str(context.exception))
    
    def test_invalid_color_format(self):
        """Test invalid color format validation."""
        invalid_theme_data = self.valid_theme_data.copy()
        invalid_theme_data['colors']['primary'] = 'not-a-color'
        
        theme = UserThemePreference(
            user=self.user,
            name='Invalid Color Theme',
            theme_data=invalid_theme_data
        )
        
        with self.assertRaises(ValidationError) as context:
            theme.full_clean()
        
        self.assertIn('color format', str(context.exception))
    
    def test_str_representation(self):
        """Test string representation of theme."""
        theme = UserThemePreference.objects.create(
            user=self.user,
            name='Test Theme',
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        expected = f"{self.user.email} - Test Theme (Active)"
        self.assertEqual(str(theme), expected)


class ThemeTemplateModelTest(TestCase):
    """Test cases for ThemeTemplate model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        
        self.theme_data = DEFAULT_THEME_DATA.copy()
    
    def test_create_theme_template(self):
        """Test creating a theme template."""
        template = ThemeTemplate.objects.create(
            name='Ocean Blue',
            description='A calming blue theme',
            category=ThemeCategory.LIGHT,
            theme_data=self.theme_data,
            created_by=self.user
        )
        
        self.assertEqual(template.name, 'Ocean Blue')
        self.assertEqual(template.category, ThemeCategory.LIGHT)
        self.assertTrue(template.is_public)
        self.assertFalse(template.is_featured)
        self.assertEqual(template.usage_count, 0)
    
    def test_unique_template_name(self):
        """Test that template names must be unique."""
        ThemeTemplate.objects.create(
            name='Unique Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=self.user
        )
        
        with self.assertRaises(IntegrityError):
            ThemeTemplate.objects.create(
                name='Unique Template',
                description='Another test',
                theme_data=self.theme_data,
                created_by=self.user
            )
    
    def test_increment_usage_count(self):
        """Test incrementing usage count."""
        template = ThemeTemplate.objects.create(
            name='Popular Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=self.user
        )
        
        self.assertEqual(template.usage_count, 0)
        
        template.increment_usage()
        template.refresh_from_db()
        
        self.assertEqual(template.usage_count, 1)
    
    def test_create_user_preference_from_template(self):
        """Test creating user preference from template."""
        template = ThemeTemplate.objects.create(
            name='Base Template',
            description='Test template',
            category=ThemeCategory.DARK,
            theme_data=self.theme_data,
            created_by=self.user
        )
        
        test_user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Create preference from template
        preference = template.create_user_preference(test_user, 'My Dark Theme')
        
        self.assertEqual(preference.user, test_user)
        self.assertEqual(preference.name, 'My Dark Theme')
        self.assertEqual(preference.category, ThemeCategory.DARK)
        self.assertEqual(preference.theme_data, self.theme_data)
        self.assertIn('Based on Base Template', preference.description)
        
        # Check usage count increased
        template.refresh_from_db()
        self.assertEqual(template.usage_count, 1)
    
    def test_template_ordering(self):
        """Test template ordering."""
        template1 = ThemeTemplate.objects.create(
            name='Regular Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=self.user,
            usage_count=10
        )
        
        template2 = ThemeTemplate.objects.create(
            name='Featured Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=self.user,
            is_featured=True,
            usage_count=5
        )
        
        template3 = ThemeTemplate.objects.create(
            name='Popular Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=self.user,
            usage_count=20
        )
        
        templates = list(ThemeTemplate.objects.all())
        
        # Featured should come first, then by usage count
        self.assertEqual(templates[0], template2)  # Featured
        self.assertEqual(templates[1], template3)  # Highest usage
        self.assertEqual(templates[2], template1)  # Lower usage


class ThemeAuditLogModelTest(TestCase):
    """Test cases for ThemeAuditLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.theme = UserThemePreference.objects.create(
            user=self.user,
            name='Test Theme',
            theme_data={
                'colors': {'primary': '#0d6efd', 'background': '#ffffff', 'text-primary': '#212529'},
                'typography': {'font-family-base': 'Arial'},
                'spacing': {'spacer': '1rem'},
                'borders': {'radius': '0.375rem'}
            }
        )
    
    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        audit_log = ThemeAuditLog.objects.create(
            user=self.user,
            theme=self.theme,
            action='created',
            details={'theme_id': str(self.theme.id)},
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0'
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.theme, self.theme)
        self.assertEqual(audit_log.action, 'created')
        self.assertEqual(audit_log.ip_address, '127.0.0.1')
    
    def test_audit_log_ordering(self):
        """Test audit logs are ordered by creation date descending."""
        log1 = ThemeAuditLog.objects.create(
            user=self.user,
            action='created'
        )
        
        log2 = ThemeAuditLog.objects.create(
            user=self.user,
            action='updated'
        )
        
        logs = list(ThemeAuditLog.objects.all())
        
        # Most recent should be first
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)
    
    def test_audit_log_without_theme(self):
        """Test creating audit log without theme reference."""
        audit_log = ThemeAuditLog.objects.create(
            user=self.user,
            action='exported',
            details={'export_format': 'json'}
        )
        
        self.assertIsNone(audit_log.theme)
        self.assertEqual(audit_log.action, 'exported')
    
    def test_str_representation(self):
        """Test string representation of audit log."""
        audit_log = ThemeAuditLog.objects.create(
            user=self.user,
            action='activated'
        )
        
        expected = f"{self.user.email} - activated - {audit_log.created_at}"
        self.assertEqual(str(audit_log), expected)


class ThemeManagerTest(TestCase):
    """Test cases for custom theme managers."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='pass123'
        )
        
        self.theme_data = {
            'colors': {'primary': '#0d6efd', 'background': '#ffffff', 'text-primary': '#212529'},
            'typography': {'font-family-base': 'Arial'},
            'spacing': {'spacer': '1rem'},
            'borders': {'radius': '0.375rem'}
        }
    
    def test_get_active_theme_for_user(self):
        """Test getting active theme for a user."""
        # Create inactive theme
        UserThemePreference.objects.create(
            user=self.user1,
            name='Inactive Theme',
            theme_data=self.theme_data,
            is_active=False
        )
        
        # Create active theme
        active_theme = UserThemePreference.objects.create(
            user=self.user1,
            name='Active Theme',
            theme_data=self.theme_data,
            is_active=True
        )
        
        # Create theme for different user
        UserThemePreference.objects.create(
            user=self.user2,
            name='Other User Theme',
            theme_data=self.theme_data,
            is_active=True
        )
        
        result = UserThemePreference.objects.get_active_theme_for_user(self.user1)
        
        self.assertEqual(result, active_theme)
    
    def test_get_public_templates(self):
        """Test getting public templates."""
        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass'
        )
        
        # Create public template
        public_template = ThemeTemplate.objects.create(
            name='Public Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=admin_user,
            is_public=True,
            usage_count=10
        )
        
        # Create private template
        ThemeTemplate.objects.create(
            name='Private Template',
            description='Test',
            theme_data=self.theme_data,
            created_by=admin_user,
            is_public=False
        )
        
        templates = ThemeTemplate.objects.get_public_templates()
        
        self.assertEqual(templates.count(), 1)
        self.assertEqual(templates.first(), public_template)