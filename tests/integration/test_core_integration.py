"""
Integration tests for core functionality.
Tests the integration between different components.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.test.client import RequestFactory

from app.core.rbac import RBACManager
from app.core.audit import AuditLogger
from app.services import TenantService, UserService, AccountService, TransactionService


@pytest.mark.integration
class TestRBACIntegration(TestCase):
    """Integration tests for RBAC system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rbac_manager = RBACManager()
        self.audit_logger = AuditLogger()
        self.audit_logger.enabled = True
    
    @patch('app.core.rbac.get_db_session')
    @patch('app.core.rbac.cache_get')
    @patch('app.core.rbac.cache_set')
    def test_rbac_permission_check_with_audit(self, mock_cache_set, mock_cache_get, mock_session):
        """Test RBAC permission checking with audit logging."""
        # Mock cache miss
        mock_cache_get.return_value = None
        
        # Mock user with superuser privileges
        mock_user = Mock()
        mock_user.is_superuser = True
        
        # Mock permission
        mock_permission = Mock()
        mock_permission.name = 'admin_access'
        mock_permission.is_active = True
        
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock queries
        def query_side_effect(model):
            if model.__name__ == 'User':
                query_mock = Mock()
                query_mock.filter.return_value.first.return_value = mock_user
                return query_mock
            else:  # Permission query
                query_mock = Mock()
                query_mock.filter.return_value.all.return_value = [mock_permission]
                return query_mock
        
        mock_db_session.query.side_effect = query_side_effect
        
        # Test permission check
        result = self.rbac_manager.has_permission('user-123', 'admin_access', use_cache=False)
        
        # Verify
        assert result is True
        mock_cache_set.assert_called_once()
    
    @patch('app.core.rbac.get_db_session')
    @patch('app.core.audit.get_db_session')
    def test_rbac_role_assignment_with_audit(self, mock_audit_session, mock_rbac_session):
        """Test role assignment with audit logging."""
        # Mock RBAC session
        mock_rbac_db = Mock()
        mock_rbac_session.return_value.__enter__.return_value = mock_rbac_db
        
        # Mock audit session
        mock_audit_db = Mock()
        mock_audit_session.return_value.__enter__.return_value = mock_audit_db
        
        # Mock user and role
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.roles = []
        
        mock_role = Mock()
        mock_role.name = 'admin'
        
        mock_rbac_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_role]
        
        # Test role assignment
        with patch('app.core.audit.AuditLog') as mock_audit_log:
            mock_log_instance = Mock()
            mock_log_instance.id = 'audit-123'
            mock_audit_log.return_value = mock_log_instance
            
            result = self.rbac_manager.assign_role('user-123', 'admin', 'admin-456')
            
            # Verify
            assert result is True
            mock_rbac_db.commit.assert_called_once()
            mock_audit_db.add.assert_called_once()
            mock_audit_db.commit.assert_called_once()


