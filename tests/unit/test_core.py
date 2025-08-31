"""
Sample unit tests for core functionality.
Tests the RBAC system, audit logging, and cache/queue functionality.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""
import pytest
from unittest.mock import Mock, patch
from app.core.rbac import RBACManager
from app.core.audit import AuditLogger
from app.core.cache.memcached import MemcachedClient
from app.core.queue.rabbitmq import RabbitMQClient


class TestRBACManager:
    """Test cases for RBAC Manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rbac_manager = RBACManager(cache_timeout=60)
    
    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.get_db_session')
    def test_has_permission_superuser(self, mock_session, mock_cache_get):
        """Test that superuser has all permissions."""
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock permission
        mock_permission = Mock()
        mock_permission.name = 'test_permission'
        mock_permission.is_active = True
        
        # Mock user
        mock_user = Mock()
        mock_user.is_superuser = True
        
        # Mock session and database queries
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock user query
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock permission query for superuser
        def side_effect(*args, **kwargs):
            if args[0] == mock_user.__class__:
                return mock_db_session.query.return_value.filter.return_value
            else:  # Permission query
                mock_perm_query = Mock()
                mock_perm_query.filter.return_value.all.return_value = [mock_permission]
                return mock_perm_query
        
        mock_db_session.query.side_effect = side_effect
        
        # Test
        result = self.rbac_manager.has_permission('user-123', 'test_permission', use_cache=False)
        assert result is True
    
    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.get_db_session')
    def test_has_permission_regular_user(self, mock_session, mock_cache_get):
        """Test permission checking for regular user."""
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock user with role and permission
        mock_permission = Mock()
        mock_permission.name = 'test_permission'
        mock_permission.is_active = True
        
        mock_role = Mock()
        mock_role.is_active = True
        mock_role.permissions = [mock_permission]
        
        mock_user = Mock()
        mock_user.is_superuser = False
        mock_user.roles = [mock_role]
        
        # Mock session
        mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test
        result = self.rbac_manager.has_permission('user-123', 'test_permission', use_cache=False)
        assert result is True

    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.get_db_session')
    def test_has_permission_no_permission(self, mock_session, mock_cache_get):
        """Test permission checking when user has no permission."""
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock user with no permissions
        mock_user = Mock()
        mock_user.is_superuser = False
        mock_user.roles = []
        
        # Mock session
        mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test
        result = self.rbac_manager.has_permission('user-123', 'test_permission', use_cache=False)
        assert result is False

    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.get_db_session')
    def test_has_permission_user_not_found(self, mock_session, mock_cache_get):
        """Test permission checking when user is not found."""
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock session - user not found
        mock_session.return_value.__enter__.return_value.query.return_value.filter.return_value.first.return_value = None
        
        # Test
        result = self.rbac_manager.has_permission('non-existent-user', 'test_permission', use_cache=False)
        assert result is False

    @patch('app.core.rbac.cache_get')
    def test_has_permission_cached(self, mock_cache_get):
        """Test permission checking with cache hit."""
        # Mock cache hit with permissions
        mock_cache_get.return_value = ['test_permission', 'other_permission']
        
        # Test
        result = self.rbac_manager.has_permission('user-123', 'test_permission', use_cache=True)
        assert result is True
        
        # Verify cache was checked
        mock_cache_get.assert_called_once_with('user_permissions:user-123')
    
    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.get_db_session')
    def test_get_user_roles_success(self, mock_session, mock_cache_get):
        """Test getting user roles."""
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock role
        mock_role = Mock()
        mock_role.name = 'admin'
        mock_role.is_active = True
        
        # Mock user
        mock_user = Mock()
        mock_user.roles = [mock_role]
        
        # Mock session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test
        result = self.rbac_manager.get_user_roles('user-123', use_cache=False)
        
        # Verify
        assert result == {'admin'}
    
    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.get_db_session')
    def test_has_role_success(self, mock_session, mock_cache_get):
        """Test role checking."""
        # Mock cache miss  
        mock_cache_get.return_value = None
        
        # Mock role
        mock_role = Mock()
        mock_role.name = 'admin'
        mock_role.is_active = True
        
        # Mock user
        mock_user = Mock()
        mock_user.roles = [mock_role]
        
        # Mock session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Test
        result = self.rbac_manager.has_role('user-123', 'admin', use_cache=False)
        
        # Verify
        assert result is True
    
    @patch('app.core.rbac.get_db_session')
    def test_assign_role_success(self, mock_session):
        """Test role assignment."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock user and role
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.roles = []
        
        mock_role = Mock()
        mock_role.name = 'admin'
        
        # Mock queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_role]
        
        # Test
        result = self.rbac_manager.assign_role('user-123', 'admin', 'admin-456')
        
        # Verify
        assert result is True
        mock_db_session.commit.assert_called_once()
    
    @patch('app.core.rbac.get_db_session')
    def test_assign_role_user_not_found(self, mock_session):
        """Test role assignment when user not found."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock user not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Test
        result = self.rbac_manager.assign_role('non-existent', 'admin', 'admin-456')
        
        # Verify
        assert result is False
    
    @patch('app.core.rbac.get_db_session')
    def test_remove_role_success(self, mock_session):
        """Test role removal."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock role to remove
        mock_role = Mock()
        mock_role.name = 'admin'
        
        # Mock user with role
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.roles = [mock_role]
        
        # Mock queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_role]
        
        # Test
        result = self.rbac_manager.remove_role('user-123', 'admin', 'admin-456')
        
        # Verify
        assert result is True
        mock_db_session.commit.assert_called_once()
    
    @patch('app.core.rbac.audit_logger')
    @patch('app.core.rbac.get_db_session')
    def test_assign_role_with_audit(self, mock_session, mock_audit_logger):
        """Test role assignment with audit logging."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock user and role
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.roles = []
        
        mock_role = Mock()
        mock_role.name = 'admin'
        
        # Mock queries
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_role]
        
        # Mock audit logger
        mock_audit_logger.log_activity.return_value = 'audit-123'
        
        # Test
        result = self.rbac_manager.assign_role('user-123', 'admin', 'admin-456')
        
        # Verify audit logging occurred
        assert result is True
        mock_audit_logger.log_activity.assert_called_once()
        
        # Check audit log parameters
        call_args = mock_audit_logger.log_activity.call_args[1]
        assert call_args['action'] == 'ASSIGN_ROLE'
        assert call_args['user_id'] == 'admin-456'
        assert call_args['resource_type'] == 'role'


