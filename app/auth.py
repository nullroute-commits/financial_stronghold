"""Multi-tenancy extension for Financial Stronghold."""

from datetime import datetime, timedelta
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db_session),
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
        tenant_type: str = payload.get("tenant_type", TenantType.USER.value)
        tenant_id: str = str(payload.get("tenant_id", user_id))

        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    # Load the user from DB
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Verify that the tenant belongs to the user (if organization)
    if tenant_type == TenantType.ORGANIZATION.value:
        link = db.query(UserOrganizationLink).filter_by(user_id=user.id, org_id=int(tenant_id)).first()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not a member of the requested organization",
            )
    elif tenant_type == TenantType.USER.value:
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
        if tenant_type != TenantType.ORGANIZATION.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role checks only apply to organization tenants",
            )

        # Get a new session for this check
        db = next(get_db_session())
        try:
            # Fetch the link row
            link = db.query(UserOrganizationLink).filter_by(user_id=user.id, org_id=int(tenant_id)).first()
            if not link or link.role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions (need one of: {required_roles})",
                )
            return link
        finally:
            db.close()

    return checker


def get_tenant_context(auth: Tuple[User, str, str] = Depends(get_current_user)) -> dict:
    """Helper to get tenant context for easy access in route handlers."""
    user, tenant_type, tenant_id = auth
    return {
        "user": user,
        "tenant_type": tenant_type,
        "tenant_id": tenant_id,
        "is_organization": tenant_type == TenantType.ORGANIZATION.value,
        "is_user": tenant_type == TenantType.USER.value,
    }


class Authentication:
    """Authentication service for handling user authentication and token validation."""
    
    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def validate_token(self, token: str) -> dict:
        """Validate a JWT token and return the payload."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    def authenticate_user(self, credentials: HTTPAuthorizationCredentials, db: Session) -> Tuple[User, str, str]:
        """Authenticate user using credentials."""
        if not credentials:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
        
        token = credentials.credentials
        payload = self.validate_token(token)
        
        user_id: str = payload.get("sub")
        tenant_type: str = payload.get("tenant_type", TenantType.USER.value)
        tenant_id: str = str(payload.get("tenant_id", user_id))
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Load the user from DB
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
        
        return user, tenant_type, tenant_id


class TokenManager:
    """Token management service for JWT operations."""
    
    def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_token(self, user_id: str, tenant_type: str, tenant_id: str, expires_delta: Optional[timedelta] = None) -> str:
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
            "iat": datetime.utcnow()
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
            "iat": datetime.utcnow()
        }
        return jwt.encode(new_payload, self.secret_key, algorithm=self.algorithm)


class PermissionChecker:
    """Permission checking service for authorization."""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session
    
    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission."""
        # This would be implemented based on the RBAC system
        # For now, return True for basic functionality
        return True
    
    def check_role(self, user: User, role: str, tenant_id: str = None) -> bool:
        """Check if user has a specific role."""
        if not self.db:
            return True  # Fallback for testing
        
        # Check organization role if tenant_id provided
        if tenant_id:
            link = self.db.query(UserOrganizationLink).filter_by(
                user_id=user.id, org_id=int(tenant_id)
            ).first()
            return link and link.role == role
        
        return True
    
    def check_tenant_access(self, user: User, tenant_type: str, tenant_id: str) -> bool:
        """Check if user has access to the specified tenant."""
        if tenant_type == TenantType.USER.value:
            return str(user.id) == tenant_id
        
        if tenant_type == TenantType.ORGANIZATION.value and self.db:
            link = self.db.query(UserOrganizationLink).filter_by(
                user_id=user.id, org_id=int(tenant_id)
            ).first()
            return link is not None
        
        return False
