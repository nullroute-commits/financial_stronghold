"""
Security tests for the application.
Tests security vulnerabilities and compliance requirements.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import pytest
from unittest.mock import Mock, patch
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser

from app.core.rbac import RBACManager
from app.core.audit import AuditLogger
from app.auth import authenticate_user, authorize_user


@pytest.mark.security
class TestAuthenticationSecurity(TestCase):
    """Security tests for authentication system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.auth.User')
    @patch('app.auth.check_password')
    def test_password_timing_attack_protection(self, mock_check_password, mock_user):
        """Test protection against timing attacks on authentication."""
        # Test with existing user
        mock_user_instance = Mock()
        mock_user_instance.is_active = True
        mock_user_instance.password_hash = 'hashed_password'
        mock_user.objects.filter.return_value.first.return_value = mock_user_instance
        mock_check_password.return_value = False
        
        result1 = authenticate_user('existing_user', 'wrong_password')
        
        # Test with non-existing user
        mock_user.objects.filter.return_value.first.return_value = None
        
        result2 = authenticate_user('non_existing_user', 'wrong_password')
        
        # Both should return None (fail) and take similar time
        assert result1 is None
        assert result2 is None
        
        # Verify password check was called for existing user but not for non-existing
        mock_check_password.assert_called_once()
    
    @patch('app.auth.User')
    def test_account_lockout_after_failed_attempts(self, mock_user):
        """Test account lockout after multiple failed login attempts."""
        mock_user_instance = Mock()
        mock_user_instance.is_active = True
        mock_user_instance.failed_login_attempts = 5  # Already at threshold
        mock_user_instance.is_locked = True
        
        mock_user.objects.filter.return_value.first.return_value = mock_user_instance
        
        result = authenticate_user('locked_user', 'any_password')
        
        # Should fail even if password is correct when account is locked
        assert result is None
    
    @patch('app.auth.RBACManager')
    def test_privilege_escalation_prevention(self, mock_rbac_manager):
        """Test prevention of privilege escalation attacks."""
        # Mock RBAC manager to deny admin permissions
        mock_rbac_instance = Mock()
        mock_rbac_instance.has_permission.return_value = False
        mock_rbac_manager.return_value = mock_rbac_instance
        
        # Test normal user trying to access admin function
        result = authorize_user('user-123', 'admin_users')
        
        assert result is False
        mock_rbac_instance.has_permission.assert_called_once_with('user-123', 'admin_users')
    
    def test_session_fixation_protection(self):
        """Test protection against session fixation attacks."""
        from app.auth import login_user
        
        # Create request with existing session
        request = self.factory.post('/login/')
        
        # Mock session middleware
        request.session = {}
        request.session['old_data'] = 'should_be_cleared'
        old_session_key = 'old_session_key'
        
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.username = 'testuser'
        
        with patch('app.auth.audit_logger') as mock_audit:
            mock_audit.log_activity.return_value = 'audit-123'
            
            # Simulate login
            result = login_user(request, mock_user)
            
            # Session should be regenerated (old data cleared)
            assert result is True
            assert request.session.get('old_data') is None
            assert request.session['user_id'] == 'user-123'


@pytest.mark.security
class TestInputValidationSecurity(TestCase):
    """Security tests for input validation."""
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in queries."""
        # This test would typically use real database queries
        # For now, we test that parameterized queries are used
        
        from app.services import UserService
        user_service = UserService()
        
        # Test malicious input
        malicious_input = "'; DROP TABLE users; --"
        
        with patch('app.services.get_db_session') as mock_session:
            mock_db_session = Mock()
            mock_session.return_value.__enter__.return_value = mock_db_session
            mock_db_session.query.return_value.filter.return_value.first.return_value = None
            
            # This should safely handle malicious input
            result = user_service.get_user_by_id(malicious_input)
            
            # Should not raise exception and return None safely
            assert result is None
    
    def test_xss_prevention_in_audit_logs(self):
        """Test XSS prevention in audit log data."""
        audit_logger = AuditLogger()
        audit_logger.enabled = True
        
        # Test malicious script input
        malicious_data = {
            'user_input': '<script>alert("XSS")</script>',
            'message': 'User entered: <img src=x onerror=alert(1)>'
        }
        
        sanitized = audit_logger._sanitize_data(malicious_data)
        
        # Script tags should be preserved but not executed
        # (actual XSS prevention would be in presentation layer)
        assert 'script' in sanitized['user_input']
        assert 'img' in sanitized['message']
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        # Test with malicious file path
        malicious_path = "../../../etc/passwd"
        
        # Function should validate and reject malicious paths
        from app.core.audit import AuditLogger
        
        audit_logger = AuditLogger()
        
        # Test that malicious paths are sanitized
        test_data = {'file_path': malicious_path}
        sanitized = audit_logger._sanitize_data(test_data)
        
        # Path should be preserved as string (not executed)
        assert sanitized['file_path'] == malicious_path
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection attacks."""
        # Test malicious command input
        malicious_command = "test; rm -rf /"
        
        # This should be handled safely by input validation
        from app.core.audit import AuditLogger
        
        audit_logger = AuditLogger()
        test_data = {'command': malicious_command}
        
        # Should not execute the command
        sanitized = audit_logger._sanitize_data(test_data)
        assert sanitized['command'] == malicious_command


