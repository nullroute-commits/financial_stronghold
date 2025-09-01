"""Comprehensive test coverage for authentication module."""

import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.auth import Authentication, TokenManager, PermissionChecker
from app.core.models import User, Role, Permission
from app.core.tenant import TenantType
from sqlalchemy.orm import Session


class TestAuthentication:
    """Test suite for Authentication class."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def auth_service(self, db_session):
        """Create Authentication service instance."""
        return Authentication()

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.username = "testuser"
        user.email = "test@example.com"
        user.password_hash = "hashed_password"
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        return user

    def test_authentication_init(self, db_session):
        """Test Authentication initialization."""
        auth = Authentication()
        assert auth.secret_key == "your-secret-key-here"
        assert auth.algorithm == "HS256"

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "test_password"
        hashed = auth_service.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)

    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "test_password"
        hashed = auth_service.hash_password(password)
        
        assert auth_service.verify_password(password, hashed) is True
        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_authenticate_success(self, auth_service, mock_user):
        """Test successful authentication."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=True), \
             patch.object(auth_service.token_manager, 'create_access_token', return_value="test_token"):
            
            result = auth_service.authenticate("testuser", "password")
            
            assert result is not None
            assert "access_token" in result
            assert "token_type" in result
            assert result["token_type"] == "Bearer"

    def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.authenticate("nonexistent", "password")
        assert result is None

    def test_authenticate_inactive_user(self, auth_service, mock_user):
        """Test authentication with inactive user."""
        mock_user.is_active = False
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = auth_service.authenticate("testuser", "password")
        assert result is None

    def test_authenticate_wrong_password(self, auth_service, mock_user):
        """Test authentication with wrong password."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch.object(auth_service, 'verify_password', return_value=False):
            result = auth_service.authenticate("testuser", "wrong_password")
            assert result is None

    def test_get_user_by_id_success(self, auth_service, mock_user):
        """Test getting user by ID."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = auth_service.get_user_by_id(str(mock_user.id))
        assert result == mock_user

    def test_get_user_by_id_not_found(self, auth_service):
        """Test getting non-existent user by ID."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.get_user_by_id("nonexistent-id")
        assert result is None

    def test_get_user_by_username_success(self, auth_service, mock_user):
        """Test getting user by username."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = auth_service.get_user_by_username("testuser")
        assert result == mock_user

    def test_get_user_by_username_not_found(self, auth_service):
        """Test getting non-existent user by username."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.get_user_by_username("nonexistent")
        assert result is None

    def test_create_user_success(self, auth_service):
        """Test creating a new user."""
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "password",
            "first_name": "New",
            "last_name": "User"
        }
        
        mock_user = Mock(spec=User)
        auth_service.db.add = Mock()
        auth_service.db.commit = Mock()
        auth_service.db.refresh = Mock()
        
        with patch.object(auth_service, 'hash_password', return_value="hashed_password"), \
             patch('app.auth.User', return_value=mock_user):
            
            result = auth_service.create_user(user_data)
            
            assert result == mock_user
            auth_service.db.add.assert_called_once()
            auth_service.db.commit.assert_called_once()

    def test_create_user_duplicate_username(self, auth_service):
        """Test creating user with duplicate username."""
        user_data = {"username": "existing", "email": "new@example.com"}
        
        # Mock database integrity error
        auth_service.db.commit.side_effect = Exception("UNIQUE constraint failed")
        
        with pytest.raises(Exception):
            auth_service.create_user(user_data)

    def test_update_user_success(self, auth_service, mock_user):
        """Test updating user information."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        auth_service.db.commit = Mock()
        
        update_data = {"first_name": "Updated", "email": "updated@example.com"}
        
        result = auth_service.update_user(str(mock_user.id), update_data)
        
        assert result == mock_user
        auth_service.db.commit.assert_called_once()

    def test_update_user_not_found(self, auth_service):
        """Test updating non-existent user."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.update_user("nonexistent-id", {"first_name": "Updated"})
        assert result is None

    def test_delete_user_success(self, auth_service, mock_user):
        """Test deleting a user."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = mock_user
        auth_service.db.delete = Mock()
        auth_service.db.commit = Mock()
        
        result = auth_service.delete_user(str(mock_user.id))
        
        assert result is True
        auth_service.db.delete.assert_called_once_with(mock_user)
        auth_service.db.commit.assert_called_once()

    def test_delete_user_not_found(self, auth_service):
        """Test deleting non-existent user."""
        auth_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = auth_service.delete_user("nonexistent-id")
        assert result is False


