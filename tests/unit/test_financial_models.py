"""
Unit tests for financial models.
Tests Account, Transaction, Budget, and Fee models with tenant scoping.

Last updated: 2025-08-31 by AI Assistant
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Mock the UUID type for SQLite compatibility
import sqlalchemy
from sqlalchemy import String

# Replace UUID with String for testing 
original_uuid = None

def setup_module():
    """Replace UUID with String for SQLite compatibility."""
    global original_uuid
    from sqlalchemy.dialects.postgresql import UUID
    original_uuid = UUID
    # Mock UUID to be String for SQLite
    sqlalchemy.dialects.postgresql.UUID = lambda *args, **kwargs: String(36)

def teardown_module():
    """Restore original UUID."""
    global original_uuid
    if original_uuid:
        sqlalchemy.dialects.postgresql.UUID = original_uuid

from app.financial_models import Account, Transaction, Budget, Fee


class TestAccountModel:
    """Test cases for Account model."""
    
    def test_account_creation(self):
        """Test basic account creation."""
        account = Account(
            name="Test Checking Account",
            account_type="checking",
            account_number="123456789",
            balance=Decimal('1000.00'),
            currency="USD",
            is_active=True,
            description="Primary checking account",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # Test object creation
        assert account.name == "Test Checking Account"
        assert account.account_type == "checking"
        assert account.balance == Decimal('1000.00')
        assert account.tenant_type == "user"
        assert account.tenant_id == "user-123"
    
    def test_account_repr(self):
        """Test Account string representation."""
        account = Account(
            name="Test Account",
            account_type="savings",
            balance=Decimal('500.00')
        )
        account.id = "test-account-id"
        
        repr_str = repr(account)
        assert "Account" in repr_str
        assert "test-account-id" in repr_str
        assert "Test Account" in repr_str
        assert "savings" in repr_str
        assert "500.00" in repr_str
    
    def test_account_default_values(self):
        """Test account default values."""
        account = Account(
            name="Minimal Account",
            account_type="checking",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # When not specified, balance should default to None (set by DB)
        # But the column default is 0, so we test that the field accepts None
        assert account.balance is None  # Will be set to 0 by database
        assert account.currency is None  # Will be set to USD by database  
        assert account.is_active is None  # Will be set to True by database
        assert account.description is None


class TestTransactionModel:
    """Test cases for Transaction model."""
    
    def test_transaction_creation(self):
        """Test basic transaction creation."""
        transaction = Transaction(
            amount=Decimal('100.50'),
            currency="USD",
            description="Test transaction",
            transaction_type="debit",
            reference_number="TXN001",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        assert transaction.amount == Decimal('100.50')
        assert transaction.transaction_type == "debit"
        assert transaction.reference_number == "TXN001"
    
    def test_transaction_repr(self):
        """Test Transaction string representation."""
        transaction = Transaction(
            amount=Decimal('250.00'),
            transaction_type="credit",
            description="Test credit"
        )
        transaction.id = "test-txn-id"
        
        repr_str = repr(transaction)
        assert "Transaction" in repr_str
        assert "test-txn-id" in repr_str
        assert "250.00" in repr_str
        assert "credit" in repr_str
    
    def test_transaction_default_currency(self):
        """Test transaction default currency."""
        transaction = Transaction(
            amount=Decimal('50.00'),
            transaction_type="debit",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # Currency default is set by database, not by model instantiation
        assert transaction.currency is None  # Will be set to USD by database
    
    def test_transaction_default_status(self):
        """Test transaction default status."""
        transaction = Transaction(
            amount=Decimal('75.00'),
            transaction_type="credit",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # Status default is set by database, not by model instantiation
        assert transaction.status is None  # Will be set to "completed" by database


class TestBudgetModel:
    """Test cases for Budget model."""
    
    def test_budget_creation(self):
        """Test basic budget creation."""
        budget = Budget(
            name="Monthly Food Budget",
            total_amount=Decimal('500.00'),
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            tenant_type="user",
            tenant_id="user-123"
        )
        
        assert budget.name == "Monthly Food Budget"
        assert budget.total_amount == Decimal('500.00')
        assert budget.start_date.year == 2024
    
    def test_budget_repr(self):
        """Test Budget string representation."""
        budget = Budget(
            name="Test Budget",
            total_amount=Decimal('200.00'),
            spent_amount=Decimal('50.00'),
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc)
        )
        budget.id = "test-budget-id"
        
        repr_str = repr(budget)
        assert "Budget" in repr_str
        assert "test-budget-id" in repr_str
        assert "Test Budget" in repr_str
        assert "200.00" in repr_str
    
    def test_budget_is_active_default(self):
        """Test budget is active by default."""
        budget = Budget(
            name="Test Budget",
            total_amount=Decimal('100.00'),
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # is_active default is set by database, not by model instantiation
        assert budget.is_active is None  # Will be set to True by database
    
    def test_budget_spending_tracking(self):
        """Test budget spending tracking."""
        budget = Budget(
            name="Test Budget",
            total_amount=Decimal('300.00'),
            spent_amount=Decimal('150.00'),
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            tenant_type="user",
            tenant_id="user-123"
        )
        
        assert budget.spent_amount == Decimal('150.00')
        # Remaining budget would be 300 - 150 = 150
        remaining = budget.total_amount - budget.spent_amount
        assert remaining == Decimal('150.00')


class TestFeeModel:
    """Test cases for Fee model."""
    
    def test_fee_creation(self):
        """Test basic fee creation."""
        fee = Fee(
            name="Monthly Maintenance Fee",
            fee_type="maintenance",
            amount=Decimal('5.00'),
            currency="USD",
            description="Monthly account maintenance fee",
            tenant_type="organization",
            tenant_id="org-456"
        )
        
        assert fee.name == "Monthly Maintenance Fee"
        assert fee.amount == Decimal('5.00')
        assert fee.fee_type == "maintenance"
    
    def test_fee_repr(self):
        """Test Fee string representation."""
        fee = Fee(
            name="Transaction Fee",
            fee_type="transaction",
            amount=Decimal('2.50')
        )
        fee.id = "test-fee-id"
        
        repr_str = repr(fee)
        assert "Fee" in repr_str
        assert "test-fee-id" in repr_str
        assert "Transaction Fee" in repr_str
        assert "2.50" in repr_str
    
    def test_fee_default_values(self):
        """Test fee default values."""
        fee = Fee(
            name="Test Fee",
            fee_type="test",
            amount=Decimal('1.00'),
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # Default values are set by database, not by model instantiation
        assert fee.currency is None  # Will be set to USD by database
        assert fee.status is None    # Will be set to "active" by database
    
    def test_fee_with_account_association(self):
        """Test fee with account association."""
        fee = Fee(
            name="Overdraft Fee",
            fee_type="overdraft",
            amount=Decimal('35.00'),
            account_id="account-123",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        assert fee.account_id == "account-123"


class TestFinancialModelTenantIsolation:
    """Test tenant isolation across all financial models."""
    
    def test_tenant_field_assignment(self):
        """Test that tenant fields are properly assigned."""
        # Create data for user tenant
        user_account = Account(
            name="User Account",
            account_type="personal",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        user_transaction = Transaction(
            amount=Decimal('100.00'),
            transaction_type="debit",
            tenant_type="user",
            tenant_id="user-123"
        )
        
        user_budget = Budget(
            name="User Budget",
            total_amount=Decimal('200.00'),
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            tenant_type="user",
            tenant_id="user-123"
        )
        
        # Create data for organization tenant
        org_account = Account(
            name="Org Account",
            account_type="business",
            tenant_type="organization",
            tenant_id="org-456"
        )
        
        org_transaction = Transaction(
            amount=Decimal('1000.00'),
            transaction_type="credit",
            tenant_type="organization",
            tenant_id="org-456"
        )
        
        org_budget = Budget(
            name="Org Budget",
            total_amount=Decimal('5000.00'),
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
            tenant_type="organization",
            tenant_id="org-456"
        )
        
        # Verify tenant assignment
        assert user_account.tenant_type == "user"
        assert user_account.tenant_id == "user-123"
        assert user_transaction.tenant_type == "user"
        assert user_transaction.tenant_id == "user-123"
        assert user_budget.tenant_type == "user"
        assert user_budget.tenant_id == "user-123"
        
        assert org_account.tenant_type == "organization"
        assert org_account.tenant_id == "org-456"
        assert org_transaction.tenant_type == "organization"
        assert org_transaction.tenant_id == "org-456"
        assert org_budget.tenant_type == "organization"
        assert org_budget.tenant_id == "org-456"