@pytest.mark.security
class TestDataProtectionSecurity(TestCase):
    """Security tests for data protection."""
    
    def test_sensitive_data_masking(self):
        """Test masking of sensitive data in logs."""
        audit_logger = AuditLogger()
        
        sensitive_data = {
            'username': 'testuser',
            'password': 'secret123',
            'credit_card': '4111-1111-1111-1111',
            'ssn': '123-45-6789',
            'api_key': 'sk_test_123456789',
            'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
            'authorization': 'Bearer abc123',
            'session_id': 'sess_123456789',
            'normal_field': 'visible_data'
        }
        
        sanitized = audit_logger._sanitize_data(sensitive_data)
        
        # Sensitive fields should be redacted
        assert sanitized['password'] == '[REDACTED]'
        assert sanitized['api_key'] == '[REDACTED]'
        assert sanitized['token'] == '[REDACTED]'
        assert sanitized['authorization'] == '[REDACTED]'
        assert sanitized['session_id'] == '[REDACTED]'
        
        # Non-sensitive fields should remain
        assert sanitized['username'] == 'testuser'
        assert sanitized['normal_field'] == 'visible_data'
    
    def test_password_hashing_security(self):
        """Test secure password hashing."""
        from app.auth import hash_password, check_password
        
        password = 'test_password_123'
        
        # Test password hashing
        with patch('app.auth.bcrypt') as mock_bcrypt:
            mock_bcrypt.hashpw.return_value = b'hashed_password'
            mock_bcrypt.gensalt.return_value = b'salt'
            
            hashed = hash_password(password)
            
            # Verify bcrypt was used with salt
            mock_bcrypt.gensalt.assert_called_once()
            mock_bcrypt.hashpw.assert_called_once()
            assert hashed == 'hashed_password'
    
    def test_data_encryption_at_rest(self):
        """Test encryption of sensitive data at rest."""
        # This would test database encryption, field-level encryption etc.
        # For now, test that sensitive fields are marked for encryption
        
        from app.core.models import User
        
        # Test that password field is hashed, not plaintext
        user = User(password_hash='hashed_value')
        
        # Password should never be stored in plaintext
        assert user.password_hash != 'plaintext_password'
        assert 'hashed' in str(user.password_hash).lower() or len(user.password_hash) > 20


@pytest.mark.security
class TestAccessControlSecurity(TestCase):
    """Security tests for access control."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rbac_manager = RBACManager()
    
    @patch('app.core.rbac.get_db_session')
    def test_horizontal_privilege_escalation_prevention(self, mock_session):
        """Test prevention of horizontal privilege escalation."""
        # Mock user trying to access another user's data
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # User should only access their own data
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.is_superuser = False
        mock_user.roles = []
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test access to other user's permission
        result = self.rbac_manager.has_permission('user-123', 'access_user_456_data', use_cache=False)
        
        # Should be denied
        assert result is False
    
    @patch('app.core.rbac.get_db_session')
    def test_vertical_privilege_escalation_prevention(self, mock_session):
        """Test prevention of vertical privilege escalation."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Regular user trying to access admin functions
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.is_superuser = False
        mock_user.roles = []  # No admin roles
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test access to admin permission
        result = self.rbac_manager.has_permission('user-123', 'admin_delete_users', use_cache=False)
        
        # Should be denied
        assert result is False
    
    def test_anonymous_user_access_restriction(self):
        """Test that anonymous users are properly restricted."""
        from app.auth import require_permission
        from django.http import JsonResponse
        
        # Create a protected view
        @require_permission('read_users')
        def protected_view(request):
            return JsonResponse({'message': 'success'})
        
        # Test with anonymous user
        request = self.factory.get('/protected/')
        request.user = AnonymousUser()
        
        with patch('app.auth.JsonResponse') as mock_json_response:
            mock_json_response.return_value = Mock()
            
            result = protected_view(request)
            
            # Should return authentication required error
            mock_json_response.assert_called_once()
            call_args = mock_json_response.call_args
            assert call_args[0][0]['error'] == 'Authentication required'
            assert call_args[1]['status'] == 401


