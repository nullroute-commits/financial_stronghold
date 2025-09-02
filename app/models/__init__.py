"""
Models package for Financial Stronghold application.
Organizes models by functionality.

IMPORTANT: This package shadows a legacy `app/models.py` module. To ensure
all Django models are registered (including the custom `User`), we import
the core Django ORM models here so Django sees them when loading `app.models`.
"""

from .import_models import (
    ImportJob,
    ImportTemplate, 
    ImportValidationError,
    TransactionCategory,
    ImportedTransaction,
    FileUpload,
    MLModel
)

# Ensure core models (including the custom User) are registered under app.models
from ..django_models import (
    BaseModel,
    User,
    Role,
    Permission,
    AuditLog,
    SystemConfiguration,
    TenantType,
    TenantMixin,
    Organization,
    UserOrganizationLink,
    Account,
    Transaction,
    Fee,
    Budget,
)

__all__ = [
    # Core models
    'BaseModel',
    'User',
    'Role',
    'Permission',
    'AuditLog',
    'SystemConfiguration',
    'TenantType',
    'TenantMixin',
    'Organization',
    'UserOrganizationLink',
    'Account',
    'Transaction',
    'Fee',
    'Budget',
    # Import feature models
    'ImportJob',
    'ImportTemplate',
    'ImportValidationError', 
    'TransactionCategory',
    'ImportedTransaction',
    'FileUpload',
    'MLModel'
]