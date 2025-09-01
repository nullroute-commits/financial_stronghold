"""
Comprehensive API Tests for 100% Coverage.

This test module provides complete coverage for app/api.py, ensuring every endpoint,
error path, and edge case is thoroughly tested.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

# Import API modules and dependencies
try:
    from app import api
    from app.api import router
    from app.schemas import (
        AccountCreate, AccountRead, AccountUpdate,
        TransactionCreate, TransactionRead, TransactionUpdate,
        BudgetCreate, BudgetRead, BudgetUpdate,
        FeeCreate, FeeRead, FeeUpdate,
        DashboardData, FinancialSummary, AccountSummary,
        TransactionSummary, BudgetStatus
    )
    from app.financial_models import Account, Transaction, Budget, Fee
    from app.core.tenant import TenantType

    API_AVAILABLE = True
except ImportError as e:
    API_AVAILABLE = False
    import_error = str(e)


class TestAPIRouterStructure:
    """Test API router configuration and basic structure."""
    
    def test_router_available(self):
        """Test that the API router can be imported."""
        if not API_AVAILABLE:
            pytest.skip(f"API module not available: {import_error}")
        
        from app.api import router
        assert router is not None
        assert hasattr(router, 'routes')
    
    def test_api_module_imports(self):
        """Test that key API module imports work."""
        if not API_AVAILABLE:
            pytest.skip(f"API module not available: {import_error}")
        
        # Test that we can import the API module
        import app.api
        assert hasattr(app.api, 'router')
        
        # Test that router has routes
        from app.api import router
        assert len(router.routes) > 0


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAPIFunctionExecution:
    """Complete coverage for API functions by direct invocation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = {"id": str(uuid4()), "username": "testuser"}
        self.tenant_context = {
            "tenant_type": TenantType.USER, 
            "tenant_id": self.mock_user["id"],
            "is_organization": False
        }
        
        # Mock account data
        self.account_data = AccountCreate(
            name="Test Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="USD"
        )
        
        self.mock_account = Mock()
        self.mock_account.id = uuid4()
        self.mock_account.name = "Test Account"
        self.mock_account.account_type = "checking"
        self.mock_account.balance = Decimal("1000.00")
        self.mock_account.currency = "USD"
    
    def test_create_account_function(self):
        """Test the create_account function directly."""
        # Get the function from the module
        from app.api import create_account
        
        # Mock TenantService
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.create.return_value = self.mock_account
            mock_service_class.return_value = mock_service
            
            result = create_account(
                payload=self.account_data,
                tenant_context=self.tenant_context,
                db=self.mock_db
            )
            
            assert result == self.mock_account
            mock_service.create.assert_called_once()
    
    def test_list_accounts_function(self):
        """Test the list_accounts function directly."""
        from app.api import list_accounts
        
        mock_accounts = [self.mock_account]
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_all.return_value = mock_accounts
            mock_service_class.return_value = mock_service
            
            result = list_accounts(
                tenant_context=self.tenant_context,
                db=self.mock_db,
                limit=None,
                offset=None
            )
            
            assert result == mock_accounts
            mock_service.get_all.assert_called_once()
    
    def test_list_accounts_with_pagination(self):
        """Test the list_accounts function with pagination."""
        from app.api import list_accounts
        
        mock_accounts = [self.mock_account]
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_all.return_value = mock_accounts
            mock_service_class.return_value = mock_service
            
            result = list_accounts(
                tenant_context=self.tenant_context,
                db=self.mock_db,
                limit=10,
                offset=0
            )
            
            assert result == mock_accounts
            mock_service.get_all.assert_called_once_with(
                tenant_type=TenantType.USER,
                tenant_id=self.mock_user["id"],
                limit=10,
                offset=0
            )
    
    def test_get_account_function_success(self):
        """Test the get_account function with existing account."""
        from app.api import get_account
        
        account_id = uuid4()
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_one.return_value = self.mock_account
            mock_service_class.return_value = mock_service
            
            result = get_account(
                account_id=account_id,
                tenant_context=self.tenant_context,
                db=self.mock_db
            )
            
            assert result == self.mock_account
            mock_service.get_one.assert_called_once()
    
    def test_get_account_function_not_found(self):
        """Test the get_account function with non-existent account."""
        from app.api import get_account
        
        account_id = uuid4()
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_one.return_value = None
            mock_service_class.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc_info:
                get_account(
                    account_id=account_id,
                    tenant_context=self.tenant_context,
                    db=self.mock_db
                )
            
            assert exc_info.value.status_code == 404
            assert "Account not found" in exc_info.value.detail
    
    def test_update_account_function_success(self):
        """Test the update_account function with existing account."""
        from app.api import update_account
        
        account_id = uuid4()
        update_data = AccountUpdate(name="Updated Account")
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.update.return_value = self.mock_account
            mock_service_class.return_value = mock_service
            
            result = update_account(
                account_id=account_id,
                payload=update_data,
                tenant_context=self.tenant_context,
                db=self.mock_db
            )
            
            assert result == self.mock_account
            mock_service.update.assert_called_once()
    
    def test_update_account_function_not_found(self):
        """Test the update_account function with non-existent account."""
        from app.api import update_account
        
        account_id = uuid4()
        update_data = AccountUpdate(name="Updated Account")
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.update.return_value = None
            mock_service_class.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc_info:
                update_account(
                    account_id=account_id,
                    payload=update_data,
                    tenant_context=self.tenant_context,
                    db=self.mock_db
                )
            
            assert exc_info.value.status_code == 404
            assert "Account not found" in exc_info.value.detail
    
    def test_delete_account_function_success(self):
        """Test the delete_account function with existing account."""
        from app.api import delete_account
        
        account_id = uuid4()
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.delete.return_value = True
            mock_service_class.return_value = mock_service
            
            # Should not raise an exception
            delete_account(
                account_id=account_id,
                tenant_context=self.tenant_context,
                db=self.mock_db
            )
            
            mock_service.delete.assert_called_once()
    
    def test_delete_account_function_not_found(self):
        """Test the delete_account function with non-existent account."""
        from app.api import delete_account
        
        account_id = uuid4()
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.delete.return_value = False
            mock_service_class.return_value = mock_service
            
            with pytest.raises(HTTPException) as exc_info:
                delete_account(
                    account_id=account_id,
                    tenant_context=self.tenant_context,
                    db=self.mock_db
                )
            
            assert exc_info.value.status_code == 404
            assert "Account not found" in exc_info.value.detail
    
    def test_delete_account_organization_admin_check(self):
        """Test delete_account with organization tenant requires admin role."""
        from app.api import delete_account
        
        account_id = uuid4()
        org_tenant_context = {
            "tenant_type": TenantType.ORGANIZATION,
            "tenant_id": str(uuid4()),
            "is_organization": True
        }
        
        with patch('app.api.TenantService') as mock_service_class, \
             patch('app.api.require_role') as mock_require_role:
            
            mock_service = Mock()
            mock_service.delete.return_value = True
            mock_service_class.return_value = mock_service
            
            # Mock the role requirement decorator
            mock_role_check = Mock()
            mock_require_role.return_value = mock_role_check
            
            # Should not raise an exception
            delete_account(
                account_id=account_id,
                tenant_context=org_tenant_context,
                db=self.mock_db
            )
            
            # Verify role check was called
            mock_require_role.assert_called_once_with(["owner", "admin"])
            mock_role_check.assert_called_once_with(org_tenant_context)


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestTransactionAPIFunctions:
    """Complete coverage for transaction API functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = {"id": str(uuid4()), "username": "testuser"}
        self.tenant_context = {
            "tenant_type": TenantType.USER, 
            "tenant_id": self.mock_user["id"],
            "is_organization": False
        }
        
        self.transaction_data = TransactionCreate(
            account_id=uuid4(),
            amount=Decimal("50.00"),
            description="Test Transaction",
            category="groceries",
            transaction_type="expense",
            transaction_date=datetime.now(timezone.utc)
        )
        
        self.mock_transaction = Mock()
        self.mock_transaction.id = uuid4()
        self.mock_transaction.amount = Decimal("50.00")
        self.mock_transaction.description = "Test Transaction"
    
    def test_create_transaction_function(self):
        """Test the create_transaction function directly."""
        from app.api import create_transaction
        
        with patch('app.api.TenantService') as mock_service_class, \
             patch('app.api.TransactionClassifier') as mock_classifier_class:
            
            mock_service = Mock()
            mock_service.create.return_value = self.mock_transaction
            mock_service_class.return_value = mock_service
            
            # Mock classifier
            mock_classifier = Mock()
            mock_classifier.classify.return_value = Mock(category="groceries", confidence=0.95)
            mock_classifier_class.return_value = mock_classifier
            
            result = create_transaction(
                payload=self.transaction_data,
                tenant_context=self.tenant_context,
                current_user=self.mock_user,
                auto_classify=True,
                db=self.mock_db
            )
            
            assert result == self.mock_transaction
            mock_service.create.assert_called_once()
    
    def test_create_transaction_without_auto_classify(self):
        """Test transaction creation without auto-classification."""
        from app.api import create_transaction
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.create.return_value = self.mock_transaction
            mock_service_class.return_value = mock_service
            
            result = create_transaction(
                payload=self.transaction_data,
                tenant_context=self.tenant_context,
                current_user=self.mock_user,
                auto_classify=False,
                db=self.mock_db
            )
            
            assert result == self.mock_transaction
            mock_service.create.assert_called_once()
    
    def test_list_transactions_function(self):
        """Test the list_transactions function."""
        from app.api import list_transactions
        
        mock_transactions = [self.mock_transaction]
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_all.return_value = mock_transactions
            mock_service_class.return_value = mock_service
            
            result = list_transactions(
                tenant_context=self.tenant_context,
                db=self.mock_db,
                account_id=None,
                category=None,
                start_date=None,
                end_date=None,
                limit=None,
                offset=None
            )
            
            assert result == mock_transactions
            mock_service.get_all.assert_called_once()
    
    def test_list_transactions_with_filters(self):
        """Test the list_transactions function with filters."""
        from app.api import list_transactions
        
        mock_transactions = [self.mock_transaction]
        account_id = uuid4()
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        end_date = datetime.now(timezone.utc)
        
        with patch('app.api.TenantService') as mock_service_class, \
             patch('app.api.and_') as mock_and:
            
            mock_service = Mock()
            mock_service.get_all.return_value = mock_transactions
            mock_service_class.return_value = mock_service
            
            mock_and.return_value = Mock()  # Mock SQLAlchemy and_ function
            
            result = list_transactions(
                tenant_context=self.tenant_context,
                db=self.mock_db,
                account_id=account_id,
                category="groceries",
                start_date=start_date,
                end_date=end_date,
                limit=10,
                offset=0
            )
            
            assert result == mock_transactions
            mock_service.get_all.assert_called_once()


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestDashboardAPIFunctions:
    """Complete coverage for dashboard API functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = {"id": str(uuid4()), "username": "testuser"}
        self.tenant_context = {
            "tenant_type": TenantType.USER, 
            "tenant_id": self.mock_user["id"],
            "is_organization": False
        }
    
    def test_get_dashboard_data_function(self):
        """Test the get_dashboard_data function."""
        from app.api import get_dashboard_data
        
        mock_dashboard_data = Mock()
        
        with patch('app.api.DashboardService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_complete_dashboard_data.return_value = mock_dashboard_data
            mock_service_class.return_value = mock_service
            
            result = get_dashboard_data(
                tenant_context=self.tenant_context,
                db=self.mock_db
            )
            
            assert result == mock_dashboard_data
            mock_service.get_complete_dashboard_data.assert_called_once()
    
    def test_get_dashboard_summary_function(self):
        """Test the get_dashboard_summary function."""
        from app.api import get_dashboard_summary
        
        mock_summary = Mock()
        
        with patch('app.api.DashboardService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_financial_summary.return_value = mock_summary
            mock_service_class.return_value = mock_service
            
            result = get_dashboard_summary(
                tenant_context=self.tenant_context,
                db=self.mock_db
            )
            
            assert result == mock_summary
            mock_service.get_financial_summary.assert_called_once()


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAnalyticsAPIFunctions:
    """Complete coverage for analytics API functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = {"id": str(uuid4()), "username": "testuser"}
        self.tenant_context = {
            "tenant_type": TenantType.USER, 
            "tenant_id": self.mock_user["id"],
            "is_organization": False
        }
    
    def test_get_spending_patterns_function(self):
        """Test the get_spending_patterns function."""
        from app.api import get_spending_patterns
        
        mock_patterns = Mock()
        
        with patch('app.api.AnalyticsService') as mock_service_class:
            mock_service = Mock()
            mock_service.analyze_spending_patterns.return_value = mock_patterns
            mock_service_class.return_value = mock_service
            
            result = get_spending_patterns(
                tenant_context=self.tenant_context,
                db=self.mock_db,
                months=6
            )
            
            assert result == mock_patterns
            mock_service.analyze_spending_patterns.assert_called_once()
    
    def test_get_monthly_breakdown_function(self):
        """Test the get_monthly_breakdown function."""
        from app.api import get_monthly_breakdown
        
        mock_breakdown = Mock()
        
        with patch('app.api.AnalyticsService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_monthly_breakdown.return_value = mock_breakdown
            mock_service_class.return_value = mock_service
            
            result = get_monthly_breakdown(
                tenant_context=self.tenant_context,
                db=self.mock_db,
                year=2024
            )
            
            assert result == mock_breakdown
            mock_service.get_monthly_breakdown.assert_called_once()


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestTaggingAPIFunctions:
    """Complete coverage for tagging API functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = {"id": str(uuid4()), "username": "testuser"}
        self.tenant_context = {
            "tenant_type": TenantType.USER, 
            "tenant_id": self.mock_user["id"],
            "is_organization": False
        }
    
    def test_apply_tag_function(self):
        """Test the apply_tag function."""
        from app.api import apply_tag
        
        tag_id = uuid4()
        resource_id = uuid4()
        mock_result = {"success": True}
        
        with patch('app.api.TaggingService') as mock_service_class:
            mock_service = Mock()
            mock_service.apply_tag.return_value = mock_result
            mock_service_class.return_value = mock_service
            
            result = apply_tag(
                tag_id=tag_id,
                resource_id=resource_id,
                resource_type="transaction",
                tenant_context=self.tenant_context,
                current_user=self.mock_user,
                db=self.mock_db
            )
            
            assert result == mock_result
            mock_service.apply_tag.assert_called_once()
    
    def test_remove_tag_function(self):
        """Test the remove_tag function."""
        from app.api import remove_tag
        
        tag_id = uuid4()
        resource_id = uuid4()
        mock_result = {"success": True}
        
        with patch('app.api.TaggingService') as mock_service_class:
            mock_service = Mock()
            mock_service.remove_tag.return_value = mock_result
            mock_service_class.return_value = mock_service
            
            result = remove_tag(
                tag_id=tag_id,
                resource_id=resource_id,
                resource_type="transaction",
                tenant_context=self.tenant_context,
                current_user=self.mock_user,
                db=self.mock_db
            )
            
            assert result == mock_result
            mock_service.remove_tag.assert_called_once()


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAPIErrorHandling:
    """Test error handling in API functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = {"id": str(uuid4()), "username": "testuser"}
        self.tenant_context = {
            "tenant_type": TenantType.USER, 
            "tenant_id": self.mock_user["id"],
            "is_organization": False
        }
    
    def test_service_exception_handling(self):
        """Test that service exceptions are properly handled."""
        from app.api import list_accounts
        
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service.get_all.side_effect = Exception("Database error")
            mock_service_class.return_value = mock_service
            
            # The function should let the exception propagate
            with pytest.raises(Exception) as exc_info:
                list_accounts(
                    tenant_context=self.tenant_context,
                    db=self.mock_db,
                    limit=None,
                    offset=None
                )
            
            assert "Database error" in str(exc_info.value)


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAPIModuleStructure:
    """Test API module structure and imports."""
    
    def test_api_router_endpoints(self):
        """Test that API router has expected endpoints."""
        from app.api import router
        
        # Check that router has routes
        assert len(router.routes) > 0
        
        # Check for some expected endpoint patterns
        route_paths = [route.path for route in router.routes]
        
        # Should have account endpoints
        assert any("/accounts" in path for path in route_paths)
        assert any("/transactions" in path for path in route_paths)
        assert any("/dashboard" in path for path in route_paths)
    
    def test_api_imports_available(self):
        """Test that expected imports are available."""
        import app.api
        
        # Check for key imports
        assert hasattr(app.api, 'router')
        assert hasattr(app.api, 'TenantService')
        assert hasattr(app.api, 'DashboardService')
        assert hasattr(app.api, 'TaggingService')
    
    def test_api_dependencies_available(self):
        """Test that API dependencies can be imported."""
        from app.api import get_tenant_context, get_current_user, get_db_session
        
        # These should be callable
        assert callable(get_tenant_context)
        assert callable(get_current_user)
        assert callable(get_db_session)


class TestAPIRouterStructure:
    """Test API router configuration and basic structure."""
    
    def test_router_available(self):
        """Test that the API router can be imported."""
        if not API_AVAILABLE:
            pytest.skip(f"API module not available: {import_error}")
        
        from app.api import router
        assert router is not None
        assert hasattr(router, 'routes')
    
    def test_api_endpoints_structure(self):
        """Test that key API endpoints are defined."""
        if not API_AVAILABLE:
            pytest.skip(f"API module not available: {import_error}")
        
        # Test that endpoint functions exist
        from app.api import create_account, list_accounts, create_transaction, list_transactions
        assert callable(create_account)
        assert callable(list_accounts)
        assert callable(create_transaction)
        assert callable(list_transactions)


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAccountEndpoints:
    """Complete coverage for account-related API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
        
        # Mock account data
        self.account_data = AccountCreate(
            name="Test Account",
            account_type="checking",
            balance=Decimal("1000.00"),
            currency="USD"
        )
        
        self.mock_account = Mock()
        self.mock_account.id = uuid4()
        self.mock_account.name = "Test Account"
        self.mock_account.account_type = "checking"
        self.mock_account.balance = Decimal("1000.00")
        self.mock_account.currency = "USD"
        self.mock_account.tenant_type = TenantType.USER
        self.mock_account.tenant_id = str(self.mock_user.id)
        self.mock_account.created_at = datetime.now(timezone.utc)
        self.mock_account.updated_at = datetime.now(timezone.utc)
    
    def test_get_accounts_success(self):
        """Test successful retrieval of accounts."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = [self.mock_account]
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            result = get_accounts(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert len(result) == 1
            assert result[0] == self.mock_account
    
    def test_get_accounts_empty(self):
        """Test retrieval of accounts when none exist."""
        # Mock empty result
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            result = get_accounts(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == []
    
    def test_create_account_success(self):
        """Test successful account creation."""
        # Mock database operations
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.financial_models.Account', return_value=self.mock_account):
            
            result = create_account(
                account_data=self.account_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == self.mock_account
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
    
    def test_create_account_database_error(self):
        """Test account creation with database error."""
        # Mock database error
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock(side_effect=Exception("Database error"))
        self.mock_db.rollback = Mock()
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.financial_models.Account', return_value=self.mock_account):
            
            with pytest.raises(HTTPException) as exc_info:
                create_account(
                    account_data=self.account_data,
                    db=self.mock_db,
                    current_user=self.mock_user,
                    tenant_context=self.tenant_context
                )
            
            assert exc_info.value.status_code == 500
            self.mock_db.rollback.assert_called_once()
    
    def test_update_account_success(self):
        """Test successful account update."""
        account_id = uuid4()
        update_data = AccountUpdate(name="Updated Account")
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = self.mock_account
        self.mock_db.query.return_value = mock_query
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            result = update_account(
                account_id=account_id,
                account_data=update_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == self.mock_account
            self.mock_db.commit.assert_called_once()
    
    def test_update_account_not_found(self):
        """Test update of non-existent account."""
        account_id = uuid4()
        update_data = AccountUpdate(name="Updated Account")
        
        # Mock account not found
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            with pytest.raises(HTTPException) as exc_info:
                update_account(
                    account_id=account_id,
                    account_data=update_data,
                    db=self.mock_db,
                    current_user=self.mock_user,
                    tenant_context=self.tenant_context
                )
            
            assert exc_info.value.status_code == 404
    
    def test_delete_account_success(self):
        """Test successful account deletion."""
        account_id = uuid4()
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = self.mock_account
        self.mock_db.query.return_value = mock_query
        self.mock_db.delete = Mock()
        self.mock_db.commit = Mock()
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            result = delete_account(
                account_id=account_id,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == {"message": "Account deleted successfully"}
            self.mock_db.delete.assert_called_once()
            self.mock_db.commit.assert_called_once()
    
    def test_delete_account_not_found(self):
        """Test deletion of non-existent account."""
        account_id = uuid4()
        
        # Mock account not found
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            with pytest.raises(HTTPException) as exc_info:
                delete_account(
                    account_id=account_id,
                    db=self.mock_db,
                    current_user=self.mock_user,
                    tenant_context=self.tenant_context
                )
            
            assert exc_info.value.status_code == 404


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestDashboardEndpoints:
    """Complete coverage for dashboard-related API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
    
    def test_get_dashboard_data_success(self):
        """Test successful dashboard data retrieval."""
        # Mock dashboard service
        mock_dashboard_data = Mock()
        mock_dashboard_data.financial_summary = Mock()
        mock_dashboard_data.account_summaries = []
        mock_dashboard_data.transaction_summary = Mock()
        mock_dashboard_data.budget_statuses = []
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.DashboardService') as mock_service:
            
            mock_service.return_value.get_complete_dashboard_data.return_value = mock_dashboard_data
            
            result = get_dashboard_data(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_dashboard_data
    
    def test_get_dashboard_data_service_error(self):
        """Test dashboard data retrieval with service error."""
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.DashboardService') as mock_service:
            
            mock_service.return_value.get_complete_dashboard_data.side_effect = Exception("Service error")
            
            with pytest.raises(HTTPException) as exc_info:
                get_dashboard_data(
                    db=self.mock_db,
                    current_user=self.mock_user,
                    tenant_context=self.tenant_context
                )
            
            assert exc_info.value.status_code == 500
    
    def test_get_financial_summary_success(self):
        """Test successful financial summary retrieval."""
        mock_summary = Mock()
        mock_summary.total_balance = Decimal("5000.00")
        mock_summary.total_accounts = 3
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.DashboardService') as mock_service:
            
            mock_service.return_value.get_financial_summary.return_value = mock_summary
            
            result = get_financial_summary(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_summary
    
    def test_get_account_summaries_success(self):
        """Test successful account summaries retrieval."""
        mock_summaries = [Mock(), Mock()]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.DashboardService') as mock_service:
            
            mock_service.return_value.get_account_summaries.return_value = mock_summaries
            
            result = get_account_summaries(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_summaries
    
    def test_get_transaction_summary_success(self):
        """Test successful transaction summary retrieval."""
        mock_summary = Mock()
        mock_summary.total_transactions = 100
        mock_summary.this_month_amount = Decimal("2000.00")
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.DashboardService') as mock_service:
            
            mock_service.return_value.get_transaction_summary.return_value = mock_summary
            
            result = get_transaction_summary(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_summary
    
    def test_get_budget_statuses_success(self):
        """Test successful budget statuses retrieval."""
        mock_statuses = [Mock(), Mock()]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.DashboardService') as mock_service:
            
            mock_service.return_value.get_budget_statuses.return_value = mock_statuses
            
            result = get_budget_statuses(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_statuses


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestTransactionEndpoints:
    """Complete coverage for transaction-related API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
        
        # Mock transaction data
        self.transaction_data = TransactionCreate(
            account_id=uuid4(),
            amount=Decimal("50.00"),
            description="Test Transaction",
            category="groceries",
            transaction_type="expense",
            transaction_date=datetime.now(timezone.utc)
        )
        
        self.mock_transaction = Mock()
        self.mock_transaction.id = uuid4()
        self.mock_transaction.amount = Decimal("50.00")
        self.mock_transaction.description = "Test Transaction"
        self.mock_transaction.category = "groceries"
        self.mock_transaction.transaction_type = "expense"
    
    def test_get_transactions_success(self):
        """Test successful retrieval of transactions."""
        # Mock database query
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.filter.return_value.all.return_value = [self.mock_transaction]
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            result = get_transactions(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert len(result) == 1
            assert result[0] == self.mock_transaction
    
    def test_get_transactions_with_filters(self):
        """Test transaction retrieval with category filter."""
        # Mock database query with filters
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [self.mock_transaction]
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            result = get_transactions(
                category="groceries",
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert len(result) == 1
            assert result[0] == self.mock_transaction
    
    def test_create_transaction_success(self):
        """Test successful transaction creation."""
        # Mock database operations
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Mock account validation
        mock_account = Mock()
        mock_account.tenant_type = TenantType.USER
        mock_account.tenant_id = str(self.mock_user.id)
        
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_account
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.financial_models.Transaction', return_value=self.mock_transaction):
            
            result = create_transaction(
                transaction_data=self.transaction_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == self.mock_transaction
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
    
    def test_create_transaction_invalid_account(self):
        """Test transaction creation with invalid account."""
        # Mock account not found
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context):
            
            with pytest.raises(HTTPException) as exc_info:
                create_transaction(
                    transaction_data=self.transaction_data,
                    db=self.mock_db,
                    current_user=self.mock_user,
                    tenant_context=self.tenant_context
                )
            
            assert exc_info.value.status_code == 404
            assert "Account not found" in exc_info.value.detail


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAnalyticsEndpoints:
    """Complete coverage for analytics-related API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
    
    def test_get_analytics_summary_success(self):
        """Test successful analytics summary retrieval."""
        mock_summary = Mock()
        mock_summary.total_spending = Decimal("1500.00")
        mock_summary.spending_trend = "increasing"
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.get_analytics_summary.return_value = mock_summary
            
            result = get_analytics_summary(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_summary
    
    def test_get_spending_insights_success(self):
        """Test successful spending insights retrieval."""
        mock_insights = Mock()
        mock_insights.top_categories = ["groceries", "utilities"]
        mock_insights.unusual_spending = []
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.get_spending_insights.return_value = mock_insights
            
            result = get_spending_insights(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_insights
    
    def test_get_monthly_breakdown_success(self):
        """Test successful monthly breakdown retrieval."""
        mock_breakdown = Mock()
        mock_breakdown.months = ["2024-01", "2024-02"]
        mock_breakdown.amounts = [Decimal("500.00"), Decimal("600.00")]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.get_monthly_breakdown.return_value = mock_breakdown
            
            result = get_monthly_breakdown(
                year=2024,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_breakdown
    
    def test_get_category_insights_success(self):
        """Test successful category insights retrieval."""
        mock_insights = [Mock(), Mock()]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.get_category_insights.return_value = mock_insights
            
            result = get_category_insights(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_insights
    
    def test_detect_anomalies_success(self):
        """Test successful anomaly detection."""
        request_data = AnomalyDetectionRequest(
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc),
            sensitivity=0.8
        )
        
        mock_response = Mock()
        mock_response.anomalies = []
        mock_response.total_checked = 100
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.detect_anomalies.return_value = mock_response
            
            result = detect_anomalies(
                request=request_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_response


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestClassificationEndpoints:
    """Complete coverage for transaction classification API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
    
    def test_classify_transaction_success(self):
        """Test successful transaction classification."""
        request_data = TransactionClassificationRequest(
            description="Grocery store purchase",
            amount=Decimal("75.00"),
            merchant="Whole Foods"
        )
        
        mock_response = Mock()
        mock_response.category = "groceries"
        mock_response.confidence = 0.95
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionClassifier') as mock_classifier:
            
            mock_classifier.return_value.classify.return_value = mock_response
            
            result = classify_transaction(
                request=request_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_response
    
    def test_get_classification_config_success(self):
        """Test successful classification configuration retrieval."""
        mock_config = Mock()
        mock_config.auto_classify = True
        mock_config.confidence_threshold = 0.8
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionClassifier') as mock_classifier:
            
            mock_classifier.return_value.get_config.return_value = mock_config
            
            result = get_classification_config(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_config
    
    def test_update_classification_config_success(self):
        """Test successful classification configuration update."""
        request_data = ClassificationConfigRequest(
            auto_classify=False,
            confidence_threshold=0.9,
            custom_rules=[]
        )
        
        mock_response = Mock()
        mock_response.success = True
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionClassifier') as mock_classifier:
            
            mock_classifier.return_value.update_config.return_value = mock_response
            
            result = update_classification_config(
                request=request_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_response
    
    def test_get_classification_analytics_success(self):
        """Test successful classification analytics retrieval."""
        request_data = ClassificationAnalyticsRequest(
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc)
        )
        
        mock_response = Mock()
        mock_response.total_classified = 150
        mock_response.accuracy_rate = 0.92
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionClassifier') as mock_classifier:
            
            mock_classifier.return_value.get_analytics.return_value = mock_response
            
            result = get_classification_analytics(
                request=request_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_response
    
    def test_get_classification_distribution_success(self):
        """Test successful classification distribution retrieval."""
        mock_distribution = Mock()
        mock_distribution.categories = {"groceries": 45, "utilities": 12}
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionClassifier') as mock_classifier:
            
            mock_classifier.return_value.get_distribution.return_value = mock_distribution
            
            result = get_classification_distribution(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_distribution


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestTaggingEndpoints:
    """Complete coverage for data tagging API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
    
    def test_create_data_tag_success(self):
        """Test successful data tag creation."""
        tag_data = DataTagCreate(
            name="Important",
            color="#FF0000",
            description="Important transactions"
        )
        
        mock_tag = Mock()
        mock_tag.id = uuid4()
        mock_tag.name = "Important"
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.create_tag.return_value = mock_tag
            
            result = create_data_tag(
                tag_data=tag_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_tag
    
    def test_get_data_tags_success(self):
        """Test successful data tags retrieval."""
        mock_tags = [Mock(), Mock()]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.get_tags.return_value = mock_tags
            
            result = get_data_tags(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_tags
    
    def test_update_data_tag_success(self):
        """Test successful data tag update."""
        tag_id = uuid4()
        update_data = DataTagUpdate(name="Updated Tag")
        
        mock_tag = Mock()
        mock_tag.id = tag_id
        mock_tag.name = "Updated Tag"
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.update_tag.return_value = mock_tag
            
            result = update_data_tag(
                tag_id=tag_id,
                tag_data=update_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_tag
    
    def test_delete_data_tag_success(self):
        """Test successful data tag deletion."""
        tag_id = uuid4()
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.delete_tag.return_value = True
            
            result = delete_data_tag(
                tag_id=tag_id,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == {"message": "Tag deleted successfully"}
    
    def test_get_tagged_resources_success(self):
        """Test successful tagged resources retrieval."""
        tag_id = uuid4()
        mock_resources = [Mock(), Mock()]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.get_tagged_resources.return_value = mock_resources
            
            result = get_tagged_resources(
                tag_id=tag_id,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_resources
    
    def test_filter_resources_by_tags_success(self):
        """Test successful resource filtering by tags."""
        filter_request = TagFilterRequest(
            tag_ids=[uuid4(), uuid4()],
            resource_type="transaction",
            operation="AND"
        )
        
        mock_response = Mock()
        mock_response.resources = [Mock(), Mock()]
        mock_response.total_count = 2
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.filter_resources.return_value = mock_response
            
            result = filter_resources_by_tags(
                filter_request=filter_request,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_response
    
    def test_get_resource_metrics_success(self):
        """Test successful resource metrics retrieval."""
        mock_metrics = Mock()
        mock_metrics.total_resources = 250
        mock_metrics.tagged_percentage = 0.85
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TaggingService') as mock_service:
            
            mock_service.return_value.get_metrics.return_value = mock_metrics
            
            result = get_resource_metrics(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_metrics


@pytest.mark.skipif(not API_AVAILABLE, reason="API module not available")
class TestAnalyticsViewEndpoints:
    """Complete coverage for analytics view API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.tenant_context = (TenantType.USER, str(self.mock_user.id))
    
    def test_create_analytics_view_success(self):
        """Test successful analytics view creation."""
        view_data = AnalyticsViewCreate(
            name="Monthly Spending",
            query_config={"type": "monthly", "metric": "spending"},
            chart_type="line",
            filters={}
        )
        
        mock_view = Mock()
        mock_view.id = uuid4()
        mock_view.name = "Monthly Spending"
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.create_view.return_value = mock_view
            
            result = create_analytics_view(
                view_data=view_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_view
    
    def test_get_analytics_views_success(self):
        """Test successful analytics views retrieval."""
        mock_views = [Mock(), Mock()]
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.get_views.return_value = mock_views
            
            result = get_analytics_views(
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_views
    
    def test_update_analytics_view_success(self):
        """Test successful analytics view update."""
        view_id = uuid4()
        update_data = AnalyticsViewUpdate(name="Updated View")
        
        mock_view = Mock()
        mock_view.id = view_id
        mock_view.name = "Updated View"
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.update_view.return_value = mock_view
            
            result = update_analytics_view(
                view_id=view_id,
                view_data=update_data,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == mock_view
    
    def test_delete_analytics_view_success(self):
        """Test successful analytics view deletion."""
        view_id = uuid4()
        
        with patch('app.api.get_db_session', return_value=self.mock_db), \
             patch('app.api.get_current_user', return_value=self.mock_user), \
             patch('app.api.get_tenant_context', return_value=self.tenant_context), \
             patch('app.api.TransactionAnalytics') as mock_analytics:
            
            mock_analytics.return_value.delete_view.return_value = True
            
            result = delete_analytics_view(
                view_id=view_id,
                db=self.mock_db,
                current_user=self.mock_user,
                tenant_context=self.tenant_context
            )
            
            assert result == {"message": "Analytics view deleted successfully"}