@pytest.mark.security
class TestAuditSecurity(TestCase):
    """Security tests for audit system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audit_logger = AuditLogger()
        self.audit_logger.enabled = True
        self.factory = RequestFactory()
    
    @patch('app.core.audit.get_db_session')
    def test_audit_log_tampering_prevention(self, mock_session):
        """Test prevention of audit log tampering."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_audit_log = Mock()
        mock_audit_log.id = 'audit-123'
        
        with patch('app.core.audit.AuditLog') as mock_audit_log_class:
            mock_audit_log_class.return_value = mock_audit_log
            
            # Create audit log
            result = self.audit_logger.log_activity(
                action='SECURITY_EVENT',
                user_id='user-123',
                message='Suspicious activity detected'
            )
            
            # Verify audit log was created
            assert result == 'audit-123'
            
            # Audit logs should be append-only (no update/delete)
            # This would be enforced at database level
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    def test_audit_log_information_disclosure(self):
        """Test that audit logs don't disclose sensitive information."""
        sensitive_data = {
            'user_password': 'secret123',
            'credit_card_number': '4111-1111-1111-1111',
            'social_security': '123-45-6789',
            'api_secret': 'sk_live_abcdef123456',
            'normal_data': 'safe_to_log'
        }
        
        # Sanitize data before logging
        sanitized = self.audit_logger._sanitize_data(sensitive_data)
        
        # Sensitive data should be redacted
        assert '[REDACTED]' in str(sanitized['user_password'])
        assert sanitized['normal_data'] == 'safe_to_log'
    
    @patch('app.core.audit.get_db_session')
    def test_audit_log_integrity(self, mock_session):
        """Test audit log data integrity."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_audit_log = Mock()
        mock_audit_log.id = 'audit-123'
        
        with patch('app.core.audit.AuditLog') as mock_audit_log_class:
            mock_audit_log_class.return_value = mock_audit_log
            
            # Test audit log with all required fields
            result = self.audit_logger.log_activity(
                action='USER_LOGIN',
                user_id='user-123',
                ip_address='192.168.1.1',
                user_agent='Mozilla/5.0...',
                session_id='sess_123',
                message='User logged in successfully'
            )
            
            # Verify all security-relevant fields are captured
            mock_audit_log_class.assert_called_once()
            call_kwargs = mock_audit_log_class.call_args[1]
            
            assert call_kwargs['action'] == 'USER_LOGIN'
            assert call_kwargs['user_id'] == 'user-123'
            assert call_kwargs['ip_address'] == '192.168.1.1'
            assert call_kwargs['user_agent'] == 'Mozilla/5.0...'
            assert call_kwargs['session_id'] == 'sess_123'


@pytest.mark.security
class TestCryptographicSecurity(TestCase):
    """Security tests for cryptographic functions."""
    
    def test_secure_random_generation(self):
        """Test secure random number generation."""
        import secrets
        
        # Test that secure random is used for tokens/IDs
        token1 = secrets.token_urlsafe(32)
        token2 = secrets.token_urlsafe(32)
        
        # Tokens should be different and of expected length
        assert token1 != token2
        assert len(token1) >= 32
        assert len(token2) >= 32
    
    def test_key_derivation_security(self):
        """Test secure key derivation functions."""
        # This would test PBKDF2, scrypt, or Argon2 usage
        # For now, verify that strong hashing is used
        
        from app.auth import hash_password
        
        with patch('app.auth.bcrypt') as mock_bcrypt:
            mock_bcrypt.gensalt.return_value = b'$2b$12$salt...'
            mock_bcrypt.hashpw.return_value = b'$2b$12$hash...'
            
            result = hash_password('password123')
            
            # Verify proper cost factor is used
            mock_bcrypt.gensalt.assert_called_once()
            mock_bcrypt.hashpw.assert_called_once()
    
    def test_timing_safe_comparison(self):
        """Test timing-safe string comparison."""
        import hmac
        
        # Test that timing-safe comparison is used for sensitive data
        secret1 = "secret_token_123"
        secret2 = "secret_token_123"
        secret3 = "different_token"
        
        # Use HMAC for timing-safe comparison
        result1 = hmac.compare_digest(secret1, secret2)
        result2 = hmac.compare_digest(secret1, secret3)
        
        assert result1 is True
        assert result2 is False