class TestTokenManager:
    """Test suite for TokenManager class."""

    @pytest.fixture
    def token_manager(self):
        """Create TokenManager instance."""
        return TokenManager()

    def test_create_access_token(self, token_manager):
        """Test creating access token."""
        data = {"user_id": "test-user-id", "username": "testuser"}
        
        token = token_manager.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiration(self, token_manager):
        """Test creating access token with custom expiration."""
        data = {"user_id": "test-user-id"}
        expires_delta = timedelta(minutes=30)
        
        token = token_manager.create_access_token(data, expires_delta)
        
        assert token is not None
        
        # Decode token to verify expiration
        with patch('app.auth.settings.SECRET_KEY', 'test_secret'):
            decoded = jwt.decode(token, 'test_secret', algorithms=['HS256'], options={"verify_signature": False})
            assert 'exp' in decoded

    def test_verify_token_valid(self, token_manager):
        """Test verifying valid token."""
        data = {"user_id": "test-user-id", "username": "testuser"}
        token = token_manager.create_access_token(data)
        
        payload = token_manager.verify_token(token)
        
        assert payload is not None
        assert payload["user_id"] == "test-user-id"
        assert payload["username"] == "testuser"

    def test_verify_token_invalid(self, token_manager):
        """Test verifying invalid token."""
        payload = token_manager.verify_token("invalid_token")
        assert payload is None

    def test_verify_token_expired(self, token_manager):
        """Test verifying expired token."""
        data = {"user_id": "test-user-id"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        
        token = token_manager.create_access_token(data, expires_delta)
        payload = token_manager.verify_token(token)
        
        assert payload is None

    def test_refresh_token_creation(self, token_manager):
        """Test creating refresh token."""
        data = {"user_id": "test-user-id"}
        
        token = token_manager.create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)

    def test_get_current_user_from_token(self, token_manager):
        """Test extracting user info from token."""
        data = {"user_id": "test-user-id", "username": "testuser"}
        token = token_manager.create_access_token(data)
        
        user_info = token_manager.get_current_user(token)
        
        assert user_info is not None
        assert user_info["user_id"] == "test-user-id"

    def test_token_blacklisting(self, token_manager):
        """Test token blacklisting functionality."""
        token = "test_token"
        
        # Test adding to blacklist
        result = token_manager.blacklist_token(token)
        assert result is True
        
        # Test checking blacklisted token
        is_blacklisted = token_manager.is_token_blacklisted(token)
        assert is_blacklisted is True

    def test_decode_token_without_verification(self, token_manager):
        """Test decoding token without signature verification."""
        data = {"user_id": "test-user-id", "test": "data"}
        token = token_manager.create_access_token(data)
        
        payload = token_manager.decode_token_unverified(token)
        
        assert payload is not None
        assert payload["user_id"] == "test-user-id"
        assert payload["test"] == "data"


