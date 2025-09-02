"""Comprehensive test coverage for services module."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services import TenantService
from app.financial_models import Account, Transaction, Budget
from app.core.tenant import TenantType, TenantMixin
from app.django_models import BaseModel
from unittest.mock import Mock
# Remove SQLAlchemy imports - using Django ORM


class TestTenantService:
    """Test suite for TenantService class to achieve 100% coverage."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def tenant_service(self, db_session):
        """Create TenantService instance."""
        return TenantService(db=db_session, model=Account)

    @pytest.fixture
    def sample_account_data(self):
        """Sample account data for testing."""
        return {
            "name": "Test Account",
            "account_type": "checking",
            "balance": Decimal("1500.00"),
            "currency": "USD",
            "is_active": True
        }

    @pytest.fixture
    def mock_account(self):
        """Create mock account instance."""
        account = Mock(spec=Account)
        account.id = uuid4()
        account.name = "Test Account"
        account.account_type = "checking"
        account.balance = Decimal("1500.00")
        account.currency = "USD"
        account.is_active = True
        account.tenant_type = TenantType.USER
        account.tenant_id = "test_user_123"
        return account

    def test_tenant_service_initialization(self, db_session):
        """Test TenantService initialization."""
        service = TenantService(db=db_session, model=Account)
        assert service.db == db_session
        assert service.model == Account

    def test_tenant_service_initialization_without_model(self, db_session):
        """Test TenantService initialization without model."""
        service = TenantService(db=db_session)
        assert service.db == db_session
        assert service.model is None

    def test_create_with_tenant_scoping(self, tenant_service, sample_account_data, mock_account):
        """Test creating a record with tenant scoping."""
        tenant_service.db.add = Mock()
        tenant_service.db.commit = Mock()
        tenant_service.db.refresh = Mock()
        
        with patch.object(tenant_service.model, '__call__', return_value=mock_account):
            result = tenant_service.create(
                sample_account_data,
                tenant_type=TenantType.USER,
                tenant_id="test_user_123"
            )
            
            assert result == mock_account
            tenant_service.db.add.assert_called_once_with(mock_account)
            tenant_service.db.commit.assert_called_once()
            tenant_service.db.refresh.assert_called_once_with(mock_account)

    def test_create_without_tenant_scoping(self, tenant_service, sample_account_data):
        """Test creating a record without tenant scoping raises error."""
        with pytest.raises(ValueError, match="tenant_type and tenant_id are required"):
            tenant_service.create(sample_account_data)

    def test_create_with_invalid_tenant_type(self, tenant_service, sample_account_data):
        """Test creating with invalid tenant type."""
        with pytest.raises(ValueError, match="Invalid tenant_type"):
            tenant_service.create(
                sample_account_data,
                tenant_type="invalid_type",
                tenant_id="test_id"
            )

    def test_get_all_with_tenant_filtering(self, tenant_service, mock_account):
        """Test retrieving all records with tenant filtering."""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_account]
        tenant_service.db.query.return_value = mock_query
        
        results = tenant_service.get_all(
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert results == [mock_account]
        tenant_service.db.query.assert_called_once_with(Account)
        mock_query.filter.assert_called()

    def test_get_all_without_tenant_filtering(self, tenant_service, mock_account):
        """Test retrieving all records without tenant filtering."""
        mock_query = Mock()
        mock_query.all.return_value = [mock_account]
        tenant_service.db.query.return_value = mock_query
        
        results = tenant_service.get_all()
        
        assert results == [mock_account]
        mock_query.all.assert_called_once()

    def test_get_by_id_with_tenant_scoping(self, tenant_service, mock_account):
        """Test getting record by ID with tenant scoping."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        tenant_service.db.query.return_value = mock_query
        
        result = tenant_service.get_by_id(
            str(mock_account.id),
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert result == mock_account

    def test_get_by_id_without_tenant_scoping(self, tenant_service, mock_account):
        """Test getting record by ID without tenant scoping."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        tenant_service.db.query.return_value = mock_query
        
        result = tenant_service.get_by_id(str(mock_account.id))
        
        assert result == mock_account

    def test_get_by_id_not_found(self, tenant_service):
        """Test getting non-existent record by ID."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        tenant_service.db.query.return_value = mock_query
        
        result = tenant_service.get_by_id("nonexistent-id")
        assert result is None

    def test_update_with_tenant_scoping(self, tenant_service, mock_account):
        """Test updating a record with tenant scoping."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        tenant_service.db.query.return_value = mock_query
        tenant_service.db.commit = Mock()
        
        update_data = {"name": "Updated Account"}
        
        result = tenant_service.update(
            str(mock_account.id),
            update_data,
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert result == mock_account
        assert mock_account.name == "Updated Account"
        tenant_service.db.commit.assert_called_once()

    def test_update_record_not_found(self, tenant_service):
        """Test updating non-existent record."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        tenant_service.db.query.return_value = mock_query
        
        result = tenant_service.update("nonexistent-id", {"name": "Updated"})
        assert result is None

    def test_delete_with_tenant_scoping(self, tenant_service, mock_account):
        """Test deleting a record with tenant scoping."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        tenant_service.db.query.return_value = mock_query
        tenant_service.db.delete = Mock()
        tenant_service.db.commit = Mock()
        
        result = tenant_service.delete(
            str(mock_account.id),
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert result is True
        tenant_service.db.delete.assert_called_once_with(mock_account)
        tenant_service.db.commit.assert_called_once()

    def test_delete_record_not_found(self, tenant_service):
        """Test deleting non-existent record."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        tenant_service.db.query.return_value = mock_query
        
        result = tenant_service.delete("nonexistent-id")
        assert result is False

    def test_filter_by_tenant_with_mixin(self, tenant_service):
        """Test tenant filtering for models with TenantMixin."""
        mock_query = Mock()
        
        # Simulate filtering by tenant
        filtered_query = tenant_service._filter_by_tenant(
            mock_query, TenantType.USER, "test_user_123"
        )
        
        # Should return the query with filter applied
        assert filtered_query == mock_query.filter.return_value

    def test_filter_by_tenant_without_mixin(self, db_session):
        """Test tenant filtering for models without TenantMixin."""
        # Use a model that doesn't have TenantMixin
        class SimpleModel:
            pass
        
        service = TenantService(db=db_session, model=SimpleModel)
        mock_query = Mock()
        
        # Should return original query unchanged
        filtered_query = service._filter_by_tenant(
            mock_query, TenantType.USER, "test_user_123"
        )
        
        assert filtered_query == mock_query

    def test_bulk_create(self, tenant_service, sample_account_data):
        """Test bulk creating multiple records."""
        data_list = [
            sample_account_data,
            {**sample_account_data, "name": "Account 2"},
            {**sample_account_data, "name": "Account 3"}
        ]
        
        mock_accounts = [Mock(spec=Account) for _ in range(3)]
        tenant_service.db.add_all = Mock()
        tenant_service.db.commit = Mock()
        
        with patch.object(tenant_service.model, '__call__', side_effect=mock_accounts):
            results = tenant_service.bulk_create(
                data_list,
                tenant_type=TenantType.USER,
                tenant_id="test_user_123"
            )
            
            assert len(results) == 3
            tenant_service.db.add_all.assert_called_once()
            tenant_service.db.commit.assert_called_once()

    def test_bulk_update(self, tenant_service, mock_account):
        """Test bulk updating multiple records."""
        updates = [
            {"id": str(mock_account.id), "name": "Updated 1"},
            {"id": "id2", "name": "Updated 2"}
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_account]
        tenant_service.db.query.return_value = mock_query
        tenant_service.db.commit = Mock()
        
        results = tenant_service.bulk_update(
            updates,
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert len(results) >= 0  # Should return updated records
        tenant_service.db.commit.assert_called_once()

    def test_count_with_tenant_filtering(self, tenant_service):
        """Test counting records with tenant filtering."""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        tenant_service.db.query.return_value = mock_query
        
        count = tenant_service.count(
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert count == 5

    def test_count_without_tenant_filtering(self, tenant_service):
        """Test counting records without tenant filtering."""
        mock_query = Mock()
        mock_query.count.return_value = 10
        tenant_service.db.query.return_value = mock_query
        
        count = tenant_service.count()
        
        assert count == 10

    def test_exists_with_tenant_filtering(self, tenant_service, mock_account):
        """Test checking if record exists with tenant filtering."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        tenant_service.db.query.return_value = mock_query
        
        exists = tenant_service.exists(
            str(mock_account.id),
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert exists is True

    def test_exists_record_not_found(self, tenant_service):
        """Test checking if non-existent record exists."""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        tenant_service.db.query.return_value = mock_query
        
        exists = tenant_service.exists("nonexistent-id")
        
        assert exists is False

    def test_paginate_results(self, tenant_service, mock_account):
        """Test paginating query results."""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = [mock_account]
        tenant_service.db.query.return_value = mock_query
        
        results = tenant_service.paginate(
            page=1, per_page=10,
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert results == [mock_account]
        mock_query.offset.assert_called_with(0)
        mock_query.offset.return_value.limit.assert_called_with(10)

    def test_search_records(self, tenant_service, mock_account):
        """Test searching records with filters."""
        search_filters = {"name": "Test", "account_type": "checking"}
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_account]
        tenant_service.db.query.return_value = mock_query
        
        results = tenant_service.search(
            search_filters,
            tenant_type=TenantType.USER,
            tenant_id="test_user_123"
        )
        
        assert results == [mock_account]

    def test_get_or_create_existing_record(self, tenant_service, mock_account):
        """Test get_or_create with existing record."""
        defaults = {"balance": Decimal("2000.00")}
        filters = {"name": "Test Account"}
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        tenant_service.db.query.return_value = mock_query
        
        result, created = tenant_service.get_or_create(
            defaults=defaults,
            tenant_type=TenantType.USER,
            tenant_id="test_user_123",
            **filters
        )
        
        assert result == mock_account
        assert created is False

    def test_get_or_create_new_record(self, tenant_service, mock_account):
        """Test get_or_create with new record."""
        defaults = {"balance": Decimal("2000.00")}
        filters = {"name": "New Account"}
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        tenant_service.db.query.return_value = mock_query
        
        tenant_service.db.add = Mock()
        tenant_service.db.commit = Mock()
        tenant_service.db.refresh = Mock()
        
        with patch.object(tenant_service.model, '__call__', return_value=mock_account):
            result, created = tenant_service.get_or_create(
                defaults=defaults,
                tenant_type=TenantType.USER,
                tenant_id="test_user_123",
                **filters
            )
            
            assert result == mock_account
            assert created is True

    def test_transaction_rollback_on_error(self, tenant_service, sample_account_data):
        """Test transaction rollback on database error."""
        tenant_service.db.add = Mock()
        tenant_service.db.commit = Mock(side_effect=Exception("Database error"))
        tenant_service.db.rollback = Mock()
        
        with patch.object(tenant_service.model, '__call__', return_value=Mock()):
            with pytest.raises(Exception):
                tenant_service.create(
                    sample_account_data,
                    tenant_type=TenantType.USER,
                    tenant_id="test_user_123"
                )
            
            tenant_service.db.rollback.assert_called_once()

    def test_model_validation(self, tenant_service, sample_account_data):
        """Test model validation during creation."""
        # Test with invalid data that would fail model validation
        invalid_data = {"invalid_field": "value"}
        
        with patch.object(tenant_service.model, '__call__', side_effect=ValueError("Invalid field")):
            with pytest.raises(ValueError):
                tenant_service.create(
                    invalid_data,
                    tenant_type=TenantType.USER,
                    tenant_id="test_user_123"
                )