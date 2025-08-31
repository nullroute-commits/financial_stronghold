"""
Unit tests for API functionality.
Tests the REST API endpoints and validation.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import json
import pytest
from unittest.mock import Mock, patch
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from app.api import (
    get_user_profile,
    update_user_profile,
    list_users,
    create_user,
    delete_user,
    list_audit_logs,
    get_system_health,
)


class TestUserAPI:
    """Test cases for User API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.api.get_object_or_404')
    @patch('app.api.JsonResponse')
    def test_get_user_profile_success(self, mock_json_response, mock_get_object):
        """Test successful user profile retrieval."""
        # Mock user
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.first_name = 'Test'
        mock_user.last_name = 'User'
        mock_user.is_active = True
        
        mock_get_object.return_value = mock_user
        
        # Create request
        request = self.factory.get('/api/users/user-123/')
        request.user = mock_user
        
        # Test
        get_user_profile(request, 'user-123')
        
        # Verify
        mock_get_object.assert_called_once()
        mock_json_response.assert_called_once()
        
        # Check the data passed to JsonResponse
        call_args = mock_json_response.call_args[0][0]
        assert call_args['id'] == 'user-123'
        assert call_args['username'] == 'testuser'
        assert call_args['email'] == 'test@example.com'
    
    @patch('app.api.get_object_or_404')
    def test_get_user_profile_not_found(self, mock_get_object):
        """Test user profile retrieval when user not found."""
        mock_get_object.side_effect = Http404()
        
        request = self.factory.get('/api/users/non-existent/')
        request.user = Mock()
        
        with pytest.raises(Http404):
            get_user_profile(request, 'non-existent')
    
    @patch('app.api.json.loads')
    @patch('app.api.get_object_or_404')
    @patch('app.api.JsonResponse')
    def test_update_user_profile_success(self, mock_json_response, mock_get_object, mock_json_loads):
        """Test successful user profile update."""
        # Mock user
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        mock_user.save = Mock()
        
        mock_get_object.return_value = mock_user
        
        # Mock request data
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        mock_json_loads.return_value = update_data
        
        # Create request
        request = self.factory.put('/api/users/user-123/', 
                                 data=json.dumps(update_data),
                                 content_type='application/json')
        request.user = mock_user
        
        # Test
        update_user_profile(request, 'user-123')
        
        # Verify
        mock_user.save.assert_called_once()
        mock_json_response.assert_called_once()
        assert mock_user.first_name == 'Updated'
        assert mock_user.last_name == 'Name'
        assert mock_user.email == 'updated@example.com'


class TestAuditAPI:
    """Test cases for Audit API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.api.AuditLog')
    @patch('app.api.JsonResponse')
    def test_list_audit_logs_success(self, mock_json_response, mock_audit_log):
        """Test successful audit logs listing."""
        # Mock audit logs
        mock_log1 = Mock()
        mock_log1.id = 'log-1'
        mock_log1.action = 'LOGIN'
        mock_log1.user_id = 'user-123'
        mock_log1.timestamp = '2025-01-01T00:00:00Z'
        
        mock_log2 = Mock()
        mock_log2.id = 'log-2'
        mock_log2.action = 'LOGOUT'
        mock_log2.user_id = 'user-123'
        mock_log2.timestamp = '2025-01-01T01:00:00Z'
        
        mock_audit_log.objects.all.return_value = [mock_log1, mock_log2]
        
        # Create request
        request = self.factory.get('/api/audit/')
        request.user = Mock()
        request.user.is_staff = True
        
        # Test
        list_audit_logs(request)
        
        # Verify
        mock_json_response.assert_called_once()
        call_args = mock_json_response.call_args[0][0]
        assert len(call_args['logs']) == 2
        assert call_args['logs'][0]['action'] == 'LOGIN'
        assert call_args['logs'][1]['action'] == 'LOGOUT'


class TestSystemAPI:
    """Test cases for System API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.api.cache')
    @patch('app.api.connection')
    @patch('app.api.JsonResponse')
    def test_get_system_health_success(self, mock_json_response, mock_connection, mock_cache):
        """Test successful system health check."""
        # Mock cache health
        mock_cache.get.return_value = 'test'
        mock_cache.set.return_value = True
        
        # Mock database health
        mock_connection.cursor.return_value.__enter__.return_value.execute.return_value = None
        
        # Create request
        request = self.factory.get('/api/health/')
        request.user = Mock()
        request.user.is_staff = True
        
        # Test
        get_system_health(request)
        
        # Verify
        mock_json_response.assert_called_once()
        call_args = mock_json_response.call_args[0][0]
        assert call_args['status'] == 'healthy'
        assert 'database' in call_args['checks']
        assert 'cache' in call_args['checks']
    
    @patch('app.api.cache')
    @patch('app.api.JsonResponse')
    def test_get_system_health_cache_failure(self, mock_json_response, mock_cache):
        """Test system health check with cache failure."""
        # Mock cache failure
        mock_cache.get.side_effect = Exception("Cache connection failed")
        
        # Create request
        request = self.factory.get('/api/health/')
        request.user = Mock()
        request.user.is_staff = True
        
        # Test
        get_system_health(request)
        
        # Verify
        mock_json_response.assert_called_once()
        call_args = mock_json_response.call_args[0][0]
        assert call_args['status'] == 'degraded'
        assert call_args['checks']['cache']['status'] == 'failed'