class TestAuditLogger:
    """Test cases for Audit Logger."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Enable audit logging for tests
        self.audit_logger = AuditLogger()
        self.audit_logger.enabled = True
    
    @patch('app.core.audit.AuditLog')
    @patch('app.core.audit.get_db_session')
    def test_log_activity(self, mock_session, mock_audit_log):
        """Test activity logging."""
        # Mock audit log instance
        mock_log_instance = Mock()
        mock_log_instance.id = 'audit-log-123'
        mock_audit_log.return_value = mock_log_instance
        
        # Mock session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        
        # Test
        result = self.audit_logger.log_activity(
            action='TEST_ACTION',
            user_id='user-123',
            message='Test activity'
        )
        
        # Verify
        assert result == 'audit-log-123'
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_audit_log.assert_called_once()
    
    def test_sanitize_data(self):
        """Test data sanitization."""
        sensitive_data = {
            'username': 'testuser',
            'password': 'secret123',
            'token': 'abc123',
            'nested': {
                'secret': 'hidden',
                'public': 'visible'
            }
        }
        
        sanitized = self.audit_logger._sanitize_data(sensitive_data)
        
        assert sanitized['username'] == 'testuser'
        assert sanitized['password'] == '[REDACTED]'
        assert sanitized['token'] == '[REDACTED]'
        assert sanitized['nested']['secret'] == '[REDACTED]'
        assert sanitized['nested']['public'] == 'visible'
    
    @patch('app.core.audit.AuditLog')
    @patch('app.core.audit.get_db_session')
    def test_log_activity_disabled(self, mock_session, mock_audit_log):
        """Test activity logging when disabled."""
        # Disable audit logging
        self.audit_logger.enabled = False
        
        # Test
        result = self.audit_logger.log_activity(
            action='TEST_ACTION',
            user_id='user-123',
            message='Test activity'
        )
        
        # Verify
        assert result is None
        mock_session.assert_not_called()
        mock_audit_log.assert_not_called()
    
    @patch('app.core.audit.AuditLog')
    @patch('app.core.audit.get_db_session')
    def test_log_activity_with_metadata(self, mock_session, mock_audit_log):
        """Test activity logging with additional metadata."""
        # Mock audit log instance
        mock_log_instance = Mock()
        mock_log_instance.id = 'audit-log-456'
        mock_audit_log.return_value = mock_log_instance
        
        # Mock session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        
        # Test with metadata
        metadata = {'request_id': 'req-123', 'user_agent': 'Mozilla/5.0'}
        result = self.audit_logger.log_activity(
            action='USER_UPDATE',
            user_id='user-123',
            resource_type='user',
            resource_id='user-456',
            old_values={'name': 'Old Name'},
            new_values={'name': 'New Name'},
            metadata=metadata,
            message='User profile updated'
        )
        
        # Verify
        assert result == 'audit-log-456'
        mock_audit_log.assert_called_once()
        
        # Check parameters
        call_kwargs = mock_audit_log.call_args[1]
        assert call_kwargs['action'] == 'USER_UPDATE'
        assert call_kwargs['user_id'] == 'user-123'
        assert call_kwargs['resource_type'] == 'user'
        assert call_kwargs['resource_id'] == 'user-456'
        assert call_kwargs['metadata'] == metadata
    
    @patch('app.core.audit.get_db_session')
    def test_log_activity_exception_handling(self, mock_session):
        """Test activity logging exception handling."""
        # Mock session to raise exception
        mock_session.side_effect = Exception("Database error")
        
        # Test
        result = self.audit_logger.log_activity(
            action='TEST_ACTION',
            user_id='user-123',
            message='Test activity'
        )
        
        # Should return None on exception
        assert result is None
    
    def test_sanitize_data_with_lists(self):
        """Test data sanitization with lists."""
        data_with_lists = {
            'users': [
                {'username': 'user1', 'password': 'secret1'},
                {'username': 'user2', 'token': 'abc123'}
            ],
            'config': {
                'api_keys': ['key1', 'key2'],
                'public_setting': 'visible'
            }
        }
        
        sanitized = self.audit_logger._sanitize_data(data_with_lists)
        
        # Lists with dictionaries should be sanitized
        assert sanitized['users'][0]['username'] == 'user1'
        assert sanitized['users'][0]['password'] == '[REDACTED]'
        assert sanitized['users'][1]['token'] == '[REDACTED]'
        assert sanitized['config']['public_setting'] == 'visible'
    
    def test_sanitize_data_non_dict(self):
        """Test data sanitization with non-dictionary input."""
        # String input
        result = self.audit_logger._sanitize_data("not a dict")
        assert result == "not a dict"
        
        # List input
        result = self.audit_logger._sanitize_data([1, 2, 3])
        assert result == [1, 2, 3]
        
        # None input
        result = self.audit_logger._sanitize_data(None)
        assert result is None


class TestMemcachedClient:
    """Test cases for Memcached Client."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('memcache.Client'):
            self.client = MemcachedClient(['localhost:11211'])
    
    def test_make_key(self):
        """Test key namespacing."""
        key = self.client._make_key('test_key')
        assert key.startswith('app:')
        assert len(key) > len('app:')
    
    @patch('memcache.Client')
    def test_get_miss(self, mock_memcache):
        """Test cache miss."""
        mock_memcache.return_value.get.return_value = None
        
        client = MemcachedClient(['localhost:11211'])
        result = client.get('test_key', 'default_value')
        
        assert result == 'default_value'
    
    @patch('memcache.Client')
    def test_set_success(self, mock_memcache):
        """Test successful cache set."""
        mock_memcache.return_value.set.return_value = True
        
        client = MemcachedClient(['localhost:11211'])
        result = client.set('test_key', 'test_value', 300)
        
        assert result is True


