"""
Unit tests for authentication functionality.
Tests the authentication and authorization system.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import pytest
from unittest.mock import Mock, patch
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from app.auth import (
    authenticate_user,
    authorize_user,
    login_user,
    logout_user,
    require_permission,
    validate_session,
)


class TestAuthentication:
    """Test cases for authentication functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.auth.User')
    @patch('app.auth.check_password')
    def test_authenticate_user_success(self, mock_check_password, mock_user):
        """Test successful user authentication."""
        # Mock user
        mock_user_instance = Mock()
        mock_user_instance.is_active = True
        mock_user_instance.password_hash = 'hashed_password'
        
        mock_user.objects.filter.return_value.first.return_value = mock_user_instance
        mock_check_password.return_value = True
        
        # Test
        result = authenticate_user('testuser', 'password123')
        
        # Verify
        assert result == mock_user_instance
        mock_user.objects.filter.assert_called_once()
        mock_check_password.assert_called_once_with('password123', 'hashed_password')
    
    @patch('app.auth.User')
    def test_authenticate_user_not_found(self, mock_user):
        """Test authentication with non-existent user."""
        mock_user.objects.filter.return_value.first.return_value = None
        
        result = authenticate_user('nonexistent', 'password123')
        
        assert result is None
    
    @patch('app.auth.User')
    @patch('app.auth.check_password')
    def test_authenticate_user_wrong_password(self, mock_check_password, mock_user):
        """Test authentication with wrong password."""
        # Mock user
        mock_user_instance = Mock()
        mock_user_instance.is_active = True
        mock_user_instance.password_hash = 'hashed_password'
        
        mock_user.objects.filter.return_value.first.return_value = mock_user_instance
        mock_check_password.return_value = False
        
        result = authenticate_user('testuser', 'wrong_password')
        
        assert result is None
    
    @patch('app.auth.User')
    def test_authenticate_user_inactive(self, mock_user):
        """Test authentication with inactive user."""
        # Mock inactive user
        mock_user_instance = Mock()
        mock_user_instance.is_active = False
        
        mock_user.objects.filter.return_value.first.return_value = mock_user_instance
        
        result = authenticate_user('testuser', 'password123')
        
        assert result is None


class TestAuthorization:
    """Test cases for authorization functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.auth.RBACManager')
    def test_authorize_user_success(self, mock_rbac_manager):
        """Test successful user authorization."""
        # Mock RBAC manager
        mock_rbac_instance = Mock()
        mock_rbac_instance.has_permission.return_value = True
        mock_rbac_manager.return_value = mock_rbac_instance
        
        # Test
        result = authorize_user('user-123', 'read_users')
        
        # Verify
        assert result is True
        mock_rbac_instance.has_permission.assert_called_once_with('user-123', 'read_users')
    
    @patch('app.auth.RBACManager')
    def test_authorize_user_no_permission(self, mock_rbac_manager):
        """Test user authorization without permission."""
        # Mock RBAC manager
        mock_rbac_instance = Mock()
        mock_rbac_instance.has_permission.return_value = False
        mock_rbac_manager.return_value = mock_rbac_instance
        
        result = authorize_user('user-123', 'admin_users')
        
        assert result is False


class TestSessionManagement:
    """Test cases for session management functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    def _add_session_to_request(self, request):
        """Add session to request for testing."""
        middleware = SessionMiddleware(Mock())
        middleware.process_request(request)
        request.session.save()
    
    @patch('app.auth.audit_logger')
    def test_login_user_success(self, mock_audit_logger):
        """Test successful user login."""
        # Create request with session
        request = self.factory.post('/login/')
        self._add_session_to_request(request)
        
        # Mock user
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.username = 'testuser'
        
        # Test
        result = login_user(request, mock_user)
        
        # Verify
        assert result is True
        assert request.session['user_id'] == 'user-123'
        assert request.session['username'] == 'testuser'
        mock_audit_logger.log_activity.assert_called_once()
    
    @patch('app.auth.audit_logger')
    def test_logout_user_success(self, mock_audit_logger):
        """Test successful user logout."""
        # Create request with session
        request = self.factory.post('/logout/')
        self._add_session_to_request(request)
        
        # Set up session
        request.session['user_id'] = 'user-123'
        request.session['username'] = 'testuser'
        
        # Test
        result = logout_user(request)
        
        # Verify
        assert result is True
        assert 'user_id' not in request.session
        assert 'username' not in request.session
        mock_audit_logger.log_activity.assert_called_once()
    
    def test_validate_session_valid(self):
        """Test session validation for valid session."""
        # Create request with valid session
        request = self.factory.get('/dashboard/')
        self._add_session_to_request(request)
        
        request.session['user_id'] = 'user-123'
        request.session['last_activity'] = 1640995200  # Recent timestamp
        
        result = validate_session(request)
        
        assert result is True
    
    def test_validate_session_expired(self):
        """Test session validation for expired session."""
        # Create request with expired session
        request = self.factory.get('/dashboard/')
        self._add_session_to_request(request)
        
        request.session['user_id'] = 'user-123'
        request.session['last_activity'] = 1609459200  # Old timestamp
        
        result = validate_session(request)
        
        assert result is False
    
    def test_validate_session_missing(self):
        """Test session validation for missing session."""
        request = self.factory.get('/dashboard/')
        self._add_session_to_request(request)
        
        result = validate_session(request)
        
        assert result is False


class TestPermissionDecorator:
    """Test cases for permission decorator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.auth.authorize_user')
    def test_require_permission_success(self, mock_authorize_user):
        """Test permission decorator with authorized user."""
        mock_authorize_user.return_value = True
        
        # Create decorated function
        @require_permission('read_users')
        def test_view(request):
            return 'success'
        
        # Create request with user
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.id = 'user-123'
        
        # Test
        result = test_view(request)
        
        # Verify
        assert result == 'success'
        mock_authorize_user.assert_called_once_with('user-123', 'read_users')
    
    @patch('app.auth.authorize_user')
    @patch('app.auth.JsonResponse')
    def test_require_permission_denied(self, mock_json_response, mock_authorize_user):
        """Test permission decorator with unauthorized user."""
        mock_authorize_user.return_value = False
        mock_json_response.return_value = Mock()
        
        # Create decorated function
        @require_permission('admin_users')
        def test_view(request):
            return 'success'
        
        # Create request with user
        request = self.factory.get('/test/')
        request.user = Mock()
        request.user.id = 'user-123'
        
        # Test
        result = test_view(request)
        
        # Verify
        mock_json_response.assert_called_once()
        call_args = mock_json_response.call_args
        assert call_args[0][0]['error'] == 'Permission denied'
        assert call_args[1]['status'] == 403
    
    @patch('app.auth.JsonResponse')
    def test_require_permission_anonymous_user(self, mock_json_response):
        """Test permission decorator with anonymous user."""
        mock_json_response.return_value = Mock()
        
        # Create decorated function
        @require_permission('read_users')
        def test_view(request):
            return 'success'
        
        # Create request with anonymous user
        request = self.factory.get('/test/')
        request.user = AnonymousUser()
        
        # Test
        result = test_view(request)
        
        # Verify
        mock_json_response.assert_called_once()
        call_args = mock_json_response.call_args
        assert call_args[0][0]['error'] == 'Authentication required'
        assert call_args[1]['status'] == 401