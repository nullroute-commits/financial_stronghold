"""
Django models for the Financial Stronghold application.
Import all the Django-native models to make them available to Django's ORM.

Last updated: 2025-08-31 by AI Assistant
"""

# Import all models from django_models to make them available to Django
from .django_models import (  # Core models; Multi-tenancy models; Financial models
    Account,
    AuditLog,
    BaseModel,
    Budget,
    Fee,
    Organization,
    Permission,
    Role,
    SystemConfiguration,
    TenantMixin,
    TenantType,
    Transaction,
    User,
    UserOrganizationLink,
)

# Make all models available at module level
__all__ = [
    "BaseModel",
    "User",
    "Role",
    "Permission",
    "AuditLog",
    "SystemConfiguration",
    "TenantType",
    "TenantMixin",
    "Organization",
    "UserOrganizationLink",
    "Account",
    "Transaction",
    "Fee",
    "Budget",
]
