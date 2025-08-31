"""
Unit tests for model functionality.
Tests the database models and their relationships.

Last updated: 2025-08-31 19:00:00 UTC by copilot
"""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

from app.core.models import User, Role, Permission, AuditLog
from app.financial_models import Account, Transaction, Fee, Budget
from app.core.tenant import Organization, UserOrganizationLink


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
    
    def test_user_full_name(self):
        """Test user full name property."""
        user = User(
            first_name='Test',
            last_name='User'
        )
        
        assert user.full_name == 'Test User'
    
    def test_user_str_representation(self):
        """Test user string representation."""
        user = User(username='testuser', email='test@example.com')
        
        assert str(user) == '<User(username=testuser, email=test@example.com)>'
    
    def test_user_has_permission_superuser(self):
        """Test superuser permission check."""
        user = User(is_superuser=True)
        
        result = user.has_permission('any_permission')
        assert result is True
    
    def test_user_has_permission_no_superuser(self):
        """Test permission check for non-superuser with no roles."""
        user = User(is_superuser=False)
        user.roles = []  # No roles
        
        result = user.has_permission('test_permission')
        assert result is False


class TestRoleModel:
    """Test cases for Role model."""
    
    def test_role_creation(self):
        """Test role model creation."""
        role = Role(
            name='admin',
            description='Administrator role'
        )
        
        assert role.name == 'admin'
        assert role.description == 'Administrator role'
    
    def test_role_str_representation(self):
        """Test role string representation."""
        role = Role(name='admin')
        
        assert str(role) == '<Role(name=admin)>'


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
    
    def test_permission_str_representation(self):
        """Test permission string representation."""
        permission = Permission(name='read_users', resource='users', action='read')
        
        assert str(permission) == '<Permission(name=read_users, resource=users, action=read)>'


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
    
    def test_audit_log_metadata_serialization(self):
        """Test audit log metadata serialization."""
        metadata = {'browser': 'Chrome', 'version': '91.0'}
        
        audit_log = AuditLog(
            action='LOGIN',
            extra_metadata=metadata
        )
        
        assert audit_log.extra_metadata == metadata
    
    def test_audit_log_str_representation(self):
        """Test audit log string representation."""
        audit_log = AuditLog(
            action='LOGIN',
            resource_type='user',
            user_id='user-123'
        )
        
        assert str(audit_log) == '<AuditLog(action=LOGIN, resource_type=user, user_id=user-123)>'


class TestAccountModel:
    """Test cases for Account model."""
    
    def test_account_creation(self):
        """Test account model creation."""
        account = Account(
            name='Checking Account',
            account_type='checking',
            balance=Decimal('1000.00'),
            currency='USD'
        )
        
        assert account.name == 'Checking Account'
        assert account.account_type == 'checking'
        assert account.balance == Decimal('1000.00')
        assert account.currency == 'USD'
    
    def test_account_str_representation(self):
        """Test account string representation."""
        account = Account(
            name='Checking Account',
            account_type='checking',
            balance=Decimal('1000.00')
        )
        
        expected = f'<Account(id={account.id}, name=Checking Account, type=checking, balance=1000.00)>'
        assert str(account) == expected


class TestTransactionModel:
    """Test cases for Transaction model."""
    
    def test_transaction_creation(self):
        """Test transaction model creation."""
        transaction = Transaction(
            account_id='account-1',
            to_account_id='account-2',
            amount=Decimal('500.00'),
            currency='USD',
            description='Payment for services',
            transaction_type='transfer'
        )
        
        assert transaction.account_id == 'account-1'
        assert transaction.to_account_id == 'account-2'
        assert transaction.amount == Decimal('500.00')
        assert transaction.currency == 'USD'
        assert transaction.description == 'Payment for services'
        assert transaction.transaction_type == 'transfer'
    
    def test_transaction_str_representation(self):
        """Test transaction string representation."""
        transaction = Transaction(
            amount=Decimal('500.00'),
            currency='USD',
            transaction_type='transfer'
        )
        
        expected = f'<Transaction(id={transaction.id}, amount=500.00, type=transfer, status={transaction.status})>'
        assert str(transaction) == expected


