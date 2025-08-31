"""Multi-tenancy extension for Financial Stronghold."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session
from app.core.tenant import Organization, UserOrganizationLink, TenantType
from app.financial_models import Account, Transaction, Fee, Budget
from app.services import TenantService
from app.core.models import User


@pytest.fixture
def sample_user(db_session: Session):
    """Create a sample user for testing."""
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_organization(db_session: Session):
    """Create a sample organization for testing."""
    org = Organization(name="Test Organization")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def user_org_link(db_session: Session, sample_user: User, sample_organization: Organization):
    """Create a user-organization link."""
    link = UserOrganizationLink(
        user_id=sample_user.id,
        org_id=sample_organization.id,
        role="owner"
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


class TestTenantMixin:
    """Test the TenantMixin functionality."""

    def test_tenant_key_property(self, db_session: Session, sample_user: User):
        """Test the tenant_key property."""
        account = Account(
            name="Test Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)  # Convert UUID to string for tenant_id
        )
        
        expected_key = (TenantType.USER.value, str(sample_user.id))
        assert account.tenant_key == expected_key


class TestTenantService:
    """Test the TenantService functionality."""

    def test_create_account_with_tenant_scoping(self, db_session: Session, sample_user: User):
        """Test creating an account with tenant scoping."""
        service = TenantService(db=db_session, model=Account)
        
        account_data = {
            "name": "Test Account",
            "account_type": "checking",
            "balance": Decimal("1000.00"),
            "currency": "USD"
        }
        
        account = service.create(
            account_data,
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        assert account.name == "Test Account"
        assert account.tenant_type == TenantType.USER
        assert account.tenant_id == str(sample_user.id)
        assert account.balance == Decimal("1000.00")

    def test_get_all_accounts_filtered_by_tenant(self, db_session: Session, sample_user: User, sample_organization: Organization):
        """Test that get_all properly filters by tenant."""
        service = TenantService(db=db_session, model=Account)
        
        # Create account for user tenant
        user_account = service.create(
            {
                "name": "User Account",
                "account_type": "checking",
                "balance": Decimal("1000.00")
            },
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        # Create account for organization tenant
        org_account = service.create(
            {
                "name": "Org Account",
                "account_type": "business",
                "balance": Decimal("5000.00")
            },
            tenant_type=TenantType.ORGANIZATION.value,
            tenant_id=sample_organization.id
        )
        
        # Get accounts for user tenant
        user_accounts = service.get_all(
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        # Get accounts for organization tenant
        org_accounts = service.get_all(
            tenant_type=TenantType.ORGANIZATION.value,
            tenant_id=sample_organization.id
        )
        
        # Verify isolation
        assert len(user_accounts) == 1
        assert user_accounts[0].name == "User Account"
        
        assert len(org_accounts) == 1
        assert org_accounts[0].name == "Org Account"

    def test_get_one_account_by_tenant(self, db_session: Session, sample_user: User):
        """Test getting a specific account by tenant."""
        service = TenantService(db=db_session, model=Account)
        
        # Create account
        account = service.create(
            {
                "name": "Test Account",
                "account_type": "checking",
                "balance": Decimal("1000.00")
            },
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        # Get the account
        retrieved_account = service.get_one(
            account.id,
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        assert retrieved_account is not None
        assert retrieved_account.id == account.id
        assert retrieved_account.name == "Test Account"
        
        # Try to get with wrong tenant - should return None
        wrong_tenant_account = service.get_one(
            account.id,
            tenant_type=TenantType.ORGANIZATION.value,
            tenant_id=999
        )
        
        assert wrong_tenant_account is None

    def test_update_account_with_tenant_scoping(self, db_session: Session, sample_user: User):
        """Test updating an account with tenant scoping."""
        service = TenantService(db=db_session, model=Account)
        
        # Create account
        account = service.create(
            {
                "name": "Test Account",
                "account_type": "checking",
                "balance": Decimal("1000.00")
            },
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        # Update the account
        updated_account = service.update(
            account.id,
            {"name": "Updated Account", "balance": Decimal("2000.00")},
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        assert updated_account is not None
        assert updated_account.name == "Updated Account"
        assert updated_account.balance == Decimal("2000.00")
        
        # Try to update with wrong tenant - should return None
        wrong_tenant_update = service.update(
            account.id,
            {"name": "Should Not Work"},
            tenant_type=TenantType.ORGANIZATION.value,
            tenant_id=999
        )
        
        assert wrong_tenant_update is None

    def test_delete_account_with_tenant_scoping(self, db_session: Session, sample_user: User):
        """Test deleting an account with tenant scoping."""
        service = TenantService(db=db_session, model=Account)
        
        # Create account
        account = service.create(
            {
                "name": "Test Account",
                "account_type": "checking",
                "balance": Decimal("1000.00")
            },
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        # Try to delete with wrong tenant - should return False
        wrong_tenant_delete = service.delete(
            account.id,
            tenant_type=TenantType.ORGANIZATION.value,
            tenant_id=999
        )
        
        assert wrong_tenant_delete is False
        
        # Verify account still exists
        existing_account = service.get_one(
            account.id,
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        assert existing_account is not None
        
        # Delete with correct tenant - should return True
        correct_tenant_delete = service.delete(
            account.id,
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        
        assert correct_tenant_delete is True
        
        # Verify account is deleted
        deleted_account = service.get_one(
            account.id,
            tenant_type=TenantType.USER.value,
            tenant_id=str(sample_user.id)
        )
        assert deleted_account is None


class TestOrganizationModel:
    """Test the Organization model."""

    def test_create_organization(self, db_session: Session):
        """Test creating an organization."""
        org = Organization(name="Test Company")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)
        
        assert org.id is not None
        assert org.name == "Test Company"
        assert org.created_at is not None

    def test_user_organization_link(self, db_session: Session, sample_user: User, sample_organization: Organization):
        """Test the user-organization link."""
        link = UserOrganizationLink(
            user_id=sample_user.id,
            org_id=sample_organization.id,
            role="admin"
        )
        db_session.add(link)
        db_session.commit()
        db_session.refresh(link)
        
        assert link.user_id == sample_user.id
        assert link.org_id == sample_organization.id
        assert link.role == "admin"
        assert link.joined_at is not None


class TestFinancialModels:
    """Test the financial domain models."""

    def test_create_transaction_with_tenant(self, db_session: Session, sample_user: User):
        """Test creating a transaction with tenant scoping."""
        transaction = Transaction(
            amount=Decimal("100.50"),
            currency="USD",
            description="Test transaction",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        db_session.add(transaction)
        db_session.commit()
        db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.amount == Decimal("100.50")
        assert transaction.tenant_type == TenantType.USER
        assert transaction.tenant_id == str(sample_user.id)

    def test_create_fee_with_tenant(self, db_session: Session, sample_user: User):
        """Test creating a fee with tenant scoping."""
        fee = Fee(
            name="Monthly Fee",
            amount=Decimal("10.00"),
            fee_type="monthly",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        db_session.add(fee)
        db_session.commit()
        db_session.refresh(fee)
        
        assert fee.id is not None
        assert fee.name == "Monthly Fee"
        assert fee.amount == Decimal("10.00")
        assert fee.tenant_type == TenantType.USER
        assert fee.tenant_id == str(sample_user.id)

    def test_create_budget_with_tenant(self, db_session: Session, sample_user: User):
        """Test creating a budget with tenant scoping."""
        budget = Budget(
            name="Monthly Budget",
            total_amount=Decimal("1000.00"),
            currency="USD",
            start_date=datetime.now(),
            end_date=datetime.now(),
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        db_session.add(budget)
        db_session.commit()
        db_session.refresh(budget)
        
        assert budget.id is not None
        assert budget.name == "Monthly Budget"
        assert budget.total_amount == Decimal("1000.00")
        assert budget.tenant_type == TenantType.USER
        assert budget.tenant_id == str(sample_user.id)