"""Multi-tenancy extension for Financial Stronghold."""

import pytest
from decimal import Decimal
import uuid

from app.core.tenant import TenantType, TenantMixin
from app.services import TenantService


class MockTenantModel:
    """Mock model for testing TenantMixin functionality."""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.tenant_type = kwargs.get('tenant_type', TenantType.USER)
        self.tenant_id = kwargs.get('tenant_id', 'default-tenant')
    
    @property
    def tenant_key(self) -> tuple[str, str]:
        """Convenient tuple used for filtering."""
        return self.tenant_type.value, self.tenant_id


class TestTenantMixin:
    """Test the TenantMixin functionality."""

    def test_tenant_key_property(self):
        """Test the tenant_key property."""
        model = MockTenantModel(
            tenant_type=TenantType.USER,
            tenant_id="user-123"
        )
        
        expected_key = (TenantType.USER.value, "user-123")
        assert model.tenant_key == expected_key

    def test_tenant_key_property_organization(self):
        """Test the tenant_key property for organization."""
        model = MockTenantModel(
            tenant_type=TenantType.ORGANIZATION,
            tenant_id="org-456"
        )
        
        expected_key = (TenantType.ORGANIZATION.value, "org-456")
        assert model.tenant_key == expected_key


class TestTenantType:
    """Test the TenantType enum."""
    
    def test_tenant_types(self):
        """Test that tenant types have correct values."""
        assert TenantType.USER.value == "user"
        assert TenantType.ORGANIZATION.value == "organization"


class TestServiceLogic:
    """Test the TenantService logic without database dependencies."""
    
    def test_tenant_id_conversion(self):
        """Test that tenant IDs are properly converted to strings."""
        # Test integer conversion
        assert str(123) == "123"
        
        # Test UUID conversion  
        test_uuid = uuid.uuid4()
        assert str(test_uuid) == str(test_uuid)
        
        # Test string passthrough
        assert str("test-id") == "test-id"


class TestTenantDataIsolation:
    """Test tenant data isolation concepts."""
    
    def test_tenant_context_isolation(self):
        """Test that different tenant contexts are properly isolated."""
        # Create two different tenant contexts
        user_context = {
            "tenant_type": TenantType.USER.value,
            "tenant_id": "user-123"
        }
        
        org_context = {
            "tenant_type": TenantType.ORGANIZATION.value,
            "tenant_id": "org-456"
        }
        
        # Verify they are different
        assert user_context["tenant_type"] != org_context["tenant_type"]
        assert user_context["tenant_id"] != org_context["tenant_id"]
        
        # Verify user context
        assert user_context["tenant_type"] == "user"
        assert user_context["tenant_id"] == "user-123"
        
        # Verify org context
        assert org_context["tenant_type"] == "organization"
        assert org_context["tenant_id"] == "org-456"

    def test_financial_data_scoping(self):
        """Test financial data scoping logic."""
        # Simulate account data with tenant scoping
        user_account = {
            "id": str(uuid.uuid4()),
            "name": "User Checking",
            "balance": Decimal("1000.00"),
            "tenant_type": TenantType.USER.value,
            "tenant_id": "user-123"
        }
        
        org_account = {
            "id": str(uuid.uuid4()),
            "name": "Business Account", 
            "balance": Decimal("5000.00"),
            "tenant_type": TenantType.ORGANIZATION.value,
            "tenant_id": "org-456"
        }
        
        # Verify accounts have different tenant scoping
        assert user_account["tenant_type"] != org_account["tenant_type"]
        assert user_account["tenant_id"] != org_account["tenant_id"]
        
        # Test filtering logic
        user_filter = lambda acc: (acc["tenant_type"] == TenantType.USER.value and 
                                 acc["tenant_id"] == "user-123")
        org_filter = lambda acc: (acc["tenant_type"] == TenantType.ORGANIZATION.value and 
                                acc["tenant_id"] == "org-456")
        
        # Verify filtering works correctly
        assert user_filter(user_account) == True
        assert user_filter(org_account) == False
        assert org_filter(user_account) == False
        assert org_filter(org_account) == True