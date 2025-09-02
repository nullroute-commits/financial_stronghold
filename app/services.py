"""
Django-native service layer for multi-tenant operations.
Provides generic CRUD operations using Django ORM with automatic tenant scoping.

Last updated: 2025-01-21 by AI Assistant
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from django.db import transaction
from django.db.models import Model, Q

from .django_models import TenantMixin, TenantType

ModelT = TypeVar("ModelT", bound=Model)


class DjangoTenantService(Generic[ModelT]):
    """Generic Django service that automatically filters by tenant."""

    def __init__(self, model: type[ModelT]):
        self.model = model

    def _base_queryset(self, tenant_type: str, tenant_id: Union[str, int]):
        """Create base queryset filtered by tenant."""
        if hasattr(self.model, 'tenant_type') and hasattr(self.model, 'tenant_id'):
            return self.model.objects.filter(
                tenant_type=tenant_type,
                tenant_id=str(tenant_id)
            )
        else:
            # For models without tenant scoping, return all objects
            return self.model.objects.all()

    def get_all(
        self, 
        tenant_type: str, 
        tenant_id: Union[str, int], 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[ModelT]:
        """Get all records for the tenant."""
        queryset = self._base_queryset(tenant_type, tenant_id)
        
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)

    def get_one(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> Optional[ModelT]:
        """Get one record by ID for the tenant."""
        try:
            return self._base_queryset(tenant_type, tenant_id).get(id=obj_id)
        except self.model.DoesNotExist:
            return None

    @transaction.atomic
    def create(
        self, 
        obj_data: Union[Dict[str, Any], Any], 
        tenant_type: str, 
        tenant_id: Union[str, int], 
        **extra
    ) -> ModelT:
        """Create a new record with tenant scoping."""
        # Handle both dict and Pydantic model inputs
        if hasattr(obj_data, "dict"):
            data = obj_data.dict()
        elif hasattr(obj_data, "model_dump"):
            data = obj_data.model_dump()
        elif isinstance(obj_data, dict):
            data = obj_data.copy()
        else:
            raise ValueError("obj_data must be a dict or Pydantic model")

        # Add tenant information if model supports it
        if hasattr(self.model, 'tenant_type') and hasattr(self.model, 'tenant_id'):
            data.update({"tenant_type": tenant_type, "tenant_id": str(tenant_id)})
        
        # Add any extra fields
        data.update(extra)

        instance = self.model.objects.create(**data)
        return instance

    @transaction.atomic
    def update(
        self,
        obj_id: Union[str, int],
        obj_data: Union[Dict[str, Any], Any],
        tenant_type: str,
        tenant_id: Union[str, int],
        **extra,
    ) -> Optional[ModelT]:
        """Update a record for the tenant."""
        instance = self.get_one(obj_id, tenant_type, tenant_id)
        if not instance:
            return None

        # Handle both dict and Pydantic model inputs
        if hasattr(obj_data, "dict"):
            data = obj_data.dict(exclude_unset=True)
        elif hasattr(obj_data, "model_dump"):
            data = obj_data.model_dump(exclude_unset=True)
        elif isinstance(obj_data, dict):
            data = obj_data.copy()
        else:
            raise ValueError("obj_data must be a dict or Pydantic model")

        # Add any extra fields
        data.update(extra)

        # Update fields
        for field, value in data.items():
            if (hasattr(instance, field) and 
                field not in ["id", "created_at", "tenant_type", "tenant_id"]):
                setattr(instance, field, value)

        instance.save()
        return instance

    @transaction.atomic
    def delete(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> bool:
        """Delete a record for the tenant."""
        instance = self.get_one(obj_id, tenant_type, tenant_id)
        if not instance:
            return False

        instance.delete()
        return True

    def count(self, tenant_type: str, tenant_id: Union[str, int]) -> int:
        """Count records for the tenant."""
        return self._base_queryset(tenant_type, tenant_id).count()

    def exists(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> bool:
        """Check if a record exists for the tenant."""
        return self._base_queryset(tenant_type, tenant_id).filter(id=obj_id).exists()


# Maintain backward compatibility
TenantService = DjangoTenantService