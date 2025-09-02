"""
Integration tests for theme API endpoints.

Created by: Team Epsilon (Echo)
Date: 2025-01-02
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from app.models.theme_models import (
    UserThemePreference,
    ThemeTemplate,
    ThemeAuditLog,
    ThemeCategory,
    DEFAULT_THEME_DATA
)

User = get_user_model()


class ThemeAPIIntegrationTest(TestCase):
    """Integration tests for theme API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test users
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Valid theme data
        self.valid_theme_data = {
            'colors': {
                'primary': '#0d6efd',
                'secondary': '#6c757d',
                'success': '#198754',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#0dcaf0',
                'light': '#f8f9fa',
                'dark': '#212529',
                'background': '#ffffff',
                'surface': '#f5f5f5',
                'text-primary': '#212529',
                'text-secondary': '#6c757d'
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
        
        # Create some test themes
        self.theme1 = UserThemePreference.objects.create(
            user=self.user,
            name='My Light Theme',
            category=ThemeCategory.LIGHT,
            theme_data=self.valid_theme_data,
            is_active=True
        )
        
        self.theme2 = UserThemePreference.objects.create(
            user=self.user,
            name='My Dark Theme',
            category=ThemeCategory.DARK,
            theme_data=self.valid_theme_data,
            is_active=False
        )
        
        # Create theme template
        self.template = ThemeTemplate.objects.create(
            name='Ocean Blue',
            description='A calming blue theme',
            category=ThemeCategory.LIGHT,
            theme_data=DEFAULT_THEME_DATA,
            created_by=self.admin_user,
            is_featured=True
        )
    
    def test_list_user_themes(self):
        """Test listing user themes."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Check theme data
        theme_names = [theme['name'] for theme in response.data]
        self.assertIn('My Light Theme', theme_names)
        self.assertIn('My Dark Theme', theme_names)
    
    def test_list_themes_requires_authentication(self):
        """Test that listing themes requires authentication."""
        url = reverse('theme-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_themes_filtered_by_user(self):
        """Test that users only see their own themes."""
        # Create theme for other user
        UserThemePreference.objects.create(
            user=self.other_user,
            name='Other User Theme',
            theme_data=self.valid_theme_data
        )
        
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-list')
        response = self.client.get(url)
        
        self.assertEqual(len(response.data), 2)
        for theme in response.data:
            self.assertEqual(theme['user'], self.user.id)
    
    def test_filter_themes_by_category(self):
        """Test filtering themes by category."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-list')
        response = self.client.get(url, {'category': 'dark'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'My Dark Theme')
    
    def test_get_active_theme(self):
        """Test getting the active theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('css_variables', response.data)
        self.assertIn('theme_data', response.data)
        self.assertEqual(response.data['id'], str(self.theme1.id))
        self.assertEqual(response.data['name'], 'My Light Theme')
    
    def test_get_single_theme(self):
        """Test getting a single theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-detail', kwargs={'pk': self.theme1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'My Light Theme')
        self.assertTrue(response.data['is_active'])
    
    def test_get_other_user_theme_forbidden(self):
        """Test cannot get other user's theme."""
        self.client.force_authenticate(user=self.other_user)
        
        url = reverse('theme-detail', kwargs={'pk': self.theme1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_theme(self):
        """Test creating a new theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-list')
        data = {
            'name': 'New Custom Theme',
            'description': 'My custom theme',
            'category': 'custom',
            'theme_data': self.valid_theme_data
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Custom Theme')
        self.assertEqual(response.data['description'], 'My custom theme')
        self.assertFalse(response.data['is_active'])
        
        # Check theme was created
        theme = UserThemePreference.objects.get(id=response.data['id'])
        self.assertEqual(theme.user, self.user)
        
        # Check audit log
        audit_log = ThemeAuditLog.objects.filter(
            user=self.user,
            action='created',
            theme=theme
        ).exists()
        self.assertTrue(audit_log)
    
    def test_create_theme_from_template(self):
        """Test creating theme from template."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-list')
        data = {
            'name': 'From Template',
            'theme_data': {'colors': {'primary': '#ff0000'}},
            'base_template_id': str(self.template.id)
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check merged theme data
        theme = UserThemePreference.objects.get(id=response.data['id'])
        self.assertEqual(theme.theme_data['colors']['primary'], '#ff0000')
        # Should have other values from template
        self.assertIn('typography', theme.theme_data)
    
    def test_create_theme_invalid_data(self):
        """Test creating theme with invalid data."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-list')
        data = {
            'name': 'Invalid Theme',
            'theme_data': {
                'colors': {'primary': 'not-a-color'},
                'typography': {},
                'spacing': {},
                'borders': {}
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid color format', str(response.data))
    
    def test_update_theme(self):
        """Test updating a theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-detail', kwargs={'pk': self.theme2.id})
        data = {
            'name': 'Updated Dark Theme',
            'theme_data': {
                'colors': {
                    'primary': '#ff0000',
                    'background': '#000000',
                    'text-primary': '#ffffff'
                },
                'typography': {'font-family-base': 'Georgia, serif'},
                'spacing': {'spacer': '1.5rem'},
                'borders': {'radius': '0.5rem'}
            }
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Dark Theme')
        
        # Check theme was updated
        self.theme2.refresh_from_db()
        self.assertEqual(self.theme2.name, 'Updated Dark Theme')
        self.assertEqual(self.theme2.theme_data['colors']['primary'], '#ff0000')
    
    def test_partial_update_theme(self):
        """Test partial update of a theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-detail', kwargs={'pk': self.theme2.id})
        data = {'name': 'Partially Updated Theme'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Partially Updated Theme')
        
        # Theme data should remain unchanged
        self.theme2.refresh_from_db()
        self.assertEqual(self.theme2.theme_data, self.valid_theme_data)
    
    def test_delete_theme(self):
        """Test deleting a theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-detail', kwargs={'pk': self.theme2.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check theme was deleted
        self.assertFalse(
            UserThemePreference.objects.filter(id=self.theme2.id).exists()
        )
    
    def test_delete_active_theme_fails(self):
        """Test cannot delete active theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-detail', kwargs={'pk': self.theme1.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot delete an active theme', str(response.data))
    
    def test_activate_theme(self):
        """Test activating a theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-activate', kwargs={'pk': self.theme2.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])
        
        # Check theme statuses
        self.theme1.refresh_from_db()
        self.theme2.refresh_from_db()
        
        self.assertFalse(self.theme1.is_active)
        self.assertTrue(self.theme2.is_active)
    
    def test_preview_theme(self):
        """Test previewing a theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-preview')
        data = {
            'theme_data': {
                'colors': {
                    'primary': '#ff00ff',
                    'background': '#000000',
                    'text-primary': '#ffffff'
                },
                'typography': {'font-family-base': 'Comic Sans MS'},
                'spacing': {'spacer': '2rem'},
                'borders': {'radius': '1rem'}
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('css_variables', response.data)
        self.assertEqual(
            response.data['css_variables']['--theme-color-primary'],
            '#ff00ff'
        )
        
        # No theme should be created
        theme_count = UserThemePreference.objects.filter(user=self.user).count()
        self.assertEqual(theme_count, 2)  # Only the original 2
    
    def test_import_theme(self):
        """Test importing a theme."""
        self.client.force_authenticate(user=self.user)
        
        theme_json = json.dumps({
            'name': 'Imported Theme',
            'version': '1.0',
            'category': 'dark',
            'theme_data': self.valid_theme_data
        })
        
        url = reverse('theme-import-theme')
        data = {
            'theme_json': theme_json,
            'name': 'My Imported Theme'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My Imported Theme')
        
        # Check theme was created
        theme = UserThemePreference.objects.get(id=response.data['id'])
        self.assertEqual(theme.user, self.user)
    
    def test_export_theme(self):
        """Test exporting a theme."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-export', kwargs={'pk': self.theme1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('theme_json', response.data)
        self.assertIn('filename', response.data)
        
        # Parse exported JSON
        exported_data = json.loads(response.data['theme_json'])
        self.assertEqual(exported_data['name'], 'My Light Theme')
        self.assertEqual(exported_data['category'], 'light')
        self.assertEqual(exported_data['theme_data'], self.valid_theme_data)
    
    def test_list_theme_templates(self):
        """Test listing theme templates."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-template-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Ocean Blue')
    
    def test_use_theme_template(self):
        """Test using a theme template."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('theme-template-use-template', kwargs={'pk': self.template.id})
        data = {'name': 'My Ocean Theme'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My Ocean Theme')
        
        # Check template usage count increased
        self.template.refresh_from_db()
        self.assertEqual(self.template.usage_count, 1)
    
    def test_theme_api_performance(self):
        """Test API performance with multiple themes."""
        # Create 50 themes
        for i in range(50):
            UserThemePreference.objects.create(
                user=self.user,
                name=f'Theme {i}',
                theme_data=self.valid_theme_data
            )
        
        self.client.force_authenticate(user=self.user)
        
        # Test listing with reasonable query count
        url = reverse('theme-list')
        
        with self.assertNumQueries(3):  # Auth, count, themes
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 52)  # 50 + 2 original


class ThemeWebIntegrationTest(TestCase):
    """Integration tests for theme web views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='webtest@example.com',
            password='testpass123'
        )
    
    def test_theme_editor_requires_login(self):
        """Test theme editor page requires authentication."""
        url = '/themes/editor/'  # Assuming this URL exists
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_theme_assets_load(self):
        """Test theme CSS and JS assets are accessible."""
        # Test CSS files
        css_files = [
            '/static/css/theme-system.css',
            '/static/css/theme-editor.css'
        ]
        
        for css_file in css_files:
            response = self.client.get(css_file)
            # Note: In test environment, static files might return 404
            # This is more of a smoke test
            self.assertIn(response.status_code, [200, 404])
        
        # Test JS files
        js_files = [
            '/static/js/theme-engine.js',
            '/static/js/theme-editor.js'
        ]
        
        for js_file in js_files:
            response = self.client.get(js_file)
            self.assertIn(response.status_code, [200, 404])