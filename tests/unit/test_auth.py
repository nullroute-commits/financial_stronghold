"""
Unit tests for authentication system.
Tests JWT token handling, user authentication, and tenant context.

Last updated: 2025-08-31 by AI Assistant
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import get_current_user, get_tenant_context, require_role
from app.core.models import User
from app.core.tenant import TenantType, Organization


class TestAuthentication:
    """Test cases for authentication functions."""
    
    @patch('app.auth.jwt.decode')
    def test_get_current_user_valid_token(self, mock_jwt_decode):
        """Test successful user authentication with valid token."""
        # Mock JWT payload
        mock_jwt_decode.return_value = {
            'sub': 'user-123',
            'tenant_type': 'user',
            'tenant_id': 'user-123'
        }
        
        # Mock user from database
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        mock_user.is_active = True
        
        # Mock database session with query
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Create credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        # Test
        user, tenant_type, tenant_id = get_current_user(credentials, db)
        
        # Verify
        assert user == mock_user
        assert tenant_type == 'user'
        assert tenant_id == 'user-123'
        mock_jwt_decode.assert_called_once()
    
    def test_get_current_user_no_credentials(self):
        """Test authentication failure with missing credentials."""
        db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(None, db)
        
        assert exc_info.value.status_code == 401
        assert "Missing token" in str(exc_info.value.detail)
    
    @patch('app.auth.jwt.decode')
    def test_get_current_user_invalid_token(self, mock_jwt_decode):
        """Test authentication failure with invalid token."""
        # Mock JWT decode to raise JWTError
        from jose import JWTError
        mock_jwt_decode.side_effect = JWTError("Invalid token")
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token"
        )
        db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)
    
    @patch('app.auth.jwt.decode')
    def test_get_current_user_missing_user_in_db(self, mock_jwt_decode):
        """Test authentication failure when user not found in database."""
        # Mock JWT payload
        mock_jwt_decode.return_value = {
            'sub': 'user-123',
            'tenant_type': 'user',
            'tenant_id': 'user-123'
        }
        
        # Mock user not found in database
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = None
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)
    
    @patch('app.auth.jwt.decode')
    def test_get_current_user_inactive_user(self, mock_jwt_decode):
        """Test authentication failure with inactive user."""
        # Mock JWT payload
        mock_jwt_decode.return_value = {
            'sub': 'user-123',
            'tenant_type': 'user',
            'tenant_id': 'user-123'
        }
        
        # Mock inactive user
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        mock_user.is_active = False
        
        db = Mock()
        db.query.return_value.filter.return_value.first.return_value = mock_user
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "inactive" in str(exc_info.value.detail).lower()


class TestTenantContext:
    """Test cases for tenant context functions."""
    
    def test_get_tenant_context_user_mode(self):
        """Test tenant context for user mode."""
        # Mock user tuple from get_current_user
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        user_tuple = (mock_user, 'user', 'user-123')
        
        context = get_tenant_context(user_tuple)
        
        assert context['tenant_type'] == 'user'
        assert context['tenant_id'] == 'user-123'
        assert context['user'] == mock_user
    
    def test_get_tenant_context_organization_mode(self):
        """Test tenant context for organization mode."""
        # Mock user tuple from get_current_user
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        user_tuple = (mock_user, 'organization', 'org-456')
        
        context = get_tenant_context(user_tuple)
        
        assert context['tenant_type'] == 'organization'
        assert context['tenant_id'] == 'org-456'
        assert context['user'] == mock_user


class TestRoleRequirement:
    """Test cases for role requirement decorator/function."""
    
    @patch('app.auth.get_db_session')
    def test_require_role_success(self, mock_get_db_session):
        """Test successful role requirement check for organization."""
        # Mock database session
        mock_db = Mock()
        mock_get_db_session.return_value = iter([mock_db])
        
        # Mock user organization link with correct role
        mock_link = Mock()
        mock_link.role = 'admin'
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_link
        
        # Mock user tuple for organization
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        user_tuple = (mock_user, 'organization', '456')  # Use numeric org ID
        
        # Test - should not raise exception
        result = require_role(['admin'])(user_tuple)
        
        # Verify
        assert result == mock_link
        mock_db.query.assert_called_once()
        mock_db.close.assert_called_once()
    
    def test_require_role_failure_user_tenant(self):
        """Test role requirement check fails for user tenant."""
        # Mock user tuple for user tenant (not organization)
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        user_tuple = (mock_user, 'user', 'user-123')
        
        # Test - should raise exception
        with pytest.raises(HTTPException) as exc_info:
            require_role(['admin'])(user_tuple)
        
        assert exc_info.value.status_code == 400
        assert "Role checks only apply to organization tenants" in str(exc_info.value.detail)
    
    @patch('app.auth.get_db_session')
    def test_require_role_failure_insufficient_permissions(self, mock_get_db_session):
        """Test role requirement check fails for insufficient permissions."""
        # Mock database session
        mock_db = Mock()
        mock_get_db_session.return_value = iter([mock_db])
        
        # Mock user organization link without required role
        mock_link = Mock()
        mock_link.role = 'user'  # Not admin
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_link
        
        # Mock user tuple for organization
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        user_tuple = (mock_user, 'organization', '456')
        
        # Test - should raise exception
        with pytest.raises(HTTPException) as exc_info:
            require_role(['admin'])(user_tuple)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)


class TestTokenValidation:
    """Test cases for token validation edge cases."""
    
    @patch('app.auth.jwt.decode')
    def test_get_current_user_missing_sub_in_token(self, mock_jwt_decode):
        """Test authentication failure when token lacks 'sub' field."""
        # Mock JWT payload without 'sub'
        mock_jwt_decode.return_value = {
            'tenant_type': 'user',
            'tenant_id': 'user-123'
        }
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token"
        )
        db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials, db)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)
    
    @patch('app.auth.jwt.decode')
    def test_get_current_user_organization_mode(self, mock_jwt_decode):
        """Test authentication in organization mode."""
        # Mock JWT payload for organization
        mock_jwt_decode.return_value = {
            'sub': 'user-123',
            'tenant_type': 'organization',
            'tenant_id': '456'  # Use numeric org ID
        }
        
        # Mock user from database
        mock_user = Mock(spec=User)
        mock_user.id = 'user-123'
        mock_user.is_active = True
        
        # Mock organization link
        mock_link = Mock()
        
        # Mock database session
        db = Mock()
        
        # Set up query side effects for different models
        def query_side_effect(model):
            if model == User:
                mock_query = Mock()
                mock_query.filter.return_value.first.return_value = mock_user
                return mock_query
            elif hasattr(model, '__name__') and 'UserOrganizationLink' in model.__name__:
                mock_query = Mock()
                mock_query.filter_by.return_value.first.return_value = mock_link
                return mock_query
            return Mock()
        
        db.query.side_effect = query_side_effect
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )
        
        # Test
        user, tenant_type, tenant_id = get_current_user(credentials, db)
        
        # Verify
        assert user == mock_user
        assert tenant_type == 'organization'
        assert tenant_id == '456'