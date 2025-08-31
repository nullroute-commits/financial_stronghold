"""Integration tests for tagging and analytics API endpoints."""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4, UUID
from decimal import Decimal

from app.main import app
from app.core.models import User, Role
from app.financial_models import Account, Transaction, Budget
from app.tagging_models import DataTag, TagType


class TestTaggingEndpoints:
    """Test cases for tagging API endpoints."""

    def test_create_user_tag(self, client: TestClient, auth_headers, sample_data):
        """Test creating a user tag via API."""
        user, resource_id = sample_data
        
        payload = {
            "tag_type": "user",
            "tag_key": "user_id",
            "tag_value": str(user.id),
            "resource_type": "transaction",
            "resource_id": str(resource_id),
            "tag_label": "Test User Tag",
            "tag_description": "Created via API test",
            "tag_color": "#FF5733",
            "tag_metadata": {"test": "metadata"}
        }
        
        response = client.post(
            "/financial/tags",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["tag_type"] == "user"
        assert data["tag_key"] == "user_id"
        assert data["tag_value"] == str(user.id)
        assert data["resource_type"] == "transaction"
        assert data["resource_id"] == str(resource_id)
        assert data["tag_label"] == "Test User Tag"
        assert data["tag_description"] == "Created via API test"
        assert data["tag_color"] == "#FF5733"
        assert data["tag_metadata"] == {"test": "metadata"}
        assert data["is_active"] is True

    def test_create_organization_tag(self, client: TestClient, auth_headers, sample_data):
        """Test creating an organization tag via API."""
        user, resource_id = sample_data
        
        payload = {
            "tag_type": "organization",
            "tag_key": "org_id",
            "tag_value": "123",
            "resource_type": "account",
            "resource_id": str(resource_id),
            "tag_label": "Test Org Tag"
        }
        
        response = client.post(
            "/financial/tags",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["tag_type"] == "organization"
        assert data["tag_key"] == "org_id"
        assert data["tag_value"] == "123"
        assert data["resource_type"] == "account"

    def test_create_role_tag(self, client: TestClient, auth_headers, sample_data, sample_role):
        """Test creating a role tag via API."""
        user, resource_id = sample_data
        
        payload = {
            "tag_type": "role",
            "tag_key": "role_id",
            "tag_value": str(sample_role.id),
            "resource_type": "budget",
            "resource_id": str(resource_id),
            "tag_label": "Test Role Tag"
        }
        
        response = client.post(
            "/financial/tags",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["tag_type"] == "role"
        assert data["tag_key"] == "role_id"
        assert data["tag_value"] == str(sample_role.id)
        assert data["resource_type"] == "budget"

    def test_get_resource_tags(self, client: TestClient, auth_headers, sample_data):
        """Test retrieving tags for a resource."""
        user, resource_id = sample_data
        
        # First create some tags
        tag_payload = {
            "tag_type": "user",
            "tag_key": "user_id",
            "tag_value": str(user.id),
            "resource_type": "transaction",
            "resource_id": str(resource_id),
            "tag_label": "Test Tag"
        }
        
        client.post("/financial/tags", json=tag_payload, headers=auth_headers)
        
        # Now retrieve tags
        response = client.get(
            f"/financial/tags/resource/transaction/{resource_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["resource_id"] == str(resource_id)
        assert data[0]["resource_type"] == "transaction"

    def test_auto_tag_resource(self, client: TestClient, auth_headers, sample_data, sample_role):
        """Test automatic tagging of a resource."""
        user, resource_id = sample_data
        
        response = client.post(
            f"/financial/tags/auto/account/{resource_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Should have at least a user tag
        tag_types = [tag["tag_type"] for tag in data]
        assert "user" in tag_types

    def test_query_tagged_resources(self, client: TestClient, auth_headers, sample_data):
        """Test querying resources by tag filters."""
        user, resource_id = sample_data
        
        # First create a tag
        tag_payload = {
            "tag_type": "user",
            "tag_key": "user_id",
            "tag_value": str(user.id),
            "resource_type": "transaction",
            "resource_id": str(resource_id),
            "tag_label": "Test Tag"
        }
        
        client.post("/financial/tags", json=tag_payload, headers=auth_headers)
        
        # Query tagged resources
        query_payload = {"user_id": str(user.id)}
        
        response = client.post(
            "/financial/tags/query",
            params={"resource_type": "transaction"},
            json=query_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "resource_ids" in data
        assert "resource_count" in data
        assert "tag_filters" in data
        assert "resource_type" in data
        
        assert data["resource_type"] == "transaction"
        assert data["tag_filters"] == {"user_id": str(user.id)}
        assert str(resource_id) in data["resource_ids"]


class TestAnalyticsEndpoints:
    """Test cases for analytics API endpoints."""

    def test_compute_tag_metrics(self, client: TestClient, auth_headers, sample_transactions):
        """Test computing metrics for tagged resources."""
        user, transaction_ids = sample_transactions
        
        # Create tags for transactions
        for tx_id in transaction_ids:
            tag_payload = {
                "tag_type": "user",
                "tag_key": "user_id",
                "tag_value": str(user.id),
                "resource_type": "transaction",
                "resource_id": str(tx_id),
                "tag_label": "User Transaction"
            }
            client.post("/financial/tags", json=tag_payload, headers=auth_headers)
        
        # Compute metrics
        request_payload = {
            "tag_filters": {"user_id": str(user.id)},
            "resource_types": ["transaction"]
        }
        
        response = client.post(
            "/financial/analytics/compute",
            params={"resource_type": "transaction"},
            json=request_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["resource_type"] == "transaction"
        assert data["total_count"] >= 2
        assert "total_amount" in data
        assert "average_amount" in data

    def test_get_analytics_summary(self, client: TestClient, auth_headers, sample_data):
        """Test getting comprehensive analytics summary."""
        user, resource_id = sample_data
        
        request_payload = {
            "tag_filters": {"user_id": str(user.id)},
            "resource_types": ["transaction", "account", "budget"]
        }
        
        response = client.post(
            "/financial/analytics/summary",
            json=request_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tenant_info" in data
        assert "tag_filters" in data
        assert "resource_metrics" in data
        assert "generated_at" in data
        
        assert data["tag_filters"] == {"user_id": str(user.id)}
        assert "transaction" in data["resource_metrics"]
        assert "account" in data["resource_metrics"]
        assert "budget" in data["resource_metrics"]

    def test_create_analytics_view(self, client: TestClient, auth_headers, sample_data):
        """Test creating an analytics view."""
        user, resource_id = sample_data
        
        payload = {
            "view_name": "Test Analytics View",
            "view_description": "A test analytics view",
            "tag_filters": {"user_id": str(user.id)},
            "resource_types": ["transaction", "account"],
            "cache_ttl_seconds": 1800,
            "auto_refresh": True
        }
        
        response = client.post(
            "/financial/analytics/views",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["view_name"] == "Test Analytics View"
        assert data["view_description"] == "A test analytics view"
        assert data["tag_filters"] == {"user_id": str(user.id)}
        assert data["resource_types"] == ["transaction", "account"]
        assert data["cache_ttl_seconds"] == 1800
        assert data["auto_refresh"] is True
        assert data["computation_status"] == "completed"
        assert "metrics" in data

    def test_list_analytics_views(self, client: TestClient, auth_headers, sample_data):
        """Test listing analytics views."""
        user, resource_id = sample_data
        
        # Create a view first
        payload = {
            "view_name": "List Test View",
            "tag_filters": {"user_id": str(user.id)},
            "resource_types": ["transaction"]
        }
        
        client.post("/financial/analytics/views", json=payload, headers=auth_headers)
        
        # List views
        response = client.get(
            "/financial/analytics/views",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        
        view = data[0]
        assert "view_name" in view
        assert "tag_filters" in view
        assert "resource_types" in view
        assert "computation_status" in view

    def test_get_analytics_view(self, client: TestClient, auth_headers, sample_data):
        """Test getting a specific analytics view."""
        user, resource_id = sample_data
        
        # Create a view first
        payload = {
            "view_name": "Get Test View",
            "tag_filters": {"user_id": str(user.id)},
            "resource_types": ["transaction"]
        }
        
        create_response = client.post(
            "/financial/analytics/views", 
            json=payload, 
            headers=auth_headers
        )
        view_id = create_response.json()["id"]
        
        # Get the view
        response = client.get(
            f"/financial/analytics/views/{view_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == view_id
        assert data["view_name"] == "Get Test View"
        assert data["tag_filters"] == {"user_id": str(user.id)}

    def test_refresh_analytics_view(self, client: TestClient, auth_headers, sample_data):
        """Test refreshing an analytics view."""
        user, resource_id = sample_data
        
        # Create a view first
        payload = {
            "view_name": "Refresh Test View",
            "tag_filters": {"user_id": str(user.id)},
            "resource_types": ["transaction"]
        }
        
        create_response = client.post(
            "/financial/analytics/views",
            json=payload,
            headers=auth_headers
        )
        view_id = create_response.json()["id"]
        
        # Refresh the view
        response = client.post(
            f"/financial/analytics/views/{view_id}/refresh",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == view_id
        assert data["computation_status"] == "completed"
        assert "last_computed" in data

    def test_get_dashboard_analytics(self, client: TestClient, auth_headers, sample_data):
        """Test getting dashboard with analytics filtering."""
        user, resource_id = sample_data
        
        response = client.get(
            "/financial/dashboard/analytics",
            params={"user_id": str(user.id)},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tenant_info" in data
        assert "tag_filters" in data
        assert "resource_metrics" in data
        assert "generated_at" in data
        
        assert data["tag_filters"] == {"user_id": str(user.id)}

    def test_dashboard_analytics_multi_filter(self, client: TestClient, auth_headers, sample_data, sample_role):
        """Test dashboard analytics with multiple filters."""
        user, resource_id = sample_data
        
        response = client.get(
            "/financial/dashboard/analytics",
            params={
                "user_id": str(user.id),
                "role_id": str(sample_role.id)
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        expected_filters = {
            "user_id": str(user.id),
            "role_id": str(sample_role.id)
        }
        assert data["tag_filters"] == expected_filters


# Test fixtures
@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {
        "Authorization": "Bearer test_token",
        "X-Tenant-Type": "user",
        "X-Tenant-ID": "test_user_123"
    }


@pytest.fixture
def sample_data():
    """Create sample user and resource ID for testing."""
    # This would create actual data in a test database
    user_id = uuid4()
    resource_id = uuid4()
    
    # Mock user object
    class MockUser:
        def __init__(self, id):
            self.id = id
    
    return MockUser(user_id), resource_id


@pytest.fixture
def sample_role():
    """Create a sample role for testing."""
    role_id = uuid4()
    
    class MockRole:
        def __init__(self, id):
            self.id = id
    
    return MockRole(role_id)


@pytest.fixture
def sample_transactions(sample_data):
    """Create sample transactions for testing."""
    user, _ = sample_data
    transaction_ids = [uuid4(), uuid4(), uuid4()]
    
    return user, transaction_ids


class TestTaggingValidation:
    """Test input validation for tagging endpoints."""

    def test_invalid_tag_color(self, client: TestClient, auth_headers, sample_data):
        """Test validation of tag color format."""
        user, resource_id = sample_data
        
        payload = {
            "tag_type": "user",
            "tag_key": "user_id",
            "tag_value": str(user.id),
            "resource_type": "transaction",
            "resource_id": str(resource_id),
            "tag_color": "invalid_color"  # Invalid hex color
        }
        
        response = client.post(
            "/financial/tags",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self, client: TestClient, auth_headers):
        """Test validation of required fields."""
        payload = {
            "tag_type": "user",
            # Missing required fields
        }
        
        response = client.post(
            "/financial/tags",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error

    def test_invalid_resource_id_format(self, client: TestClient, auth_headers, sample_data):
        """Test validation of UUID format for resource_id."""
        user, _ = sample_data
        
        payload = {
            "tag_type": "user",
            "tag_key": "user_id",
            "tag_value": str(user.id),
            "resource_type": "transaction",
            "resource_id": "not_a_uuid"  # Invalid UUID
        }
        
        response = client.post(
            "/financial/tags",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestAnalyticsErrorHandling:
    """Test error handling in analytics endpoints."""

    def test_nonexistent_analytics_view(self, client: TestClient, auth_headers):
        """Test handling of nonexistent analytics view."""
        fake_view_id = str(uuid4())
        
        response = client.get(
            f"/financial/analytics/views/{fake_view_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        
        # Test refresh of nonexistent view
        response = client.post(
            f"/financial/analytics/views/{fake_view_id}/refresh",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_invalid_tag_filters(self, client: TestClient, auth_headers):
        """Test handling of invalid tag filters."""
        request_payload = {
            "tag_filters": {},  # Empty filters
            "resource_types": ["transaction"]
        }
        
        response = client.post(
            "/financial/analytics/compute",
            params={"resource_type": "transaction"},
            json=request_payload,
            headers=auth_headers
        )
        
        # Should succeed but return empty results
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0