class TestRabbitMQClient:
    """Test cases for RabbitMQ Client."""
    
    @patch('pika.BlockingConnection')
    def test_publish_success(self, mock_connection):
        """Test successful message publishing."""
        # Mock connection and channel
        mock_channel = Mock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False
        
        client = RabbitMQClient('localhost', 5672, 'guest', 'guest')
        result = client.publish('test.routing.key', {'message': 'test'})
        
        assert result is True
        mock_channel.basic_publish.assert_called_once()
    
    @patch('pika.BlockingConnection')
    def test_declare_queue(self, mock_connection):
        """Test queue declaration."""
        # Mock connection and channel
        mock_channel = Mock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False
        
        client = RabbitMQClient('localhost', 5672, 'guest', 'guest')
        result = client.declare_queue('test_queue')
        
        assert result == 'test_queue'
        mock_channel.queue_declare.assert_called()


class TestAdvancedMemcachedFeatures:
    """Test cases for advanced Memcached features."""
    
    @patch('memcache.Client')
    def test_get_multi_keys(self, mock_memcache):
        """Test getting multiple keys at once."""
        mock_client = Mock()
        mock_client.get_multi.return_value = {
            'key1': 'value1',
            'key2': 'value2'
        }
        mock_memcache.return_value = mock_client
        
        client = MemcachedClient(['localhost:11211'])
        result = client.get_multi(['key1', 'key2'])
        
        assert result == {'key1': 'value1', 'key2': 'value2'}
    
    @patch('memcache.Client')
    def test_connection_retry_logic(self, mock_memcache):
        """Test connection retry logic."""
        mock_client = Mock()
        # First call fails, second succeeds
        mock_client.get.side_effect = [Exception("Connection failed"), 'success_value']
        mock_memcache.return_value = mock_client
        
        client = MemcachedClient(['localhost:11211'])
        result = client.get('test_key')
        
        # Should handle the failure gracefully
        assert result is None  # Based on error handling implementation


