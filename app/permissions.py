"""
Django REST Framework custom permissions for RBAC and tenant isolation.
Replaces FastAPI dependency injection with DRF permission classes.

Last updated: 2025-01-02 by Team Beta (Architecture & Backend Agents)
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model
from .django_models import UserOrganizationLink, Role, Permission

User = get_user_model()


class TenantPermission(permissions.BasePermission):
    """
    Permission class to ensure users can only access their tenant data.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have access to everything
        if request.user.is_superuser:
            return True
        
        # Set tenant context if not already set by middleware
        if not hasattr(request, 'tenant_type'):
            request.tenant_type = 'user'
            request.tenant_id = str(request.user.id)
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have access to everything
        if request.user.is_superuser:
            return True
        
        # Check if object belongs to user's tenant
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # Check if object belongs to user's organization
        if hasattr(request, 'tenant_type') and request.tenant_type == 'organization':
            if hasattr(obj, 'tenant_id') and obj.tenant_id == request.tenant_id:
                return True
        
        return False


class RBACPermission(permissions.BasePermission):
    """
    Permission class for Role-Based Access Control.
    Checks user roles and permissions for specific actions.
    """
    
    def has_permission(self, request, view):
        """Check if user has role-based permission for the view."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have access to everything
        if request.user.is_superuser:
            return True
        
        # Get required permission for this view/action
        required_permission = self._get_required_permission(request, view)
        if not required_permission:
            return True  # No specific permission required
        
        # Check if user has the required permission
        return self._user_has_permission(request.user, required_permission)
    
    def _get_required_permission(self, request, view):
        """
        Get the required permission for the current request.
        
        Returns:
            tuple: (resource, action) or None if no permission required
        """
        # Map HTTP methods to actions
        method_action_map = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        
        action = method_action_map.get(request.method, 'read')
        
        # Get resource from view
        if hasattr(view, 'queryset') and view.queryset is not None:
            resource = view.queryset.model._meta.model_name
        elif hasattr(view, 'get_queryset'):
            try:
                queryset = view.get_queryset()
                resource = queryset.model._meta.model_name
            except:
                resource = 'unknown'
        else:
            resource = 'unknown'
        
        return (resource, action)
    
    def _user_has_permission(self, user, required_permission):
        """
        Check if user has the required permission through their roles.
        
        Args:
            user: User instance
            required_permission: tuple of (resource, action)
            
        Returns:
            bool: True if user has permission
        """
        resource, action = required_permission
        
        try:
            # Get user roles
            user_roles = Role.objects.filter(users=user)
            
            # Check if any role has the required permission
            for role in user_roles:
                role_permissions = Permission.objects.filter(roles=role)
                
                for permission in role_permissions:
                    if (permission.resource == resource or permission.resource == '*') and \
                       (permission.action == action or permission.action == '*'):
                        return True
            
            return False
            
        except Exception:
            # If RBAC system fails, deny access
            return False


class OrganizationPermission(permissions.BasePermission):
    """
    Permission class for organization-specific access control.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access organization resources."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have access to everything
        if request.user.is_superuser:
            return True
        
        # Check if accessing organization context
        if hasattr(request, 'tenant_type') and request.tenant_type == 'organization':
            tenant_id = getattr(request, 'tenant_id', None)
            if tenant_id:
                # Verify user is member of the organization
                return UserOrganizationLink.objects.filter(
                    user=request.user,
                    organization_id=tenant_id
                ).exists()
        
        return True  # Allow for non-organization requests
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific organization object."""
        if not request.user.is_authenticated:
            return False
        
        # Superusers have access to everything
        if request.user.is_superuser:
            return True
        
        # Check if object belongs to user's organization
        if hasattr(obj, 'organization'):
            return UserOrganizationLink.objects.filter(
                user=request.user,
                organization=obj.organization
            ).exists()
        
        return True