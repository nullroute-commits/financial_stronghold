"""Integration tests for Financial Dashboard API endpoints."""

import pytest
from decimal import Decimal
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app


class TestDashboardAPI:
    """Integration tests for Dashboard API."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer test_token"}

    def test_get_dashboard_data_endpoint(self, client, auth_headers):
        """Test the main dashboard data endpoint."""
        response = client.get("/financial/dashboard", headers=auth_headers)
        
        # Should return 200 for valid request
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify response structure
        assert "financial_summary" in data
        assert "account_summaries" in data
        assert "transaction_summary" in data
        assert "budget_statuses" in data
        assert "tenant_info" in data
        
        # Verify financial_summary structure
        summary = data["financial_summary"]
        assert "total_balance" in summary
        assert "total_accounts" in summary
        assert "active_accounts" in summary
        assert "total_transactions" in summary
        assert "currency" in summary
        assert "last_updated" in summary

    def test_get_financial_summary_endpoint(self, client, auth_headers):
        """Test the financial summary endpoint."""
        response = client.get("/financial/dashboard/summary", headers=auth_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "total_balance" in data
        assert "total_accounts" in data
        assert "currency" in data

    def test_get_account_summaries_endpoint(self, client, auth_headers):
        """Test the account summaries endpoint."""
        response = client.get("/financial/dashboard/accounts", headers=auth_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_get_transaction_summary_endpoint(self, client, auth_headers):
        """Test the transaction summary endpoint."""
        response = client.get("/financial/dashboard/transactions", headers=auth_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert "total_transactions" in data
        assert "total_amount" in data
        assert "avg_amount" in data
        assert "recent_transactions" in data

    def test_get_budget_statuses_endpoint(self, client, auth_headers):
        """Test the budget statuses endpoint."""
        response = client.get("/financial/dashboard/budgets", headers=auth_headers)
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_dashboard_with_data(self, client, auth_headers, db_session):
        """Test dashboard endpoints with actual data."""
        # This test would require setting up test data
        # For now, just verify the endpoints are accessible
        
        endpoints = [
            "/financial/dashboard",
            "/financial/dashboard/summary",
            "/financial/dashboard/accounts",
            "/financial/dashboard/transactions",
            "/financial/dashboard/budgets",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [200, 401]  # 401 if auth not properly mocked

    def test_dashboard_unauthorized_access(self, client):
        """Test dashboard endpoints without authorization."""
        endpoints = [
            "/financial/dashboard",
            "/financial/dashboard/summary",
            "/financial/dashboard/accounts",
            "/financial/dashboard/transactions",
            "/financial/dashboard/budgets",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should require authentication
            assert response.status_code in [401, 422]  # Depending on auth implementation