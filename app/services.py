"""Multi-tenancy extension for Financial Stronghold."""

from typing import Generic, TypeVar, List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.tenant import TenantMixin, TenantType
from app.core.db.connection import get_db_session

ModelT = TypeVar("ModelT", bound=TenantMixin)


class TenantService(Generic[ModelT]):
    """Generic service that automatically filters by tenant."""

    def __init__(self, db: Session, model: type[ModelT]):
        self.db = db
        self.model = model

    def _base_query(self, tenant_type: str, tenant_id: Union[str, int]):
        """Create base query filtered by tenant."""
        return self.db.query(self.model).filter(
            and_(
                self.model.tenant_type == tenant_type,
                self.model.tenant_id == str(tenant_id),
            )
        )

    def get_all(
        self, tenant_type: str, tenant_id: Union[str, int], limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[ModelT]:
        """Get all records for the tenant."""
        query = self._base_query(tenant_type, tenant_id)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_one(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> Optional[ModelT]:
        """Get one record by ID for the tenant."""
        return self._base_query(tenant_type, tenant_id).filter(self.model.id == obj_id).first()

    def create(
        self, obj_data: Union[Dict[str, Any], Any], tenant_type: str, tenant_id: Union[str, int], **extra
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

        # Add tenant information
        data.update({"tenant_type": tenant_type, "tenant_id": str(tenant_id), **extra})

        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

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
            if hasattr(instance, field) and field not in ["id", "created_at", "tenant_type", "tenant_id"]:
                setattr(instance, field, value)

        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> bool:
        """Delete a record for the tenant."""
        instance = self.get_one(obj_id, tenant_type, tenant_id)
        if not instance:
            return False

        self.db.delete(instance)
        self.db.commit()
        return True

    def count(self, tenant_type: str, tenant_id: Union[str, int]) -> int:
        """Count records for the tenant."""
        return self._base_query(tenant_type, tenant_id).count()

    def exists(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> bool:
        """Check if a record exists for the tenant."""
        return self.get_one(obj_id, tenant_type, tenant_id) is not None