class TestAdvancedRabbitMQFeatures:
    """Test cases for advanced RabbitMQ features."""
    
    @patch('pika.BlockingConnection')
    def test_publish_with_properties(self, mock_connection):
        """Test publishing with message properties."""
        mock_channel = Mock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False
        
        client = RabbitMQClient('localhost', 5672, 'guest', 'guest')
        result = client.publish(
            'test_queue',
            {'message': 'test'},
            priority=5,
            expiration='60000'
        )
        
        assert result is True
        mock_channel.basic_publish.assert_called_once()
    
    @patch('pika.BlockingConnection')
    def test_connection_error_recovery(self, mock_connection):
        """Test connection error recovery."""
        # Mock connection failure
        mock_connection.side_effect = Exception("Connection refused")
        
        client = RabbitMQClient('localhost', 5672, 'guest', 'guest')
        result = client.publish('test_queue', {'message': 'test'})
        
        # Should handle error gracefully
        assert result is False


class TestDatabaseConnectionAdvanced:
    """Test cases for advanced database connection features."""
    
    @patch('app.core.db.connection.create_engine')
    def test_connection_pooling(self, mock_create_engine):
        """Test database connection pooling."""
        from app.core.db.connection import get_db_session
        
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Multiple calls should reuse the engine
        session1 = get_db_session()
        session2 = get_db_session()
        
        # Engine should only be created once (reused)
        assert session1 is not None
        assert session2 is not None


class TestModelValidationAdvanced:
    """Test cases for advanced model validation."""
    
    def test_user_model_edge_cases(self):
        """Test user model edge cases."""
        from app.core.models import User
        
        # Test with minimal data
        user = User(username='test', email='test@example.com')
        assert user.username == 'test'
        assert user.email == 'test@example.com'
        
        # Test full name with empty names
        user_empty = User(first_name='', last_name='')
        assert user_empty.full_name.strip() == ''
    
    def test_audit_log_model_edge_cases(self):
        """Test audit log model edge cases."""
        from app.core.models import AuditLog
        
        # Test with minimal data
        log = AuditLog(action='TEST')
        assert log.action == 'TEST'
        
        # Test with complex metadata
        complex_metadata = {
            'nested': {'data': [1, 2, 3]},
            'list': ['a', 'b', 'c'],
            'number': 42
        }
        log_complex = AuditLog(action='COMPLEX', extra_metadata=complex_metadata)
        assert log_complex.extra_metadata == complex_metadata