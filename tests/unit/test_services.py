"""
Unit tests for service functionality.
Tests the business logic services.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.services import (
    TenantService,
    UserService,
    AccountService,
    TransactionService,
    BudgetService,
    AuditService,
)


class TestTenantService:
    """Test cases for Tenant Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tenant_service = TenantService()
    
    @patch('app.services.get_db_session')
    def test_create_organization_success(self, mock_session):
        """Test successful organization creation."""
        # Mock session and organization
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_org = Mock()
        mock_org.id = 'org-123'
        
        with patch('app.services.Organization') as mock_org_class:
            mock_org_class.return_value = mock_org
            
            result = self.tenant_service.create_organization(
                name='Test Company',
                tenant_type='enterprise',
                description='A test company'
            )
            
            assert result == mock_org
            mock_db_session.add.assert_called_once_with(mock_org)
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_add_user_to_organization_success(self, mock_session):
        """Test successfully adding user to organization."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_link = Mock()
        
        with patch('app.services.UserOrganizationLink') as mock_link_class:
            mock_link_class.return_value = mock_link
            
            result = self.tenant_service.add_user_to_organization(
                user_id='user-123',
                org_id='org-456',
                role='admin'
            )
            
            assert result == mock_link
            mock_db_session.add.assert_called_once_with(mock_link)
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_get_user_organizations(self, mock_session):
        """Test getting user organizations."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock organizations
        mock_org1 = Mock()
        mock_org1.name = 'Company A'
        mock_org2 = Mock()
        mock_org2.name = 'Company B'
        
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_org1, mock_org2
        ]
        
        result = self.tenant_service.get_user_organizations('user-123')
        
        assert len(result) == 2
        assert result[0].name == 'Company A'
        assert result[1].name == 'Company B'


class TestUserService:
    """Test cases for User Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.user_service = UserService()
    
    @patch('app.services.get_db_session')
    @patch('app.services.hash_password')
    def test_create_user_success(self, mock_hash_password, mock_session):
        """Test successful user creation."""
        mock_hash_password.return_value = 'hashed_password'
        
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_user = Mock()
        mock_user.id = 'user-123'
        
        with patch('app.services.User') as mock_user_class:
            mock_user_class.return_value = mock_user
            
            result = self.user_service.create_user(
                username='testuser',
                email='test@example.com',
                password='password123',
                first_name='Test',
                last_name='User'
            )
            
            assert result == mock_user
            mock_hash_password.assert_called_once_with('password123')
            mock_db_session.add.assert_called_once_with(mock_user)
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_get_user_by_id_success(self, mock_session):
        """Test successful user retrieval by ID."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_user = Mock()
        mock_user.id = 'user-123'
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = self.user_service.get_user_by_id('user-123')
        
        assert result == mock_user
    
    @patch('app.services.get_db_session')
    def test_get_user_by_id_not_found(self, mock_session):
        """Test user retrieval when user not found."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = self.user_service.get_user_by_id('non-existent')
        
        assert result is None
    
    @patch('app.services.get_db_session')
    def test_update_user_success(self, mock_session):
        """Test successful user update."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_user = Mock()
        mock_user.id = 'user-123'
        mock_user.email = 'old@example.com'
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        update_data = {'email': 'new@example.com', 'first_name': 'Updated'}
        result = self.user_service.update_user('user-123', update_data)
        
        assert result == mock_user
        assert mock_user.email == 'new@example.com'
        assert mock_user.first_name == 'Updated'
        mock_db_session.commit.assert_called_once()