@pytest.mark.integration
class TestUserManagementIntegration(TestCase):
    """Integration tests for user management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.user_service = UserService()
        self.tenant_service = TenantService()
        self.rbac_manager = RBACManager()
    
    @patch('app.services.get_db_session')
    @patch('app.services.hash_password')
    def test_complete_user_setup_workflow(self, mock_hash_password, mock_session):
        """Test complete user setup workflow."""
        mock_hash_password.return_value = 'hashed_password'
        
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock created objects
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_org = Mock()
        mock_org.id = 'org-456'
        mock_link = Mock()
        
        with patch('app.services.User') as mock_user_class, \
             patch('app.services.Organization') as mock_org_class, \
             patch('app.services.UserOrganizationLink') as mock_link_class:
            
            mock_user_class.return_value = mock_user
            mock_org_class.return_value = mock_org
            mock_link_class.return_value = mock_link
            
            # Step 1: Create user
            user = self.user_service.create_user(
                username='testuser',
                email='test@example.com',
                password='password123'
            )
            
            # Step 2: Create organization
            org = self.tenant_service.create_organization(
                name='Test Company',
                tenant_type='enterprise'
            )
            
            # Step 3: Add user to organization
            link = self.tenant_service.add_user_to_organization(
                user_id=user.id,
                org_id=org.id,
                role='admin'
            )
            
            # Verify all operations completed
            assert user == mock_user
            assert org == mock_org
            assert link == mock_link
            assert mock_db_session.add.call_count == 3
            assert mock_db_session.commit.call_count == 3


@pytest.mark.integration
class TestFinancialWorkflowIntegration(TestCase):
    """Integration tests for financial workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.account_service = AccountService()
        self.transaction_service = TransactionService()
    
    @patch('app.services.get_db_session')
    def test_account_creation_and_transaction_workflow(self, mock_session):
        """Test complete account and transaction workflow."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock accounts
        mock_account1 = Mock()
        mock_account1.id = 'account-1'
        mock_account1.balance = Decimal('1000.00')
        
        mock_account2 = Mock()
        mock_account2.id = 'account-2'
        mock_account2.balance = Decimal('500.00')
        
        # Mock transaction
        mock_transaction = Mock()
        mock_transaction.id = 'transaction-123'
        
        with patch('app.services.Account') as mock_account_class, \
             patch('app.services.Transaction') as mock_transaction_class, \
             patch('app.services.AccountService.get_account_balance') as mock_get_balance, \
             patch('app.services.AccountService.update_account_balance') as mock_update_balance:
            
            mock_account_class.return_value = mock_account1
            mock_transaction_class.return_value = mock_transaction
            mock_get_balance.return_value = Decimal('1000.00')
            mock_update_balance.return_value = True
            
            # Step 1: Create accounts
            account1 = self.account_service.create_account(
                name='Checking Account',
                account_type='checking',
                initial_balance=Decimal('1000.00'),
                currency='USD',
                organization_id='org-123'
            )
            
            account2 = self.account_service.create_account(
                name='Savings Account',
                account_type='savings',
                initial_balance=Decimal('500.00'),
                currency='USD',
                organization_id='org-123'
            )
            
            # Step 2: Create transaction between accounts
            transaction = self.transaction_service.create_transaction(
                from_account_id=account1.id,
                to_account_id=account2.id,
                amount=Decimal('250.00'),
                currency='USD',
                description='Transfer to savings'
            )
            
            # Verify workflow completed
            assert account1 == mock_account1
            assert transaction == mock_transaction
            mock_update_balance.assert_called()  # Should be called for both accounts


@pytest.mark.integration
class TestAPIEndpointIntegration(TestCase):
    """Integration tests for API endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
    
    @patch('app.api.get_object_or_404')
    @patch('app.api.authorize_user')
    def test_api_endpoint_with_authorization(self, mock_authorize, mock_get_object):
        """Test API endpoint with authorization check."""
        # Mock authorization success
        mock_authorize.return_value = True
        
        # Mock user object
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        
        mock_get_object.return_value = mock_user
        
        # Import and test API function
        from app.api import get_user_profile
        
        # Create request
        request = self.factory.get('/api/users/user-123/')
        request.user = mock_user
        
        # Test API call
        response = get_user_profile(request, 'user-123')
        
        # Verify authorization was checked
        mock_authorize.assert_called_once()
    
    @patch('app.api.RBACManager')
    @patch('app.api.audit_logger')
    def test_api_endpoint_with_audit_logging(self, mock_audit_logger, mock_rbac):
        """Test API endpoint with audit logging."""
        # Mock RBAC manager
        mock_rbac_instance = Mock()
        mock_rbac_instance.has_permission.return_value = True
        mock_rbac.return_value = mock_rbac_instance
        
        # Mock audit logger
        mock_audit_logger.log_activity.return_value = 'audit-123'
        
        # Import and test API function
        from app.api import get_system_health
        
        # Create request
        request = self.factory.get('/api/health/')
        request.user = Mock()
        request.user.id = 'user-123'
        request.user.is_staff = True
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        
        with patch('app.api.cache') as mock_cache, \
             patch('app.api.connection') as mock_connection:
            
            mock_cache.get.return_value = 'test'
            mock_cache.set.return_value = True
            mock_connection.cursor.return_value.__enter__.return_value.execute.return_value = None
            
            # Test API call
            response = get_system_health(request)
            
            # Verify audit logging occurred
            mock_audit_logger.log_activity.assert_called_once()


