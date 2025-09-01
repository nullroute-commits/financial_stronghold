"""Test cases for Financial Dashboard feature."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from app.dashboard_service import DashboardService
from app.financial_models import Account, Budget, Transaction
from app.services import TenantService
from app.core.tenant import TenantType


class TestDashboardService:
    """Test suite for Dashboard Service."""

    @pytest.fixture
    def dashboard_service(self, db_session):
        """Create dashboard service instance."""
        return DashboardService(db=db_session)

    @pytest.fixture
    def sample_tenant(self):
        """Sample tenant for testing."""
        return {"tenant_type": TenantType.USER, "tenant_id": "test_user_123"}

    @pytest.fixture
    def sample_accounts(self, db_session, sample_tenant):
        """Create sample accounts for testing."""
        account_service = TenantService(db=db_session, model=Account)
        
        accounts = []
        accounts.append(
            account_service.create(
                {
                    "name": "Checking Account",
                    "account_type": "checking",
                    "balance": Decimal("1500.00"),
                    "currency": "USD",
                    "is_active": True,
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        accounts.append(
            account_service.create(
                {
                    "name": "Savings Account",
                    "account_type": "savings",
                    "balance": Decimal("5000.00"),
                    "currency": "USD",
                    "is_active": True,
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        accounts.append(
            account_service.create(
                {
                    "name": "Inactive Account",
                    "account_type": "savings",
                    "balance": Decimal("100.00"),
                    "currency": "USD",
                    "is_active": False,
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        return accounts

    @pytest.fixture
    def sample_transactions(self, db_session, sample_tenant, sample_accounts):
        """Create sample transactions for testing."""
        transaction_service = TenantService(db=db_session, model=Transaction)
        
        transactions = []
        # Recent transaction (this month)
        transactions.append(
            transaction_service.create(
                {
                    "amount": Decimal("100.00"),
                    "currency": "USD",
                    "description": "Grocery shopping",
                    "transaction_type": "debit",
                    "account_id": sample_accounts[0].id,
                    "status": "completed",
                    "category": "food",
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        # Older transaction
        transactions.append(
            transaction_service.create(
                {
                    "amount": Decimal("50.00"),
                    "currency": "USD",
                    "description": "Gas station",
                    "transaction_type": "debit",
                    "account_id": sample_accounts[0].id,
                    "status": "completed",
                    "category": "transport",
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        return transactions

    @pytest.fixture
    def sample_budgets(self, db_session, sample_tenant):
        """Create sample budgets for testing."""
        budget_service = TenantService(db=db_session, model=Budget)
        
        budgets = []
        now = datetime.now()
        
        budgets.append(
            budget_service.create(
                {
                    "name": "Monthly Food Budget",
                    "total_amount": Decimal("500.00"),
                    "spent_amount": Decimal("300.00"),
                    "currency": "USD",
                    "start_date": now.replace(day=1),
                    "end_date": now.replace(day=30),
                    "is_active": True,
                    "alert_threshold": Decimal("80.0"),
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        budgets.append(
            budget_service.create(
                {
                    "name": "Over Budget Example",
                    "total_amount": Decimal("200.00"),
                    "spent_amount": Decimal("250.00"),
                    "currency": "USD",
                    "start_date": now.replace(day=1),
                    "end_date": now.replace(day=30),
                    "is_active": True,
                },
                tenant_type=sample_tenant["tenant_type"],
                tenant_id=sample_tenant["tenant_id"],
            )
        )
        
        return budgets

    def test_get_account_summaries(self, dashboard_service, sample_tenant, sample_accounts):
        """Test getting account summaries."""
        summaries = dashboard_service.get_account_summaries(
            tenant_type=sample_tenant["tenant_type"],
            tenant_id=sample_tenant["tenant_id"]
        )
        
        assert len(summaries) == 3
        assert summaries[0].name == "Checking Account"
        assert summaries[0].balance == Decimal("1500.00")
        assert summaries[1].name == "Savings Account"
        assert summaries[1].balance == Decimal("5000.00")
        assert summaries[2].is_active is False

    def test_get_financial_summary(self, dashboard_service, sample_tenant, sample_accounts, sample_transactions):
        """Test getting financial summary."""
        summary = dashboard_service.get_financial_summary(
            tenant_type=sample_tenant["tenant_type"],
            tenant_id=sample_tenant["tenant_id"]
        )
        
        # Total balance from all accounts
        assert summary.total_balance == Decimal("6600.00")  # 1500 + 5000 + 100
        assert summary.total_accounts == 3
        assert summary.active_accounts == 2
        assert summary.total_transactions == 2
        assert summary.currency == "USD"

    def test_get_transaction_summary(self, dashboard_service, sample_tenant, sample_transactions):
        """Test getting transaction summary."""
        summary = dashboard_service.get_transaction_summary(
            tenant_type=sample_tenant["tenant_type"],
            tenant_id=sample_tenant["tenant_id"]
        )
        
        assert summary.total_transactions == 2
        assert summary.total_amount == Decimal("150.00")  # 100 + 50
        assert summary.avg_amount == Decimal("75.00")
        assert summary.currency == "USD"
        assert len(summary.recent_transactions) == 2

    def test_get_budget_statuses(self, dashboard_service, sample_tenant, sample_budgets):
        """Test getting budget statuses."""
        statuses = dashboard_service.get_budget_statuses(
            tenant_type=sample_tenant["tenant_type"],
            tenant_id=sample_tenant["tenant_id"]
        )
        
        assert len(statuses) == 2
        
        # First budget: 300/500 = 60% used
        food_budget = statuses[0]
        assert food_budget.name == "Monthly Food Budget"
        assert food_budget.percentage_used == Decimal("60.00")
        assert food_budget.is_over_budget is False
        assert food_budget.remaining_amount == Decimal("200.00")
        
        # Second budget: 250/200 = 125% used (over budget)
        over_budget = statuses[1]
        assert over_budget.name == "Over Budget Example"
        assert over_budget.is_over_budget is True
        assert over_budget.remaining_amount == Decimal("-50.00")

    def test_get_complete_dashboard_data(self, dashboard_service, sample_tenant, sample_accounts, sample_transactions, sample_budgets):
        """Test getting complete dashboard data."""
        dashboard_data = dashboard_service.get_complete_dashboard_data(
            tenant_type=sample_tenant["tenant_type"],
            tenant_id=sample_tenant["tenant_id"]
        )
        
        # Verify all components are present
        assert dashboard_data.financial_summary is not None
        assert dashboard_data.account_summaries is not None
        assert dashboard_data.transaction_summary is not None
        assert dashboard_data.budget_statuses is not None
        assert dashboard_data.tenant_info is not None
        
        # Verify data integrity
        assert len(dashboard_data.account_summaries) == 3
        assert len(dashboard_data.budget_statuses) == 2
        assert dashboard_data.transaction_summary.total_transactions == 2
        assert dashboard_data.financial_summary.total_balance == Decimal("6600.00")

    def test_empty_data_handling(self, dashboard_service, sample_tenant):
        """Test handling of empty data sets."""
        # Test with no data
        dashboard_data = dashboard_service.get_complete_dashboard_data(
            tenant_type=sample_tenant["tenant_type"],
            tenant_id=sample_tenant["tenant_id"]
        )
        
        assert dashboard_data.financial_summary.total_balance == Decimal("0")
        assert dashboard_data.financial_summary.total_accounts == 0
        assert len(dashboard_data.account_summaries) == 0
        assert dashboard_data.transaction_summary.total_transactions == 0
        assert len(dashboard_data.budget_statuses) == 0

    def test_tenant_isolation(self, dashboard_service, db_session):
        """Test that data is properly isolated by tenant."""
        tenant1 = {"tenant_type": TenantType.USER, "tenant_id": "user1"}
        tenant2 = {"tenant_type": TenantType.USER, "tenant_id": "user2"}
        
        # Create account for tenant1
        account_service = TenantService(db=db_session, model=Account)
        account_service.create(
            {
                "name": "Tenant1 Account",
                "account_type": "checking",
                "balance": Decimal("1000.00"),
                "currency": "USD",
            },
            tenant_type=tenant1["tenant_type"],
            tenant_id=tenant1["tenant_id"],
        )
        
        # Get data for both tenants
        tenant1_data = dashboard_service.get_complete_dashboard_data(
            tenant_type=tenant1["tenant_type"],
            tenant_id=tenant1["tenant_id"]
        )
        tenant2_data = dashboard_service.get_complete_dashboard_data(
            tenant_type=tenant2["tenant_type"],
            tenant_id=tenant2["tenant_id"]
        )
        
        # Verify isolation
        assert len(tenant1_data.account_summaries) == 1
        assert len(tenant2_data.account_summaries) == 0
        assert tenant1_data.financial_summary.total_balance == Decimal("1000.00")
        assert tenant2_data.financial_summary.total_balance == Decimal("0")