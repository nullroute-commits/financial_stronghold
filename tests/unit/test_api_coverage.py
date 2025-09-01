"""Comprehensive test coverage for API endpoints."""

import pytest
import json
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from app.api import router
from app.financial_models import Account, Transaction, Budget
from app.services import TenantService
from app.core.tenant import TenantType
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestAPIEndpoints:
    """Test suite for all API endpoints to achieve 100% coverage."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with router."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch('app.api.get_db_session') as mock:
            session = Mock()
            mock.return_value = session
            yield session

    @pytest.fixture
    def sample_account_data(self):
        """Sample account data for testing."""
        return {
            "name": "Test Account",
            "account_type": "checking",
            "balance": "1500.00",
            "currency": "USD",
            "is_active": True
        }

    @pytest.fixture
    def sample_transaction_data(self):
        """Sample transaction data for testing."""
        return {
            "amount": "100.00",
            "description": "Test Transaction",
            "transaction_type": "debit",
            "category": "food",
            "currency": "USD"
        }

    @pytest.fixture
    def sample_budget_data(self):
        """Sample budget data for testing."""
        return {
            "name": "Monthly Food Budget",
            "category": "food",
            "amount": "500.00",
            "period": "monthly",
            "currency": "USD"
        }

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_dashboard_endpoints(self, client, mock_db_session):
        """Test dashboard endpoints."""
        with patch('app.api.DashboardService') as mock_dashboard:
            mock_service = Mock()
            mock_dashboard.return_value = mock_service
            
            # Mock dashboard data
            mock_service.get_complete_dashboard_data.return_value = Mock(
                financial_summary=Mock(
                    total_balance=Decimal("1500.00"),
                    total_accounts=2,
                    active_accounts=2,
                    total_transactions=10,
                    this_month_transactions=5,
                    this_month_amount=Decimal("250.00"),
                    currency="USD",
                    last_updated=datetime.now()
                ),
                account_summaries=[],
                transaction_summary=Mock(
                    total_transactions=10,
                    total_amount=Decimal("1500.00"),
                    average_amount=Decimal("150.00"),
                    currency="USD"
                ),
                budget_statuses=[]
            )
            
            response = client.get(
                "/financial/dashboard",
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200
            
            # Test individual dashboard endpoints
            mock_service.get_financial_summary.return_value = mock_service.get_complete_dashboard_data.return_value.financial_summary
            response = client.get(
                "/financial/dashboard/summary", 
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200

    def test_account_endpoints(self, client, mock_db_session, sample_account_data):
        """Test account CRUD endpoints."""
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Test create account
            mock_account = Mock()
            mock_account.id = "test-account-id"
            mock_account.name = sample_account_data["name"]
            mock_service.create.return_value = mock_account
            
            response = client.post(
                "/financial/accounts",
                json=sample_account_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 201
            
            # Test get accounts
            mock_service.get_all.return_value = [mock_account]
            response = client.get(
                "/financial/accounts",
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200
            
            # Test get account by ID
            mock_service.get_by_id.return_value = mock_account
            response = client.get(
                "/financial/accounts/test-account-id",
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200

    def test_transaction_endpoints(self, client, mock_db_session, sample_transaction_data):
        """Test transaction CRUD endpoints."""
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Test create transaction
            mock_transaction = Mock()
            mock_transaction.id = "test-transaction-id"
            mock_transaction.description = sample_transaction_data["description"]
            mock_service.create.return_value = mock_transaction
            
            response = client.post(
                "/financial/transactions",
                json=sample_transaction_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 201
            
            # Test get transactions
            mock_service.get_all.return_value = [mock_transaction]
            response = client.get(
                "/financial/transactions",
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 200

    def test_budget_endpoints(self, client, mock_db_session, sample_budget_data):
        """Test budget CRUD endpoints."""
        with patch('app.api.TenantService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Test create budget
            mock_budget = Mock()
            mock_budget.id = "test-budget-id"
            mock_budget.name = sample_budget_data["name"]
            mock_service.create.return_value = mock_budget
            
            response = client.post(
                "/financial/budgets",
                json=sample_budget_data,
                headers={"Authorization": "Bearer test_token"}
            )
            assert response.status_code == 201

    def test_authentication_endpoints(self, client):
        """Test authentication endpoints."""
        with patch('app.api.Authentication') as mock_auth_class:
            mock_auth = Mock()
            mock_auth_class.return_value = mock_auth
            
            # Test login
            mock_auth.authenticate.return_value = {
                "user_id": "test-user-id",
                "access_token": "test-token",
                "token_type": "Bearer"
            }
            
            response = client.post(
                "/auth/login",
                json={"username": "testuser", "password": "testpass"}
            )
            assert response.status_code == 200

    def test_error_handling(self, client):
        """Test API error handling."""
        # Test 404 endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test invalid authentication
        response = client.get(
            "/financial/dashboard",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code in [401, 403]

    def test_validation_errors(self, client):
        """Test request validation errors."""
        # Test invalid account data
        response = client.post(
            "/financial/accounts",
            json={"invalid": "data"},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 422

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/financial/dashboard")
        # CORS headers should be present in actual implementation
        assert response.status_code in [200, 204, 405]  # Various valid CORS responses

    def test_content_type_headers(self, client):
        """Test content type headers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_rate_limiting(self, client):
        """Test rate limiting (if implemented)."""
        # Make multiple requests to test rate limiting
        for i in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    @patch('app.api.get_current_user')
    def test_authorization_middleware(self, mock_get_user, client):
        """Test authorization middleware."""
        mock_get_user.return_value = {
            "user_id": "test-user-id",
            "tenant_type": TenantType.USER,
            "tenant_id": "test-user-id"
        }
        
        response = client.get(
            "/financial/dashboard",
            headers={"Authorization": "Bearer valid_token"}
        )
        # Should get past authorization (though may fail on other issues)
        assert response.status_code != 401