class TestAccountService:
    """Test cases for Account Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.account_service = AccountService()
    
    @patch('app.services.get_db_session')
    def test_create_account_success(self, mock_session):
        """Test successful account creation."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_account = Mock()
        mock_account.id = 'account-123'
        
        with patch('app.services.Account') as mock_account_class:
            mock_account_class.return_value = mock_account
            
            result = self.account_service.create_account(
                name='Checking Account',
                account_type='checking',
                initial_balance=Decimal('1000.00'),
                currency='USD',
                organization_id='org-123'
            )
            
            assert result == mock_account
            mock_db_session.add.assert_called_once_with(mock_account)
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_get_account_balance(self, mock_session):
        """Test getting account balance."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_account = Mock()
        mock_account.balance = Decimal('1500.00')
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_account
        
        result = self.account_service.get_account_balance('account-123')
        
        assert result == Decimal('1500.00')
    
    @patch('app.services.get_db_session')
    def test_update_account_balance(self, mock_session):
        """Test updating account balance."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_account = Mock()
        mock_account.balance = Decimal('1000.00')
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_account
        
        result = self.account_service.update_account_balance(
            'account-123',
            Decimal('250.00'),
            'credit'
        )
        
        assert result is True
        assert mock_account.balance == Decimal('1250.00')
        mock_db_session.commit.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_get_organization_accounts(self, mock_session):
        """Test getting organization accounts."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_account1 = Mock()
        mock_account1.name = 'Checking'
        mock_account2 = Mock()
        mock_account2.name = 'Savings'
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_account1, mock_account2
        ]
        
        result = self.account_service.get_organization_accounts('org-123')
        
        assert len(result) == 2
        assert result[0].name == 'Checking'
        assert result[1].name == 'Savings'


class TestTransactionService:
    """Test cases for Transaction Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transaction_service = TransactionService()
    
    @patch('app.services.AccountService')
    @patch('app.services.get_db_session')
    def test_create_transaction_success(self, mock_session, mock_account_service):
        """Test successful transaction creation."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        # Mock account service
        mock_account_service_instance = Mock()
        mock_account_service.return_value = mock_account_service_instance
        mock_account_service_instance.get_account_balance.return_value = Decimal('1000.00')
        mock_account_service_instance.update_account_balance.return_value = True
        
        mock_transaction = Mock()
        mock_transaction.id = 'transaction-123'
        
        with patch('app.services.Transaction') as mock_transaction_class:
            mock_transaction_class.return_value = mock_transaction
            
            result = self.transaction_service.create_transaction(
                from_account_id='account-1',
                to_account_id='account-2',
                amount=Decimal('500.00'),
                currency='USD',
                description='Transfer'
            )
            
            assert result == mock_transaction
            mock_db_session.add.assert_called_once_with(mock_transaction)
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.AccountService')
    def test_create_transaction_insufficient_funds(self, mock_account_service):
        """Test transaction creation with insufficient funds."""
        # Mock account service
        mock_account_service_instance = Mock()
        mock_account_service.return_value = mock_account_service_instance
        mock_account_service_instance.get_account_balance.return_value = Decimal('100.00')
        
        with pytest.raises(ValueError, match="Insufficient funds"):
            self.transaction_service.create_transaction(
                from_account_id='account-1',
                to_account_id='account-2',
                amount=Decimal('500.00'),
                currency='USD',
                description='Transfer'
            )
    
    @patch('app.services.get_db_session')
    def test_get_transaction_history(self, mock_session):
        """Test getting transaction history."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_transaction1 = Mock()
        mock_transaction1.amount = Decimal('100.00')
        mock_transaction2 = Mock()
        mock_transaction2.amount = Decimal('200.00')
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_transaction1, mock_transaction2
        ]
        
        result = self.transaction_service.get_transaction_history('account-123', limit=10)
        
        assert len(result) == 2
        assert result[0].amount == Decimal('100.00')
        assert result[1].amount == Decimal('200.00')


class TestBudgetService:
    """Test cases for Budget Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.budget_service = BudgetService()
    
    @patch('app.services.get_db_session')
    def test_create_budget_success(self, mock_session):
        """Test successful budget creation."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_budget = Mock()
        mock_budget.id = 'budget-123'
        
        with patch('app.services.Budget') as mock_budget_class:
            mock_budget_class.return_value = mock_budget
            
            result = self.budget_service.create_budget(
                name='Monthly Budget',
                category='expenses',
                amount=Decimal('2000.00'),
                currency='USD',
                period='monthly',
                organization_id='org-123'
            )
            
            assert result == mock_budget
            mock_db_session.add.assert_called_once_with(mock_budget)
            mock_db_session.commit.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_get_budget_utilization(self, mock_session):
        """Test getting budget utilization."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_budget = Mock()
        mock_budget.amount = Decimal('1000.00')
        mock_budget.spent = Decimal('750.00')
        mock_budget.calculate_utilization.return_value = Decimal('75.0')
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_budget
        
        result = self.budget_service.get_budget_utilization('budget-123')
        
        assert result == Decimal('75.0')
        mock_budget.calculate_utilization.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_update_budget_spending(self, mock_session):
        """Test updating budget spending."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_budget = Mock()
        mock_budget.spent = Decimal('500.00')
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_budget
        
        result = self.budget_service.update_budget_spending('budget-123', Decimal('200.00'))
        
        assert result is True
        assert mock_budget.spent == Decimal('700.00')
        mock_db_session.commit.assert_called_once()


class TestAuditService:
    """Test cases for Audit Service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.audit_service = AuditService()
    
    @patch('app.services.audit_logger')
    def test_log_user_activity(self, mock_audit_logger):
        """Test logging user activity."""
        mock_audit_logger.log_activity.return_value = 'audit-log-123'
        
        result = self.audit_service.log_user_activity(
            user_id='user-123',
            action='LOGIN',
            ip_address='192.168.1.1',
            message='User logged in'
        )
        
        assert result == 'audit-log-123'
        mock_audit_logger.log_activity.assert_called_once()
    
    @patch('app.services.get_db_session')
    def test_get_audit_logs_for_user(self, mock_session):
        """Test getting audit logs for user."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_log1 = Mock()
        mock_log1.action = 'LOGIN'
        mock_log2 = Mock()
        mock_log2.action = 'LOGOUT'
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_log1, mock_log2
        ]
        
        result = self.audit_service.get_audit_logs_for_user('user-123', limit=10)
        
        assert len(result) == 2
        assert result[0].action == 'LOGIN'
        assert result[1].action == 'LOGOUT'
    
    @patch('app.services.get_db_session')
    def test_get_security_events(self, mock_session):
        """Test getting security events."""
        mock_db_session = Mock()
        mock_session.return_value.__enter__.return_value = mock_db_session
        
        mock_event1 = Mock()
        mock_event1.action = 'FAILED_LOGIN'
        mock_event2 = Mock()
        mock_event2.action = 'PERMISSION_DENIED'
        
        security_actions = ['FAILED_LOGIN', 'PERMISSION_DENIED', 'ACCOUNT_LOCKED']
        
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_event1, mock_event2
        ]
        
        result = self.audit_service.get_security_events(limit=50)
        
        assert len(result) == 2
        assert result[0].action == 'FAILED_LOGIN'
        assert result[1].action == 'PERMISSION_DENIED'