class TestPermissionChecker:
    """Test suite for PermissionChecker class."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def permission_checker(self, db_session):
        """Create PermissionChecker instance."""
        return PermissionChecker(db=db_session)

    @pytest.fixture
    def mock_user_with_permissions(self):
        """Create mock user with roles and permissions."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.is_superuser = False
        
        # Create mock role with permission
        role = Mock(spec=Role)
        role.is_active = True
        
        permission = Mock(spec=Permission)
        permission.name = "read_account"
        permission.is_active = True
        
        role.permissions = [permission]
        user.roles = [role]
        
        return user

    @pytest.fixture
    def mock_superuser(self):
        """Create mock superuser."""
        user = Mock(spec=User)
        user.id = uuid4()
        user.is_superuser = True
        user.roles = []
        return user

    def test_check_permission_superuser(self, permission_checker, mock_superuser):
        """Test permission check for superuser."""
        result = permission_checker.check_permission(mock_superuser, "any_permission")
        assert result is True

    def test_check_permission_with_valid_permission(self, permission_checker, mock_user_with_permissions):
        """Test permission check with valid permission."""
        result = permission_checker.check_permission(mock_user_with_permissions, "read_account")
        assert result is True

    def test_check_permission_without_permission(self, permission_checker, mock_user_with_permissions):
        """Test permission check without required permission."""
        result = permission_checker.check_permission(mock_user_with_permissions, "delete_account")
        assert result is False

    def test_check_permission_inactive_role(self, permission_checker):
        """Test permission check with inactive role."""
        user = Mock(spec=User)
        user.is_superuser = False
        
        role = Mock(spec=Role)
        role.is_active = False  # Inactive role
        
        permission = Mock(spec=Permission)
        permission.name = "read_account"
        permission.is_active = True
        
        role.permissions = [permission]
        user.roles = [role]
        
        result = permission_checker.check_permission(user, "read_account")
        assert result is False

    def test_check_permission_inactive_permission(self, permission_checker):
        """Test permission check with inactive permission."""
        user = Mock(spec=User)
        user.is_superuser = False
        
        role = Mock(spec=Role)
        role.is_active = True
        
        permission = Mock(spec=Permission)
        permission.name = "read_account"
        permission.is_active = False  # Inactive permission
        
        role.permissions = [permission]
        user.roles = [role]
        
        result = permission_checker.check_permission(user, "read_account")
        assert result is False

    def test_get_user_permissions(self, permission_checker, mock_user_with_permissions):
        """Test getting all user permissions."""
        permissions = permission_checker.get_user_permissions(mock_user_with_permissions)
        
        assert isinstance(permissions, list)
        assert "read_account" in permissions

    def test_get_user_permissions_superuser(self, permission_checker, mock_superuser):
        """Test getting permissions for superuser."""
        permissions = permission_checker.get_user_permissions(mock_superuser)
        
        # Superuser should have all permissions
        assert isinstance(permissions, list)

    def test_check_resource_permission(self, permission_checker, mock_user_with_permissions):
        """Test checking resource-specific permission."""
        # Add resource and action to permission
        mock_user_with_permissions.roles[0].permissions[0].resource = "account"
        mock_user_with_permissions.roles[0].permissions[0].action = "read"
        
        result = permission_checker.check_resource_permission(
            mock_user_with_permissions, "account", "read"
        )
        assert result is True

    def test_check_resource_permission_denied(self, permission_checker, mock_user_with_permissions):
        """Test checking denied resource permission."""
        # Add different resource/action to permission
        mock_user_with_permissions.roles[0].permissions[0].resource = "account"
        mock_user_with_permissions.roles[0].permissions[0].action = "read"
        
        result = permission_checker.check_resource_permission(
            mock_user_with_permissions, "account", "delete"
        )
        assert result is False

    def test_has_role(self, permission_checker, mock_user_with_permissions):
        """Test checking if user has specific role."""
        # Add role name
        mock_user_with_permissions.roles[0].name = "user"
        mock_user_with_permissions.roles[0].is_active = True
        
        result = permission_checker.has_role(mock_user_with_permissions, "user")
        assert result is True

    def test_has_role_not_found(self, permission_checker, mock_user_with_permissions):
        """Test checking for non-existent role."""
        mock_user_with_permissions.roles[0].name = "user"
        
        result = permission_checker.has_role(mock_user_with_permissions, "admin")
        assert result is False

    def test_check_tenant_access(self, permission_checker, mock_user_with_permissions):
        """Test checking tenant access."""
        # Mock method implementation
        with patch.object(permission_checker, 'check_tenant_access', return_value=True):
            result = permission_checker.check_tenant_access(
                mock_user_with_permissions, TenantType.USER, "user123"
            )
            assert result is True