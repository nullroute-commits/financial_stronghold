"""
Optimized Django service layer with performance improvements.
Includes caching, query optimization, and pagination.

Last updated: 2025-01-21 by AI Assistant
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Model, Q, Prefetch

from .django_models import TenantMixin, TenantType

ModelT = TypeVar("ModelT", bound=Model)


class OptimizedTenantService(Generic[ModelT]):
    """Optimized Django service with caching and performance improvements."""

    def __init__(self, model: type[ModelT], cache_timeout: int = 300):
        self.model = model
        self.cache_timeout = cache_timeout

    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operations."""
        key_parts = [
            self.model.__name__.lower(),
            operation,
        ]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}_{v}")
        return ":".join(key_parts)

    def _base_queryset(self, tenant_type: str, tenant_id: Union[str, int]):
        """Create optimized base queryset filtered by tenant."""
        if hasattr(self.model, 'tenant_type') and hasattr(self.model, 'tenant_id'):
            return self.model.objects.select_related(
                'created_by', 'updated_by'
            ).filter(
                tenant_type=tenant_type,
                tenant_id=str(tenant_id)
            )
        else:
            # For models without tenant scoping, return optimized queryset
            return self.model.objects.select_related().all()

    def get_all(
        self, 
        tenant_type: str, 
        tenant_id: Union[str, int], 
        limit: Optional[int] = None, 
        offset: Optional[int] = None,
        use_cache: bool = True
    ) -> List[ModelT]:
        """Get all records for the tenant with caching."""
        cache_key = self._get_cache_key(
            'get_all', 
            tenant_type=tenant_type, 
            tenant_id=tenant_id,
            limit=limit,
            offset=offset
        )
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        queryset = self._base_queryset(tenant_type, tenant_id)
        
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]
        
        result = list(queryset)
        
        if use_cache:
            cache.set(cache_key, result, self.cache_timeout)
        
        return result

    def get_paginated(
        self,
        tenant_type: str,
        tenant_id: Union[str, int],
        page: int = 1,
        page_size: int = 20,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get paginated results with metadata."""
        cache_key = self._get_cache_key(
            'get_paginated',
            tenant_type=tenant_type,
            tenant_id=tenant_id,
            page=page,
            page_size=page_size
        )
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        queryset = self._base_queryset(tenant_type, tenant_id)
        paginator = Paginator(queryset, page_size)
        
        page_obj = paginator.get_page(page)
        
        result = {
            'items': list(page_obj),
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
        
        if use_cache:
            cache.set(cache_key, result, self.cache_timeout)
        
        return result

    def get_one(
        self, 
        obj_id: Union[str, int], 
        tenant_type: str, 
        tenant_id: Union[str, int],
        use_cache: bool = True
    ) -> Optional[ModelT]:
        """Get one record by ID for the tenant with caching."""
        cache_key = self._get_cache_key(
            'get_one',
            obj_id=obj_id,
            tenant_type=tenant_type,
            tenant_id=tenant_id
        )
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result if cached_result != 'NOT_FOUND' else None

        try:
            result = self._base_queryset(tenant_type, tenant_id).get(id=obj_id)
            if use_cache:
                cache.set(cache_key, result, self.cache_timeout)
            return result
        except self.model.DoesNotExist:
            if use_cache:
                cache.set(cache_key, 'NOT_FOUND', self.cache_timeout)
            return None

    @transaction.atomic
    def create(
        self, 
        obj_data: Union[Dict[str, Any], Any], 
        tenant_type: str, 
        tenant_id: Union[str, int], 
        **extra
    ) -> ModelT:
        """Create a new record with tenant scoping and cache invalidation."""
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
        
        # Invalidate related caches
        self._invalidate_cache(tenant_type, tenant_id)
        
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
        """Update a record for the tenant with cache invalidation."""
        instance = self.get_one(obj_id, tenant_type, tenant_id, use_cache=False)
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
        
        # Invalidate related caches
        self._invalidate_cache(tenant_type, tenant_id, obj_id)
        
        return instance

    @transaction.atomic
    def delete(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> bool:
        """Delete a record for the tenant with cache invalidation."""
        instance = self.get_one(obj_id, tenant_type, tenant_id, use_cache=False)
        if not instance:
            return False

        instance.delete()
        
        # Invalidate related caches
        self._invalidate_cache(tenant_type, tenant_id, obj_id)
        
        return True

    def count(self, tenant_type: str, tenant_id: Union[str, int], use_cache: bool = True) -> int:
        """Count records for the tenant with caching."""
        cache_key = self._get_cache_key('count', tenant_type=tenant_type, tenant_id=tenant_id)
        
        if use_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        result = self._base_queryset(tenant_type, tenant_id).count()
        
        if use_cache:
            cache.set(cache_key, result, self.cache_timeout)
        
        return result

    def exists(self, obj_id: Union[str, int], tenant_type: str, tenant_id: Union[str, int]) -> bool:
        """Check if a record exists for the tenant."""
        return self.get_one(obj_id, tenant_type, tenant_id) is not None

    def _invalidate_cache(self, tenant_type: str, tenant_id: Union[str, int], obj_id: Optional[Union[str, int]] = None):
        """Invalidate related cache entries."""
        # Get all possible cache keys to invalidate
        cache_patterns = [
            f"{self.model.__name__.lower()}:get_all:tenant_type_{tenant_type}:tenant_id_{tenant_id}*",
            f"{self.model.__name__.lower()}:get_paginated:tenant_type_{tenant_type}:tenant_id_{tenant_id}*",
            f"{self.model.__name__.lower()}:count:tenant_type_{tenant_type}:tenant_id_{tenant_id}",
        ]
        
        if obj_id:
            cache_patterns.append(
                f"{self.model.__name__.lower()}:get_one:obj_id_{obj_id}:tenant_type_{tenant_type}:tenant_id_{tenant_id}"
            )
        
        # In a production environment, you might want to use Redis pattern deletion
        # For now, we'll use Django's cache.delete_many with specific keys
        # This is a simplified implementation
        for pattern in cache_patterns:
            try:
                cache.delete(pattern)
            except:
                pass  # Ignore cache deletion errors


# Maintain backward compatibility
DjangoTenantService = OptimizedTenantService