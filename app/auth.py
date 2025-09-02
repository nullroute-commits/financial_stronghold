"""Multi-tenancy extension for Financial Stronghold."""

from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.db.connection import get_db_session
from app.core.models import User
from app.core.tenant import Organization, TenantType, UserOrganizationLink

bearer_scheme = HTTPBearer(auto_error=False)

# This would normally come from environment variables
SECRET_KEY = "your-secret-key-here"  # In production, use proper secret management
ALGORITHM = "HS256"


class Authentication:
    """Authentication service for handling user authentication."""

    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def authenticate_user(self, username: str, password: str, db: Session) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = db.query(User).filter(User.username == username).first()
        if user and user.is_active and self.verify_password(password, user.password_hash):
            return user
        return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        # In a real implementation, this would use bcrypt or similar
        # For our simplified implementation, check if hashed password matches expected format
        expected_hash = f"hashed_{plain_password}"
        return hashed_password == expected_hash

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        # In a real implementation, this would use bcrypt or similar
        return f"hashed_{password}"  # Simplified for testing


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


class PermissionChecker:
    """Permission checking service."""

    def __init__(self, db: Session):
        self.db = db

    def has_permission(self, user: User, permission: str, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has a specific permission."""
        if tenant_type == TenantType.ORGANIZATION.value:
            link = self.db.query(UserOrganizationLink).filter_by(user_id=user.id, org_id=int(tenant_id)).first()
            if not link:
                return False
            # Check if the role has the required permission
            return self._role_has_permission(link.role, permission)
        return True  # User tenant has all permissions on their own data

    def has_any_permission(self, user: User, permissions: list, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has any of the specified permissions."""
        return any(self.has_permission(user, perm, tenant_type, tenant_id) for perm in permissions)

    def has_all_permissions(self, user: User, permissions: list, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has all of the specified permissions."""
        return all(self.has_permission(user, perm, tenant_type, tenant_id) for perm in permissions)

    def check_tenant_access(self, user: User, tenant_type: str, tenant_id: str) -> bool:
        """Check if a user has access to a specific tenant."""
        if tenant_type == TenantType.USER.value:
            return str(user.id) == tenant_id
        elif tenant_type == TenantType.ORGANIZATION.value:
            link = self.db.query(UserOrganizationLink).filter_by(user_id=user.id, org_id=int(tenant_id)).first()
            return link is not None
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


# Initialize global services
token_manager = TokenManager()
permission_checker = None  # Will be initialized when needed


# Dependencies for FastAPI
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme), db: Session = Depends(get_db_session)
) -> User:
    """Get the current authenticated user."""
    auth = Authentication()
    user, _, _ = auth.authenticate_user(credentials, db)
    return user


def get_tenant_context(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme), db: Session = Depends(get_db_session)
) -> dict:
    """Get tenant context from the current request."""
    auth = Authentication()
    user, tenant_type, tenant_id = auth.authenticate_user(credentials, db)

    global permission_checker
    if permission_checker is None:
        permission_checker = PermissionChecker(db)

    if not permission_checker.check_tenant_access(user, tenant_type, tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to tenant")

    return {
        "user": user,
        "tenant_type": tenant_type,
        "tenant_id": tenant_id,
    }
