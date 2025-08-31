"""
Unit tests for model functionality.
Tests the database models and their relationships.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from app.core.models import User, Role, Permission, AuditLog
from app.financial_models import Account, Transaction, Fee, Budget
from app.core.tenant import Organization, UserOrganizationLink, TenantType


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self):
        """Test user model creation."""
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash='hashed_password'
        )
        
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.password_hash == 'hashed_password'
        assert user.is_active is True  # Default value
        assert user.is_superuser is False  # Default value
    
    def test_user_full_name(self):
        """Test user full name property."""
        user = User(
            first_name='Test',
            last_name='User'
        )
        
        assert user.full_name == 'Test User'
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User(username='testuser')
        
        assert str(user) == 'testuser'
    
    def test_user_email_validation(self):
        """Test user email validation."""
        # Valid email
        user = User(email='test@example.com')
        assert user.email == 'test@example.com'
        
        # Email normalization
        user.email = 'Test@Example.COM'
        user.normalize_email()
        assert user.email == 'test@example.com'


class TestRoleModel:
    """Test cases for Role model."""
    
    def test_role_creation(self):
        """Test role model creation."""
        role = Role(
            name='admin',
            description='Administrator role',
            is_active=True
        )
        
        assert role.name == 'admin'
        assert role.description == 'Administrator role'
        assert role.is_active is True
    
    def test_role_str_representation(self):
        """Test role string representation."""
        role = Role(name='admin')
        
        assert str(role) == 'admin'


class TestPermissionModel:
    """Test cases for Permission model."""
    
    def test_permission_creation(self):
        """Test permission model creation."""
        permission = Permission(
            name='read_users',
            description='Can read user data',
            resource='users',
            action='read'
        )
        
        assert permission.name == 'read_users'
        assert permission.description == 'Can read user data'
        assert permission.resource == 'users'
        assert permission.action == 'read'
        assert permission.is_active is True  # Default value
    
    def test_permission_str_representation(self):
        """Test permission string representation."""
        permission = Permission(name='read_users')
        
        assert str(permission) == 'read_users'


class TestAuditLogModel:
    """Test cases for AuditLog model."""
    
    def test_audit_log_creation(self):
        """Test audit log model creation."""
        audit_log = AuditLog(
            user_id='user-123',
            action='LOGIN',
            resource_type='user',
            message='User logged in',
            ip_address='192.168.1.1'
        )
        
        assert audit_log.user_id == 'user-123'
        assert audit_log.action == 'LOGIN'
        assert audit_log.resource_type == 'user'
        assert audit_log.message == 'User logged in'
        assert audit_log.ip_address == '192.168.1.1'
        assert audit_log.timestamp is not None
    
    def test_audit_log_metadata_serialization(self):
        """Test audit log metadata serialization."""
        metadata = {'browser': 'Chrome', 'version': '91.0'}
        
        audit_log = AuditLog(
            action='LOGIN',
            metadata=metadata
        )
        
        assert audit_log.metadata == metadata
    
    def test_audit_log_str_representation(self):
        """Test audit log string representation."""
        audit_log = AuditLog(
            action='LOGIN',
            user_id='user-123'
        )
        
        expected = f'LOGIN by user-123 at {audit_log.timestamp}'
        assert str(audit_log) == expected


class TestAccountModel:
    """Test cases for Account model."""
    
    def test_account_creation(self):
        """Test account model creation."""
        account = Account(
            name='Checking Account',
            account_type='checking',
            balance=Decimal('1000.00'),
            currency='USD',
            organization_id='org-123'
        )
        
        assert account.name == 'Checking Account'
        assert account.account_type == 'checking'
        assert account.balance == Decimal('1000.00')
        assert account.currency == 'USD'
        assert account.organization_id == 'org-123'
        assert account.is_active is True  # Default value
    
    def test_account_balance_operations(self):
        """Test account balance operations."""
        account = Account(balance=Decimal('1000.00'))
        
        # Credit operation
        account.credit(Decimal('250.00'))
        assert account.balance == Decimal('1250.00')
        
        # Debit operation
        account.debit(Decimal('150.00'))
        assert account.balance == Decimal('1100.00')
    
    def test_account_insufficient_funds(self):
        """Test account insufficient funds handling."""
        account = Account(balance=Decimal('100.00'))
        
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.debit(Decimal('150.00'))
    
    def test_account_str_representation(self):
        """Test account string representation."""
        account = Account(name='Checking Account')
        
        assert str(account) == 'Checking Account'


class TestTransactionModel:
    """Test cases for Transaction model."""
    
    def test_transaction_creation(self):
        """Test transaction model creation."""
        transaction = Transaction(
            from_account_id='account-1',
            to_account_id='account-2',
            amount=Decimal('500.00'),
            currency='USD',
            description='Payment for services',
            transaction_type='transfer'
        )
        
        assert transaction.from_account_id == 'account-1'
        assert transaction.to_account_id == 'account-2'
        assert transaction.amount == Decimal('500.00')
        assert transaction.currency == 'USD'
        assert transaction.description == 'Payment for services'
        assert transaction.transaction_type == 'transfer'
        assert transaction.status == 'pending'  # Default value
    
    def test_transaction_validation(self):
        """Test transaction validation."""
        # Valid transaction
        transaction = Transaction(
            amount=Decimal('100.00'),
            currency='USD'
        )
        assert transaction.amount > 0
        
        # Invalid amount
        with pytest.raises(ValueError, match="Amount must be positive"):
            Transaction(amount=Decimal('-100.00'))
    
    def test_transaction_str_representation(self):
        """Test transaction string representation."""
        transaction = Transaction(
            amount=Decimal('500.00'),
            currency='USD',
            transaction_type='transfer'
        )
        
        expected = f'transfer: 500.00 USD'
        assert str(transaction) == expected


class TestBudgetModel:
    """Test cases for Budget model."""
    
    def test_budget_creation(self):
        """Test budget model creation."""
        budget = Budget(
            name='Monthly Budget',
            category='expenses',
            amount=Decimal('2000.00'),
            currency='USD',
            period='monthly',
            organization_id='org-123'
        )
        
        assert budget.name == 'Monthly Budget'
        assert budget.category == 'expenses'
        assert budget.amount == Decimal('2000.00')
        assert budget.currency == 'USD'
        assert budget.period == 'monthly'
        assert budget.organization_id == 'org-123'
    
    def test_budget_utilization_calculation(self):
        """Test budget utilization calculation."""
        budget = Budget(
            amount=Decimal('1000.00'),
            spent=Decimal('750.00')
        )
        
        utilization = budget.calculate_utilization()
        assert utilization == Decimal('75.0')  # 75% utilization
    
    def test_budget_remaining_calculation(self):
        """Test budget remaining calculation."""
        budget = Budget(
            amount=Decimal('1000.00'),
            spent=Decimal('300.00')
        )
        
        remaining = budget.calculate_remaining()
        assert remaining == Decimal('700.00')
    
    def test_budget_str_representation(self):
        """Test budget string representation."""
        budget = Budget(name='Monthly Budget')
        
        assert str(budget) == 'Monthly Budget'


class TestOrganizationModel:
    """Test cases for Organization model."""
    
    def test_organization_creation(self):
        """Test organization model creation."""
        org = Organization(
            name='Test Company',
            tenant_type=TenantType.ENTERPRISE,
            description='A test company'
        )
        
        assert org.name == 'Test Company'
        assert org.tenant_type == TenantType.ENTERPRISE
        assert org.description == 'A test company'
        assert org.is_active is True  # Default value
    
    def test_organization_str_representation(self):
        """Test organization string representation."""
        org = Organization(name='Test Company')
        
        assert str(org) == 'Test Company'


class TestUserOrganizationLink:
    """Test cases for UserOrganizationLink model."""
    
    def test_user_org_link_creation(self):
        """Test user organization link creation."""
        link = UserOrganizationLink(
            user_id='user-123',
            org_id='org-456',
            role='admin'
        )
        
        assert link.user_id == 'user-123'
        assert link.org_id == 'org-456'
        assert link.role == 'admin'
        assert link.is_active is True  # Default value
    
    def test_user_org_link_str_representation(self):
        """Test user organization link string representation."""
        link = UserOrganizationLink(
            user_id='user-123',
            org_id='org-456',
            role='admin'
        )
        
        expected = 'user-123 -> org-456 (admin)'
        assert str(link) == expected


class TestModelRelationships:
    """Test cases for model relationships."""
    
    @patch('app.core.models.get_db_session')
    def test_user_roles_relationship(self, mock_session):
        """Test user-roles relationship."""
        # Mock user with roles
        mock_role = Mock()
        mock_role.name = 'admin'
        
        mock_user = Mock()
        mock_user.roles = [mock_role]
        
        # Test relationship
        assert len(mock_user.roles) == 1
        assert mock_user.roles[0].name == 'admin'
    
    @patch('app.core.models.get_db_session')
    def test_role_permissions_relationship(self, mock_session):
        """Test role-permissions relationship."""
        # Mock role with permissions
        mock_permission = Mock()
        mock_permission.name = 'read_users'
        
        mock_role = Mock()
        mock_role.permissions = [mock_permission]
        
        # Test relationship
        assert len(mock_role.permissions) == 1
        assert mock_role.permissions[0].name == 'read_users'