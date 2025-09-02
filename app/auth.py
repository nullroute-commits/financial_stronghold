"""
Django-native authentication system for Financial Stronghold.
Handles user authentication, token management, and permission checking using Django ORM.

Last updated: 2025-01-21 by AI Assistant
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .django_models import User, UserOrganizationLink, TenantType

bearer_scheme = HTTPBearer(auto_error=False)

# Import from Django settings for consistency
from django.conf import settings

SECRET_KEY = getattr(settings, 'SECRET_KEY', 'django-insecure-fallback-key')
ALGORITHM = "HS256"


class DjangoAuthentication:
    """Django-native authentication service for handling user authentication."""

    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password using Django auth."""
        try:
            user = User.objects.get(email=username, is_active=True)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        return None

    def verify_password(self, plain_password: str, user: User) -> bool:
        """Verify a password using Django's built-in authentication."""
        return user.check_password(plain_password)

    def hash_password(self, password: str) -> str:
        """Hash a password using Django's built-in password hashing."""
        from django.contrib.auth.hashers import make_password
        return make_password(password)


class TokenManager:
    """JWT token management service."""

    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def create_token(
        self, user_id: str, tenant_type: str, tenant_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT token for a user."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        payload = {
            "sub": user_id,
            "tenant_type": tenant_type,
            "tenant_id": tenant_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        """Decode a JWT token and return the payload."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    def refresh_token(self, token: str) -> str:
        """Refresh a JWT token."""
        payload = self.decode_token(token)
        new_payload = {
            "sub": payload.get("sub"),
            "tenant_type": payload.get("tenant_type"),
            "tenant_id": payload.get("tenant_id"),
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(new_payload, self.secret_key, algorithm=self.algorithm)


class PermissionChecker:
    """Permission checking service using Django ORM."""

    def has_permission(self, user: User, permission: str, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has a specific permission."""
        if tenant_type == TenantType.ORGANIZATION:
            try:
                link = UserOrganizationLink.objects.get(user=user, organization_id=tenant_id)
                return self._role_has_permission(link.role, permission)
            except UserOrganizationLink.DoesNotExist:
                return False
        return True  # User tenant has all permissions on their own data

    def has_any_permission(self, user: User, permissions: list, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has any of the specified permissions."""
        return any(self.has_permission(user, perm, tenant_type, tenant_id) for perm in permissions)

    def has_all_permissions(self, user: User, permissions: list, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has all of the specified permissions."""
        return all(self.has_permission(user, perm, tenant_type, tenant_id) for perm in permissions)

    def check_tenant_access(self, user: User, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has access to a specific tenant."""
        if tenant_type == TenantType.USER:
            return str(user.id) == tenant_id
        elif tenant_type == TenantType.ORGANIZATION:
            return UserOrganizationLink.objects.filter(user=user, organization_id=tenant_id).exists()
        return False

    def _role_has_permission(self, role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        role_permissions = {
            "admin": ["read", "write", "delete", "manage"],
            "manager": ["read", "write", "delete"],
            "member": ["read", "write"],
            "viewer": ["read"],
        }
        return permission in role_permissions.get(role, [])

    def check_role(self, user: User, role: str, tenant_id: str = None) -> bool:
        """Check if user has a specific role."""
        # Check organization role if tenant_id provided
        if tenant_id:
            try:
                link = UserOrganizationLink.objects.get(user=user, organization_id=tenant_id)
                return link.role == role
            except UserOrganizationLink.DoesNotExist:
                return False
        return True


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> Tuple[User, str, str]:
    """
    Decode the JWT, fetch the User record, and return a tuple:
        (user_obj, tenant_type, tenant_id)

    The token payload must contain:
        - sub: user UUID
        - tenant_type: "user" | "organization"
        - tenant_id: the string id of the tenant (user_id for personal mode, org_id for org mode)
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        tenant_type: str = payload.get("tenant_type", TenantType.USER)
        tenant_id: str = str(payload.get("tenant_id", user_id))

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Load the user from Django ORM
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Verify that the tenant belongs to the user (if organization)
    if tenant_type == TenantType.ORGANIZATION:
        if not UserOrganizationLink.objects.filter(user=user, organization_id=tenant_id).exists():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not a member of the requested organization",
            )
    elif tenant_type == TenantType.USER:
        # For user tenant, tenant_id should match user id
        if tenant_id != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid tenant_id for user tenant",
            )

    return user, tenant_type, tenant_id


def require_role(required_roles: list[str]):
    """Dependency factory that checks the caller's role within the org."""

    def checker(auth: Tuple[User, str, str] = Depends(get_current_user)) -> UserOrganizationLink:
        user, tenant_type, tenant_id = auth
        if tenant_type != TenantType.ORGANIZATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role checks only apply to organization tenants",
            )

        # Fetch the link row using Django ORM
        try:
            link = UserOrganizationLink.objects.get(user=user, organization_id=tenant_id)
            if link.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions (need one of: {required_roles})",
                )
            return link
        except UserOrganizationLink.DoesNotExist:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions (need one of: {required_roles})",
            )

    return checker


def get_tenant_context(auth: Tuple[User, str, str] = Depends(get_current_user)) -> dict:
    """Helper to get tenant context for easy access in route handlers."""
    user, tenant_type, tenant_id = auth
    return {
        "user": user,
        "tenant_type": tenant_type,
        "tenant_id": tenant_id,
        "is_organization": tenant_type == TenantType.ORGANIZATION,
        "is_user": tenant_type == TenantType.USER,
    }