class TestFeeModel:
    """Test cases for Fee model."""
    
    def test_fee_creation(self):
        """Test fee model creation."""
        fee = Fee(
            name='Monthly Maintenance',
            amount=Decimal('15.00'),
            currency='USD',
            fee_type='monthly',
            description='Monthly account maintenance fee'
        )
        
        assert fee.name == 'Monthly Maintenance'
        assert fee.amount == Decimal('15.00')
        assert fee.currency == 'USD'
        assert fee.fee_type == 'monthly'
        assert fee.description == 'Monthly account maintenance fee'
    
    def test_fee_str_representation(self):
        """Test fee string representation."""
        fee = Fee(
            name='Monthly Maintenance',
            amount=Decimal('15.00'),
            fee_type='monthly'
        )
        
        expected = f'<Fee(id={fee.id}, name=Monthly Maintenance, amount=15.00, type=monthly)>'
        assert str(fee) == expected


class TestBudgetModel:
    """Test cases for Budget model."""
    
    def test_budget_creation(self):
        """Test budget model creation."""
        budget = Budget(
            name='Monthly Budget',
            total_amount=Decimal('2000.00'),
            spent_amount=Decimal('750.00'),
            currency='USD',
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 1, 31, tzinfo=timezone.utc)
        )
        
        assert budget.name == 'Monthly Budget'
        assert budget.total_amount == Decimal('2000.00')
        assert budget.spent_amount == Decimal('750.00')
        assert budget.currency == 'USD'
    
    def test_budget_utilization_calculation(self):
        """Test budget utilization calculation."""
        budget = Budget(
            total_amount=Decimal('1000.00'),
            spent_amount=Decimal('750.00')
        )
        
        # Calculate utilization percentage
        utilization = (budget.spent_amount / budget.total_amount) * 100
        assert utilization == Decimal('75.0')  # 75% utilization
    
    def test_budget_remaining_calculation(self):
        """Test budget remaining calculation."""
        budget = Budget(
            total_amount=Decimal('1000.00'),
            spent_amount=Decimal('300.00')
        )
        
        remaining = budget.total_amount - budget.spent_amount
        assert remaining == Decimal('700.00')
    
    def test_budget_str_representation(self):
        """Test budget string representation."""
        budget = Budget(
            name='Monthly Budget',
            total_amount=Decimal('2000.00'),
            spent_amount=Decimal('750.00')
        )
        
        expected = f'<Budget(id={budget.id}, name=Monthly Budget, total=2000.00, spent=750.00)>'
        assert str(budget) == expected


class TestOrganizationModel:
    """Test cases for Organization model."""
    
    def test_organization_creation(self):
        """Test organization model creation."""
        org = Organization(
            name='Test Company'
        )
        
        assert org.name == 'Test Company'
    
    def test_organization_str_representation(self):
        """Test organization string representation."""
        org = Organization(name='Test Company')
        
        expected = f'<Organization(id={org.id}, name=Test Company)>'
        assert str(org) == expected


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
    
    def test_user_org_link_str_representation(self):
        """Test user organization link string representation."""
        link = UserOrganizationLink(
            user_id='user-123',
            org_id='org-456',
            role='admin'
        )
        
        expected = f'<UserOrganizationLink(user_id=user-123, org_id=org-456, role=admin)>'
        assert str(link) == expected


class TestModelProperties:
    """Test cases for model properties and methods."""
    
    def test_user_has_role_method(self):
        """Test user has_role method."""
        user = User(is_superuser=False)
        user.roles = []
        
        result = user.has_role('admin')
        assert result is False
    
    def test_model_to_dict_method(self):
        """Test BaseModel to_dict method."""
        user = User(username='testuser', email='test@example.com')
        
        # The to_dict method should exist
        assert hasattr(user, 'to_dict')
        assert callable(user.to_dict)
    
    def test_tenant_mixin_properties(self):
        """Test TenantMixin properties."""
        account = Account(name='Test Account')
        
        # TenantMixin should provide tenant-related fields
        assert hasattr(account, 'tenant_type')
        assert hasattr(account, 'tenant_id')


class TestModelFieldValidation:
    """Test cases for model field validation."""
    
    def test_decimal_field_precision(self):
        """Test decimal field precision."""
        # Test with high precision decimal
        account = Account(balance=Decimal('12345678.99'))
        assert account.balance == Decimal('12345678.99')
        
        transaction = Transaction(amount=Decimal('0.01'))
        assert transaction.amount == Decimal('0.01')
    
    def test_string_field_length(self):
        """Test string field handling."""
        # Test normal length strings
        user = User(username='test_user_123', email='test@example.com')
        assert user.username == 'test_user_123'
        assert user.email == 'test@example.com'
    
    def test_boolean_field_defaults(self):
        """Test boolean field default handling."""
        user = User()
        permission = Permission()
        
        # These should have default column definitions even if not set at instance level
        assert hasattr(user, 'is_active')
        assert hasattr(user, 'is_superuser')
        assert hasattr(permission, 'is_active')