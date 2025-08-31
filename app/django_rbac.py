"""
Django-native RBAC system.
Provides comprehensive access control functionality using Django's built-in systems.

Last updated: 2025-08-31 by AI Assistant
"""
import logging
from typing import List, Optional, Set
from functools import wraps
from django.core.cache import cache
from django.contrib.auth.models import Group, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied

from .django_models import User, Role, Permission, AuditLog

logger = logging.getLogger(__name__)


class DjangoRBACManager:
    """
    RBAC Manager for handling role and permission operations using Django.
    
    Features:
    - User role assignment
    - Permission checking
    - Role hierarchy
    - Caching for performance
    - Audit logging integration
    - Django-native integration
    """
    
    def __init__(self, cache_timeout: int = 300):
        """
        Initialize RBAC Manager.
        
        Args:
            cache_timeout: Cache timeout in seconds
        """
        self.cache_timeout = cache_timeout
    
    def get_user_permissions(self, user: User, use_cache: bool = True) -> Set[str]:
        """
        Get all permissions for a user.
        
        Args:
            user: User instance
            use_cache: Whether to use cache
        
        Returns:
            Set of permission names
        """
        cache_key = f"user_permissions:{user.id}"
        
        if use_cache:
            cached_permissions = cache.get(cache_key)
            if cached_permissions is not None:
                return set(cached_permissions)
        
        permissions = set()
        
        # Superuser has all permissions
        if user.is_superuser:
            all_permissions = Permission.objects.filter(is_active=True).values_list('name', flat=True)
            permissions = set(all_permissions)
        else:
            # Get permissions from active roles
            for role in user.custom_roles.filter(is_active=True):
                role_permissions = role.permissions.filter(is_active=True).values_list('name', flat=True)
                permissions.update(role_permissions)
            
            # Also get Django permissions
            django_permissions = user.get_all_permissions()
            permissions.update(django_permissions)
        
        # Cache the result
        if use_cache:
            cache.set(cache_key, list(permissions), self.cache_timeout)
        
        return permissions
    
    def get_user_roles(self, user: User, use_cache: bool = True) -> Set[str]:
        """
        Get all roles for a user.
        
        Args:
            user: User instance
            use_cache: Whether to use cache
        
        Returns:
            Set of role names
        """
        cache_key = f"user_roles:{user.id}"
        
        if use_cache:
            cached_roles = cache.get(cache_key)
            if cached_roles is not None:
                return set(cached_roles)
        
        # Get custom roles
        custom_roles = user.custom_roles.filter(is_active=True).values_list('name', flat=True)
        
        # Get Django groups (treated as roles)
        django_groups = user.groups.values_list('name', flat=True)
        
        roles = set(custom_roles) | set(django_groups)
        
        # Cache the result
        if use_cache:
            cache.set(cache_key, list(roles), self.cache_timeout)
        
        return roles
    
    def has_permission(self, user: User, permission_name: str, use_cache: bool = True) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user: User instance
            permission_name: Permission name to check
            use_cache: Whether to use cache
        
        Returns:
            True if user has permission, False otherwise
        """
        permissions = self.get_user_permissions(user, use_cache)
        return permission_name in permissions
    
    def has_role(self, user: User, role_name: str, use_cache: bool = True) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user: User instance
            role_name: Role name to check
            use_cache: Whether to use cache
        
        Returns:
            True if user has role, False otherwise
        """
        roles = self.get_user_roles(user, use_cache)
        return role_name in roles
    
    def assign_role(self, user: User, role_name: str, assigned_by: Optional[User] = None) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user: User instance
            role_name: Role name to assign
            assigned_by: User performing the assignment
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try custom role first
            try:
                role = Role.objects.get(name=role_name, is_active=True)
                if role not in user.custom_roles.all():
                    user.custom_roles.add(role)
                    user.updated_by = assigned_by
                    user.save()
                    
                    # Log the action
                    self._log_role_action('ASSIGN_ROLE', user, role_name, assigned_by)
                    
                    # Clear cache
                    self._clear_user_cache(user)
                    
                    logger.info(f"Assigned custom role {role_name} to user {user.email}")
                    return True
                else:
                    logger.info(f"User {user.email} already has custom role {role_name}")
                    return True
                    
            except Role.DoesNotExist:
                # Try Django group
                try:
                    group = Group.objects.get(name=role_name)
                    if group not in user.groups.all():
                        user.groups.add(group)
                        
                        # Log the action
                        self._log_role_action('ASSIGN_GROUP', user, role_name, assigned_by)
                        
                        # Clear cache
                        self._clear_user_cache(user)
                        
                        logger.info(f"Assigned group {role_name} to user {user.email}")
                        return True
                    else:
                        logger.info(f"User {user.email} already has group {role_name}")
                        return True
                        
                except Group.DoesNotExist:
                    logger.warning(f"Role/Group {role_name} not found")
                    return False
                
        except Exception as e:
            logger.error(f"Failed to assign role {role_name} to user {user.email}: {str(e)}")
            return False
    
    def revoke_role(self, user: User, role_name: str, revoked_by: Optional[User] = None) -> bool:
        """
        Revoke a role from a user.
        
        Args:
            user: User instance
            role_name: Role name to revoke
            revoked_by: User performing the revocation
        
        Returns:
            True if successful, False otherwise
        """
        try:
            success = False
            
            # Try custom role first
            try:
                role = Role.objects.get(name=role_name)
                if role in user.custom_roles.all():
                    user.custom_roles.remove(role)
                    user.updated_by = revoked_by
                    user.save()
                    success = True
                    
                    # Log the action
                    self._log_role_action('REVOKE_ROLE', user, role_name, revoked_by)
                    
            except Role.DoesNotExist:
                pass
            
            # Try Django group
            try:
                group = Group.objects.get(name=role_name)
                if group in user.groups.all():
                    user.groups.remove(group)
                    success = True
                    
                    # Log the action
                    self._log_role_action('REVOKE_GROUP', user, role_name, revoked_by)
                    
            except Group.DoesNotExist:
                pass
            
            if success:
                # Clear cache
                self._clear_user_cache(user)
                logger.info(f"Revoked role {role_name} from user {user.email}")
                return True
            else:
                logger.info(f"User {user.email} does not have role {role_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to revoke role {role_name} from user {user.email}: {str(e)}")
            return False
    
    def create_role(self, name: str, description: str = None, permissions: List[str] = None, 
                   created_by: Optional[User] = None) -> Optional[str]:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            permissions: List of permission names to assign
            created_by: User creating the role
        
        Returns:
            Role UUID if successful, None otherwise
        """
        try:
            # Check if role already exists
            if Role.objects.filter(name=name).exists():
                logger.warning(f"Role {name} already exists")
                return None
            
            # Create the role
            role = Role.objects.create(
                name=name,
                description=description,
                created_by=created_by
            )
            
            # Assign permissions if provided
            if permissions:
                permission_objects = Permission.objects.filter(
                    name__in=permissions,
                    is_active=True
                )
                role.permissions.set(permission_objects)
            
            # Log the action
            self._log_role_action('CREATE_ROLE', None, name, created_by, {'role_id': str(role.id)})
            
            logger.info(f"Created role {name}")
            return str(role.id)
            
        except Exception as e:
            logger.error(f"Failed to create role {name}: {str(e)}")
            return None
    
    def create_permission(self, name: str, resource: str, action: str, 
                         description: str = None, created_by: Optional[User] = None) -> Optional[str]:
        """
        Create a new permission.
        
        Args:
            name: Permission name
            resource: Resource type
            action: Action type
            description: Permission description
            created_by: User creating the permission
        
        Returns:
            Permission UUID if successful, None otherwise
        """
        try:
            # Check if permission already exists
            if Permission.objects.filter(name=name).exists():
                logger.warning(f"Permission {name} already exists")
                return None
            
            # Create the permission
            permission = Permission.objects.create(
                name=name,
                resource=resource,
                action=action,
                description=description,
                created_by=created_by
            )
            
            # Log the action
            self._log_role_action('CREATE_PERMISSION', None, name, created_by, {'permission_id': str(permission.id)})
            
            logger.info(f"Created permission {name}")
            return str(permission.id)
            
        except Exception as e:
            logger.error(f"Failed to create permission {name}: {str(e)}")
            return None
    
    def _clear_user_cache(self, user: User):
        """Clear cached data for a user."""
        cache_keys = [
            f"user_permissions:{user.id}",
            f"user_roles:{user.id}"
        ]
        
        cache.delete_many(cache_keys)
    
    def _log_role_action(self, action: str, user: Optional[User], role_name: str, 
                        performed_by: Optional[User], metadata: Optional[dict] = None):
        """Log RBAC actions for audit trail."""
        try:
            AuditLog.objects.create(
                user=performed_by,
                action=action,
                resource_type='RBAC',
                resource_id=str(user.id) if user else None,
                resource_repr=f"Role: {role_name}" + (f" for User: {user.email}" if user else ""),
                extra_metadata=metadata or {},
                message=f"{action} - Role: {role_name}" + (f" for User: {user.email}" if user else "")
            )
        except Exception as e:
            logger.error(f"Failed to log RBAC action: {str(e)}")


# Global RBAC manager instance
rbac_manager = DjangoRBACManager()


# Django decorator functions for permission checking
def require_permission(permission_name: str):
    """
    Decorator to require a specific permission.
    
    Args:
        permission_name: Required permission name
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not isinstance(request, HttpRequest):
                raise ValueError("require_permission decorator can only be used with Django views")
            
            if not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated")
            
            if not rbac_manager.has_permission(request.user, permission_name):
                raise PermissionDenied(f"User does not have permission: {permission_name}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name: str):
    """
    Decorator to require a specific role.
    
    Args:
        role_name: Required role name
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not isinstance(request, HttpRequest):
                raise ValueError("require_role decorator can only be used with Django views")
            
            if not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated")
            
            if not rbac_manager.has_role(request.user, role_name):
                raise PermissionDenied(f"User does not have role: {role_name}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_names: str):
    """
    Decorator to require any of the specified permissions.
    
    Args:
        permission_names: List of permission names (user needs at least one)
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not isinstance(request, HttpRequest):
                raise ValueError("require_any_permission decorator can only be used with Django views")
            
            if not request.user.is_authenticated:
                raise PermissionDenied("User not authenticated")
            
            user_permissions = rbac_manager.get_user_permissions(request.user)
            
            if not any(perm in user_permissions for perm in permission_names):
                raise PermissionDenied(f"User does not have any of the required permissions: {', '.join(permission_names)}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# Helper functions
def get_rbac_manager() -> DjangoRBACManager:
    """
    Get the global RBAC manager instance.
    
    Returns:
        DjangoRBACManager instance
    """
    return rbac_manager


def sync_roles_with_groups():
    """
    Synchronize custom roles with Django groups for compatibility.
    """
    try:
        for role in Role.objects.filter(is_active=True):
            group, created = Group.objects.get_or_create(name=role.name)
            if created:
                logger.info(f"Created Django group for role: {role.name}")
    except Exception as e:
        logger.error(f"Failed to sync roles with groups: {str(e)}")


def initialize_default_roles():
    """
    Initialize default system roles.
    """
    default_roles = [
        {'name': 'admin', 'description': 'System administrator', 'is_system': True},
        {'name': 'manager', 'description': 'Organization manager', 'is_system': True},
        {'name': 'user', 'description': 'Regular user', 'is_system': True},
        {'name': 'viewer', 'description': 'Read-only access', 'is_system': True},
    ]
    
    for role_data in default_roles:
        role, created = Role.objects.get_or_create(
            name=role_data['name'],
            defaults=role_data
        )
        if created:
            logger.info(f"Created default role: {role.name}")


def initialize_default_permissions():
    """
    Initialize default system permissions.
    """
    default_permissions = [
        {'name': 'view_user', 'resource': 'user', 'action': 'view'},
        {'name': 'create_user', 'resource': 'user', 'action': 'create'},
        {'name': 'update_user', 'resource': 'user', 'action': 'update'},
        {'name': 'delete_user', 'resource': 'user', 'action': 'delete'},
        {'name': 'view_account', 'resource': 'account', 'action': 'view'},
        {'name': 'create_account', 'resource': 'account', 'action': 'create'},
        {'name': 'update_account', 'resource': 'account', 'action': 'update'},
        {'name': 'delete_account', 'resource': 'account', 'action': 'delete'},
        {'name': 'view_transaction', 'resource': 'transaction', 'action': 'view'},
        {'name': 'create_transaction', 'resource': 'transaction', 'action': 'create'},
        {'name': 'update_transaction', 'resource': 'transaction', 'action': 'update'},
        {'name': 'delete_transaction', 'resource': 'transaction', 'action': 'delete'},
    ]
    
    for perm_data in default_permissions:
        permission, created = Permission.objects.get_or_create(
            name=perm_data['name'],
            defaults=perm_data
        )
        if created:
            logger.info(f"Created default permission: {permission.name}")