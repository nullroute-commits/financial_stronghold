"""Tests for tagging and analytics functionality."""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.core.models import User, Role
from app.core.tenant import TenantType, Organization
from app.financial_models import Account, Transaction, Budget
from app.tagging_models import DataTag, AnalyticsView, TagType
from app.tagging_service import TaggingService, AnalyticsService


class TestTaggingService:
    """Test cases for TaggingService."""

    def test_create_user_tag(self, db_session, sample_user):
        """Test creating a user-level tag."""
        service = TaggingService(db_session)
        
        tag = service.create_user_tag(
            user_id=sample_user.id,
            resource_type="transaction",
            resource_id=str(uuid4()),
            tenant_type="user",
            tenant_id=str(sample_user.id),
            label="Test User Tag",
            metadata={"test": "data"}
        )
        
        assert tag.tag_type == TagType.USER
        assert tag.tag_key == "user_id"
        assert tag.tag_value == str(sample_user.id)
        assert tag.resource_type == "transaction"
        assert tag.tag_label == "Test User Tag"
        assert tag.tag_metadata == {"test": "data"}
        assert tag.is_active is True

    def test_create_organization_tag(self, db_session):
        """Test creating an organization-level tag."""
        service = TaggingService(db_session)
        
        tag = service.create_organization_tag(
            org_id=123,
            resource_type="account",
            resource_id=str(uuid4()),
            tenant_type="organization",
            tenant_id="123",
            label="Test Org Tag"
        )
        
        assert tag.tag_type == TagType.ORGANIZATION
        assert tag.tag_key == "org_id"
        assert tag.tag_value == "123"
        assert tag.resource_type == "account"
        assert tag.tag_label == "Test Org Tag"

    def test_create_role_tag(self, db_session, sample_role):
        """Test creating a role-level tag."""
        service = TaggingService(db_session)
        
        tag = service.create_role_tag(
            role_id=sample_role.id,
            resource_type="budget",
            resource_id=str(uuid4()),
            tenant_type="user",
            tenant_id="test_user_123",
            label="Test Role Tag"
        )
        
        assert tag.tag_type == TagType.ROLE
        assert tag.tag_key == "role_id"
        assert tag.tag_value == str(sample_role.id)
        assert tag.resource_type == "budget"
        assert tag.tag_label == "Test Role Tag"

    def test_get_resource_tags(self, db_session, sample_user):
        """Test retrieving tags for a resource."""
        service = TaggingService(db_session)
        resource_id = str(uuid4())
        
        # Create multiple tags for the same resource
        user_tag = service.create_user_tag(
            user_id=sample_user.id,
            resource_type="transaction",
            resource_id=resource_id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        org_tag = service.create_organization_tag(
            org_id=456,
            resource_type="transaction",
            resource_id=resource_id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        # Retrieve all tags
        tags = service.get_resource_tags(
            resource_type="transaction",
            resource_id=resource_id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert len(tags) == 2
        tag_types = {tag.tag_type for tag in tags}
        assert TagType.USER in tag_types
        assert TagType.ORGANIZATION in tag_types

    def test_get_tagged_resources(self, db_session, sample_user):
        """Test querying resources by tag filters."""
        service = TaggingService(db_session)
        
        resource1 = str(uuid4())
        resource2 = str(uuid4())
        resource3 = str(uuid4())
        
        # Create tags for different resources
        service.create_user_tag(
            user_id=sample_user.id,
            resource_type="transaction",
            resource_id=resource1,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        service.create_user_tag(
            user_id=sample_user.id,
            resource_type="transaction",
            resource_id=resource2,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        service.create_organization_tag(
            org_id=123,
            resource_type="transaction",
            resource_id=resource2,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        # Query by user_id filter - should return both resource1 and resource2
        user_filtered = service.get_tagged_resources(
            tag_filters={"user_id": str(sample_user.id)},
            resource_type="transaction",
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert len(user_filtered) == 2
        assert resource1 in user_filtered
        assert resource2 in user_filtered
        
        # Query by multiple filters - should return only resource2
        multi_filtered = service.get_tagged_resources(
            tag_filters={"user_id": str(sample_user.id), "org_id": "123"},
            resource_type="transaction",
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert len(multi_filtered) == 1
        assert resource2 in multi_filtered

    def test_auto_tag_resource(self, db_session, sample_user, sample_role):
        """Test automatic tagging of a resource."""
        # Assign role to user
        sample_user.roles.append(sample_role)
        db_session.commit()
        
        service = TaggingService(db_session)
        resource_id = str(uuid4())
        
        tags = service.auto_tag_resource(
            resource_type="account",
            resource_id=resource_id,
            tenant_type="user",
            tenant_id=str(sample_user.id),
            user_id=sample_user.id
        )
        
        # Should create user tag and role tag
        assert len(tags) >= 2
        
        tag_types = {tag.tag_type for tag in tags}
        assert TagType.USER in tag_types
        assert TagType.ROLE in tag_types
        
        # Verify user tag
        user_tags = [tag for tag in tags if tag.tag_type == TagType.USER]
        assert len(user_tags) == 1
        assert user_tags[0].tag_value == str(sample_user.id)
        
        # Verify role tag
        role_tags = [tag for tag in tags if tag.tag_type == TagType.ROLE]
        assert len(role_tags) == 1
        assert role_tags[0].tag_value == str(sample_role.id)


class TestAnalyticsService:
    """Test cases for AnalyticsService."""

    def test_compute_transaction_metrics(self, db_session, sample_user):
        """Test computing transaction metrics."""
        service = AnalyticsService(db_session)
        tagging_service = service.tagging_service
        
        # Create transactions
        transaction1 = Transaction(
            amount=Decimal("100.00"),
            currency="USD",
            description="Test transaction 1",
            transaction_type="debit",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        transaction2 = Transaction(
            amount=Decimal("200.00"),
            currency="USD",
            description="Test transaction 2",
            transaction_type="credit",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        
        db_session.add_all([transaction1, transaction2])
        db_session.commit()
        
        # Tag transactions
        tagging_service.create_user_tag(
            user_id=sample_user.id,
            resource_type="transaction",
            resource_id=transaction1.id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        tagging_service.create_user_tag(
            user_id=sample_user.id,
            resource_type="transaction",
            resource_id=transaction2.id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        # Compute metrics
        metrics = service.compute_tag_metrics(
            tag_filters={"user_id": str(sample_user.id)},
            resource_type="transaction",
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert metrics["resource_type"] == "transaction"
        assert metrics["total_count"] == 2
        assert metrics["total_amount"] == 300.0
        assert metrics["average_amount"] == 150.0
        assert metrics["min_amount"] == 100.0
        assert metrics["max_amount"] == 200.0
        
        # Check type breakdown
        assert "type_breakdown" in metrics
        assert "debit" in metrics["type_breakdown"]
        assert "credit" in metrics["type_breakdown"]
        assert metrics["type_breakdown"]["debit"]["count"] == 1
        assert metrics["type_breakdown"]["credit"]["count"] == 1

    def test_compute_account_metrics(self, db_session, sample_user):
        """Test computing account metrics."""
        service = AnalyticsService(db_session)
        tagging_service = service.tagging_service
        
        # Create accounts
        account1 = Account(
            name="Test Account 1",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="USD",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        account2 = Account(
            name="Test Account 2",
            account_type="savings",
            balance=Decimal("2000.00"),
            currency="USD",
            tenant_type=TenantType.USER,
            tenant_id=str(sample_user.id)
        )
        
        db_session.add_all([account1, account2])
        db_session.commit()
        
        # Tag accounts
        tagging_service.create_user_tag(
            user_id=sample_user.id,
            resource_type="account",
            resource_id=account1.id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        tagging_service.create_user_tag(
            user_id=sample_user.id,
            resource_type="account",
            resource_id=account2.id,
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        # Compute metrics
        metrics = service.compute_tag_metrics(
            tag_filters={"user_id": str(sample_user.id)},
            resource_type="account",
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert metrics["resource_type"] == "account"
        assert metrics["total_count"] == 2
        assert metrics["active_count"] == 2
        assert metrics["total_balance"] == 3000.0
        assert metrics["average_balance"] == 1500.0
        
        # Check type breakdown
        assert "type_breakdown" in metrics
        assert "checking" in metrics["type_breakdown"]
        assert "savings" in metrics["type_breakdown"]

    def test_get_analytics_summary(self, db_session, sample_user):
        """Test getting comprehensive analytics summary."""
        service = AnalyticsService(db_session)
        
        summary = service.get_analytics_summary(
            tenant_type="user",
            tenant_id=str(sample_user.id),
            tag_filters={"user_id": str(sample_user.id)}
        )
        
        assert "tenant_info" in summary
        assert summary["tenant_info"]["tenant_type"] == "user"
        assert summary["tenant_info"]["tenant_id"] == str(sample_user.id)
        
        assert "tag_filters" in summary
        assert summary["tag_filters"] == {"user_id": str(sample_user.id)}
        
        assert "resource_metrics" in summary
        assert "transaction" in summary["resource_metrics"]
        assert "account" in summary["resource_metrics"]
        assert "budget" in summary["resource_metrics"]
        
        assert "generated_at" in summary

    def test_create_analytics_view(self, db_session, sample_user):
        """Test creating an analytics view."""
        service = AnalyticsService(db_session)
        
        view = service.create_analytics_view(
            view_name="User Analytics",
            tag_filters={"user_id": str(sample_user.id)},
            resource_types=["transaction", "account"],
            tenant_type="user",
            tenant_id=str(sample_user.id),
            description="Analytics for specific user"
        )
        
        assert view.view_name == "User Analytics"
        assert view.tag_filters == {"user_id": str(sample_user.id)}
        assert view.resource_types == ["transaction", "account"]
        assert view.view_description == "Analytics for specific user"
        assert view.computation_status == "completed"
        assert view.tenant_type == TenantType.USER
        assert view.tenant_id == str(sample_user.id)
        assert view.last_computed is not None
        
        # Check metrics structure
        assert "transaction" in view.metrics
        assert "account" in view.metrics

    def test_refresh_analytics_view(self, db_session, sample_user):
        """Test refreshing an analytics view."""
        service = AnalyticsService(db_session)
        
        # Create initial view
        view = service.create_analytics_view(
            view_name="Refresh Test",
            tag_filters={"user_id": str(sample_user.id)},
            resource_types=["transaction"],
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        original_computed_time = view.last_computed
        
        # Refresh the view
        refreshed_view = service.refresh_analytics_view(view.id)
        
        assert refreshed_view.id == view.id
        assert refreshed_view.computation_status == "completed"
        assert refreshed_view.last_computed > original_computed_time

    def test_empty_metrics(self, db_session, sample_user):
        """Test handling of empty data sets."""
        service = AnalyticsService(db_session)
        
        # Query with filters that match no resources
        metrics = service.compute_tag_metrics(
            tag_filters={"user_id": "nonexistent_user"},
            resource_type="transaction",
            tenant_type="user",
            tenant_id=str(sample_user.id)
        )
        
        assert metrics["total_count"] == 0
        assert "message" in metrics
        assert metrics["message"] == "No data found for the specified filters"


# Fixtures for testing
@pytest.fixture
def sample_user(db_session):
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
def sample_role(db_session):
    """Create a sample role for testing."""
    role = Role(
        name="test_role",
        description="Test role for analytics",
        is_active=True
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def db_session():
    """Mock database session for testing."""
    # This would be properly implemented with a test database
    # For now, this is a placeholder
    pass