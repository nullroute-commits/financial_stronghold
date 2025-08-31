"""
Django-native audit logging system.
Tracks all system activities for security and compliance using Django models.

Last updated: 2025-08-31 by AI Assistant
"""

import json
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.contrib.sessions.models import Session
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin

from .django_models import AuditLog, User

logger = logging.getLogger(__name__)


class DjangoAuditLogger:
    """
    Django-native audit logger for tracking system activities.

    Features:
    - Automatic activity tracking
    - Model change detection
    - Request/response logging
    - User activity monitoring
    - Configurable audit levels
    - Django integration
    """

    def __init__(self):
        """Initialize audit logger."""
        self.enabled = getattr(settings, "AUDIT_ENABLED", True)
        self.log_models = getattr(settings, "AUDIT_LOG_MODELS", True)
        self.log_requests = getattr(settings, "AUDIT_LOG_REQUESTS", True)
        self.log_authentication = getattr(settings, "AUDIT_LOG_AUTHENTICATION", True)

    def log_activity(
        self,
        action: str,
        user: Optional[User] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_repr: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_data: Optional[Dict] = None,
        response_status: Optional[int] = None,
        metadata: Optional[Dict] = None,
        message: Optional[str] = None,
    ) -> Optional[str]:
        """
        Log an activity to the audit trail.

        Args:
            action: Action performed (CREATE, UPDATE, DELETE, LOGIN, etc.)
            user: User performing the action
            session_id: Session ID
            ip_address: Client IP address
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of affected resource
            resource_repr: String representation of resource
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            request_method: HTTP method
            request_path: Request URL path
            request_data: Request data (sanitized)
            response_status: HTTP response status
            metadata: Additional metadata
            message: Human-readable message

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled:
            return None

        try:
            # Sanitize sensitive data
            sanitized_request_data = self._sanitize_data(request_data) if request_data else None
            sanitized_old_values = self._sanitize_data(old_values) if old_values else None
            sanitized_new_values = self._sanitize_data(new_values) if new_values else None

            audit_log = AuditLog.objects.create(
                user=user,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_repr=resource_repr,
                old_values=sanitized_old_values,
                new_values=sanitized_new_values,
                request_method=request_method,
                request_path=request_path,
                request_data=sanitized_request_data,
                response_status=response_status,
                extra_metadata=metadata,
                message=message,
            )

            logger.debug(f"Logged audit activity: {action} by user {user}")
            return str(audit_log.id)

        except Exception as e:
            logger.error(f"Failed to log audit activity: {str(e)}")
            return None

    def log_model_change(
        self,
        action: str,
        model_instance: Any,
        user: Optional[User] = None,
        old_values: Optional[Dict] = None,
        request: Optional[HttpRequest] = None,
    ) -> Optional[str]:
        """
        Log model changes (create, update, delete).

        Args:
            action: Action performed (CREATE, UPDATE, DELETE)
            model_instance: Model instance
            user: User performing the action
            old_values: Previous values (for updates)
            request: Django HttpRequest object

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled or not self.log_models:
            return None

        try:
            resource_type = model_instance.__class__.__name__
            resource_id = str(getattr(model_instance, "id", None))
            resource_repr = str(model_instance)

            # Get new values from model
            new_values = {}
            if hasattr(model_instance, "__dict__"):
                for key, value in model_instance.__dict__.items():
                    if not key.startswith("_"):
                        try:
                            # Convert to JSON-serializable format
                            json.dumps(value)
                            new_values[key] = value
                        except (TypeError, ValueError):
                            new_values[key] = str(value)

            # Extract session info from request
            session_id = None
            ip_address = None
            user_agent = None

            if request:
                session_id = request.session.session_key
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get("HTTP_USER_AGENT")

            return self.log_activity(
                action=action,
                user=user,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_repr=resource_repr,
                old_values=old_values,
                new_values=new_values,
            )

        except Exception as e:
            logger.error(f"Failed to log model change: {str(e)}")
            return None

    def log_authentication(
        self,
        action: str,
        user: Optional[User] = None,
        username: Optional[str] = None,
        success: bool = True,
        request: Optional[HttpRequest] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Log authentication events.

        Args:
            action: Authentication action (LOGIN, LOGOUT, LOGIN_FAILED, etc.)
            user: User instance
            username: Username attempted
            success: Whether authentication was successful
            request: Django HttpRequest object
            metadata: Additional metadata

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled or not self.log_authentication:
            return None

        auth_metadata = metadata or {}
        auth_metadata.update({"success": success, "username": username})

        message = f"Authentication {action.lower()}"
        if username:
            message += f" for user {username}"
        if not success:
            message += " (failed)"

        # Extract session info from request
        session_id = None
        ip_address = None
        user_agent = None

        if request:
            session_id = request.session.session_key
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT")

        return self.log_activity(
            action=action,
            user=user,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="Authentication",
            metadata=auth_metadata,
            message=message,
        )

    def log_request(
        self, request: HttpRequest, response_status: Optional[int] = None, user: Optional[User] = None
    ) -> Optional[str]:
        """
        Log HTTP requests.

        Args:
            request: Django HttpRequest object
            response_status: HTTP response status
            user: Authenticated user

        Returns:
            Audit log UUID if successful, None otherwise
        """
        if not self.enabled or not self.log_requests:
            return None

        # Extract request data
        request_data = {}
        if hasattr(request, "POST") and request.POST:
            request_data.update(dict(request.POST))
        if hasattr(request, "GET") and request.GET:
            request_data.update(dict(request.GET))

        return self.log_activity(
            action="HTTP_REQUEST",
            user=user,
            session_id=request.session.session_key,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT"),
            request_method=request.method,
            request_path=request.path,
            request_data=request_data,
            response_status=response_status,
        )

    def get_user_activity(
        self, user: User, limit: int = 100, offset: int = 0, action_filter: Optional[str] = None
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.

        Args:
            user: User instance
            limit: Maximum number of records
            offset: Number of records to skip
            action_filter: Filter by action type

        Returns:
            QuerySet of audit logs
        """
        try:
            queryset = AuditLog.objects.filter(user=user)

            if action_filter:
                queryset = queryset.filter(action=action_filter)

            queryset = queryset.order_by("-created_at")
            return queryset[offset : offset + limit]

        except Exception as e:
            logger.error(f"Failed to get user activity: {str(e)}")
            return AuditLog.objects.none()

    def get_resource_history(self, resource_type: str, resource_id: str, limit: int = 100) -> List[AuditLog]:
        """
        Get audit history for a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            limit: Maximum number of records

        Returns:
            QuerySet of audit logs
        """
        try:
            queryset = AuditLog.objects.filter(resource_type=resource_type, resource_id=resource_id).order_by(
                "-created_at"
            )[:limit]

            return queryset

        except Exception as e:
            logger.error(f"Failed to get resource history: {str(e)}")
            return AuditLog.objects.none()

    def _get_client_ip(self, request: HttpRequest) -> Optional[str]:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def _sanitize_data(self, data: Dict) -> Dict:
        """
        Sanitize sensitive data from logs.

        Args:
            data: Data dictionary

        Returns:
            Sanitized data dictionary
        """
        if not isinstance(data, dict):
            return data

        sensitive_fields = {
            "password",
            "password_hash",
            "token",
            "secret",
            "key",
            "authorization",
            "cookie",
            "session",
            "csrf_token",
            "csrfmiddlewaretoken",
            "api_key",
            "access_token",
        }

        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_data(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized


# Global audit logger instance
audit_logger = DjangoAuditLogger()


class AuditMiddleware(MiddlewareMixin):
    """
    Django middleware for automatic request/response auditing.
    """

    def process_request(self, request):
        """Process incoming request."""
        # Store request start time for performance tracking
        request._audit_start_time = datetime.now(timezone.utc)
        return None

    def process_response(self, request, response):
        """Process outgoing response."""
        try:
            user = request.user if hasattr(request, "user") and request.user.is_authenticated else None

            # Skip auditing for certain paths
            skip_paths = ["/admin/jsi18n/", "/static/", "/media/", "/favicon.ico"]
            if any(request.path.startswith(path) for path in skip_paths):
                return response

            # Log the request
            audit_logger.log_request(request=request, response_status=response.status_code, user=user)

        except Exception as e:
            logger.error(f"Failed to audit request in middleware: {str(e)}")

        return response


# Decorator functions for automatic auditing
def audit_activity(action: str, resource_type: Optional[str] = None):
    """
    Decorator to automatically audit function calls.

    Args:
        action: Action being performed
        resource_type: Type of resource being affected

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract user and request from args/kwargs
            user = None
            request = None

            # Look for Django request object
            for arg in args:
                if isinstance(arg, HttpRequest):
                    request = arg
                    user = arg.user if hasattr(arg, "user") and arg.user.is_authenticated else None
                    break

            # Look for user in kwargs
            if not user:
                user = kwargs.get("user")

            try:
                result = func(*args, **kwargs)

                # Log successful activity
                audit_logger.log_activity(
                    action=action,
                    user=user,
                    session_id=request.session.session_key if request else None,
                    ip_address=audit_logger._get_client_ip(request) if request else None,
                    user_agent=request.META.get("HTTP_USER_AGENT") if request else None,
                    resource_type=resource_type,
                    metadata={
                        "function": f"{func.__module__}.{func.__name__}",
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                )

                return result

            except Exception as e:
                # Log failed activity
                audit_logger.log_activity(
                    action=f"{action}_FAILED",
                    user=user,
                    session_id=request.session.session_key if request else None,
                    ip_address=audit_logger._get_client_ip(request) if request else None,
                    user_agent=request.META.get("HTTP_USER_AGENT") if request else None,
                    resource_type=resource_type,
                    metadata={
                        "function": f"{func.__module__}.{func.__name__}",
                        "error": str(e),
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                    message=f"Failed to {action.lower()}: {str(e)}",
                )
                raise

        return wrapper

    return decorator


# Helper functions
def get_audit_logger() -> DjangoAuditLogger:
    """
    Get the global audit logger instance.

    Returns:
        DjangoAuditLogger instance
    """
    return audit_logger


def log_user_activity(action: str, user: User, **kwargs) -> Optional[str]:
    """
    Convenience function to log user activity.

    Args:
        action: Action performed
        user: User instance
        **kwargs: Additional audit parameters

    Returns:
        Audit log UUID if successful, None otherwise
    """
    return audit_logger.log_activity(action=action, user=user, **kwargs)


def log_model_change(
    action: str,
    instance,
    user: Optional[User] = None,
    old_values: Optional[Dict] = None,
    request: Optional[HttpRequest] = None,
):
    """
    Log model changes for audit trail.

    Args:
        action: Action performed (CREATE, UPDATE, DELETE)
        instance: Model instance
        user: User performing the action
        old_values: Previous values (for updates)
        request: Django HttpRequest object
    """
    return audit_logger.log_model_change(action, instance, user, old_values, request)