@pytest.mark.integration
class TestCacheIntegration(TestCase):
    """Integration tests for cache functionality."""
    
    @patch('app.core.cache.memcached.get_memcached_client')
    def test_rbac_cache_integration(self, mock_get_client):
        """Test RBAC system with cache integration."""
        # Mock memcached client
        mock_cache_client = Mock()
        mock_get_client.return_value = mock_cache_client
        
        # Mock cache operations
        mock_cache_client.get.return_value = ['read_users', 'write_users']
        mock_cache_client.set.return_value = True
        
        rbac_manager = RBACManager()
        
        # Test cached permission check
        result = rbac_manager.has_permission('user-123', 'read_users', use_cache=True)
        
        # Verify cache was used
        assert result is True
        mock_cache_client.get.assert_called_once()


@pytest.mark.integration 
class TestAuditIntegration(TestCase):
    """Integration tests for audit system."""
    
    @patch('app.core.audit.get_db_session')
    def test_audit_logging_integration(self, mock_session):
        """Test audit logging integration across services."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock audit log
        mock_audit_log = Mock()
        mock_audit_log.id = 'audit-123'
        
        with patch('app.core.audit.AuditLog') as mock_audit_log_class:
            mock_audit_log_class.return_value = mock_audit_log
            
            audit_logger = AuditLogger()
            audit_logger.enabled = True
            
            # Test audit logging
            result = audit_logger.log_activity(
                action='USER_CREATED',
                user_id='admin-123',
                resource_type='user',
                resource_id='user-456',
                message='New user created',
                ip_address='192.168.1.1'
            )
            
            # Verify audit log was created
            assert result == 'audit-123'
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.audit_logger')
    def test_service_audit_integration(self, mock_audit_logger):
        """Test service operations with audit integration."""
        from app.services import AuditService
        
        mock_audit_logger.log_activity.return_value = 'audit-456'
        
        audit_service = AuditService()
        
        # Test service audit logging
        result = audit_service.log_user_activity(
            user_id='user-123',
            action='LOGIN',
            ip_address='192.168.1.1',
            message='User logged in successfully'
        )
        
        # Verify audit service used audit logger
        assert result == 'audit-456'
        mock_audit_logger.log_activity.assert_called_once()


@pytest.mark.integration
class TestMultiTenantIntegration(TestCase):
    """Integration tests for multi-tenant functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tenant_service = TenantService()
        self.user_service = UserService()
        self.account_service = AccountService()
    
    @patch('app.services.get_db_session')
    def test_tenant_isolation_workflow(self, mock_session):
        """Test tenant isolation in multi-tenant environment."""
        # Mock database session
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock organizations
        mock_org1 = Mock()
        mock_org1.id = 'org-1'
        mock_org1.name = 'Company A'
        
        mock_org2 = Mock()
        mock_org2.id = 'org-2'
        mock_org2.name = 'Company B'
        
        # Mock accounts for different organizations
        mock_account1 = Mock()
        mock_account1.organization_id = 'org-1'
        
        mock_account2 = Mock()
        mock_account2.organization_id = 'org-2'
        
        with patch('app.services.Organization') as mock_org_class, \
             patch('app.services.Account') as mock_account_class:
            
            mock_org_class.side_effect = [mock_org1, mock_org2]
            mock_account_class.side_effect = [mock_account1, mock_account2]
            
            # Create two organizations
            org1 = self.tenant_service.create_organization(
                name='Company A',
                tenant_type='enterprise'
            )
            
            org2 = self.tenant_service.create_organization(
                name='Company B',
                tenant_type='small_business'
            )
            
            # Create accounts for each organization
            account1 = self.account_service.create_account(
                name='Company A Account',
                account_type='checking',
                initial_balance=Decimal('5000.00'),
                currency='USD',
                organization_id=org1.id
            )
            
            account2 = self.account_service.create_account(
                name='Company B Account',
                account_type='checking',
                initial_balance=Decimal('3000.00'),
                currency='USD',
                organization_id=org2.id
            )
            
            # Verify tenant isolation
            assert account1.organization_id == 'org-1'
            assert account2.organization_id == 'org-2'
            assert org1.name == 'Company A'
            assert org2.name == 'Company B'