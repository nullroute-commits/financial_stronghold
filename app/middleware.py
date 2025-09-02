"""
Django middleware for tenant scoping and security.
Provides multi-tenant isolation and security headers.

Last updated: 2025-08-31 by AI Assistant
"""

import logging

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from .django_models import TenantType, User, UserOrganizationLink

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware for multi-tenant request scoping.

    Sets tenant context for all requests based on user authentication
    and request headers/parameters.
    """

    def process_request(self, request: HttpRequest):
        """
        Process incoming request to set tenant context.

        Args:
            request: Django HttpRequest object
        """
        try:
            # Initialize tenant context
            request.tenant_type = TenantType.USER
            request.tenant_id = None
            request.tenant_org = None

            # Skip tenant resolution for unauthenticated users
            if not hasattr(request, "user") or isinstance(request.user, AnonymousUser):
                return None

            # Get tenant information from headers or query parameters
            tenant_type = request.META.get("HTTP_X_TENANT_TYPE") or request.GET.get("tenant_type", TenantType.USER)
            tenant_id = request.META.get("HTTP_X_TENANT_ID") or request.GET.get("tenant_id")

            # Validate tenant type
            if tenant_type not in [TenantType.USER, TenantType.ORGANIZATION]:
                tenant_type = TenantType.USER

            # Set tenant context based on type
            if tenant_type == TenantType.ORGANIZATION:
                if tenant_id:
                    # Verify user has access to the organization
                    try:
                        org_link = UserOrganizationLink.objects.get(user=request.user, organization_id=tenant_id)
                        request.tenant_type = TenantType.ORGANIZATION
                        request.tenant_id = str(tenant_id)
                        request.tenant_org = org_link.organization

                    except UserOrganizationLink.DoesNotExist:
                        logger.warning(
                            f"User {request.user.email} attempted to access organization {tenant_id} without permission"
                        )
                        raise PermissionDenied("Access denied to organization")
                else:
                    # No organization specified, default to user tenant
                    request.tenant_type = TenantType.USER
                    request.tenant_id = str(request.user.id)
            else:
                # User tenant (personal mode)
                request.tenant_type = TenantType.USER
                request.tenant_id = str(request.user.id)

            logger.debug(f"Set tenant context: {request.tenant_type}:{request.tenant_id}")

        except Exception as e:
            logger.error(f"Failed to set tenant context: {str(e)}")
            # Default to user tenant on error
            if hasattr(request, "user") and not isinstance(request.user, AnonymousUser):
                request.tenant_type = TenantType.USER
                request.tenant_id = str(request.user.id)

        return None

    def process_response(self, request: HttpRequest, response: HttpResponse):
        """
        Process outgoing response.

        Args:
            request: Django HttpRequest object
            response: Django HttpResponse object

        Returns:
            Modified response
        """
        # Add tenant context headers to response
        if hasattr(request, "tenant_type"):
            response["X-Tenant-Type"] = str(request.tenant_type)
            if hasattr(request, "tenant_id") and request.tenant_id:
                response["X-Tenant-ID"] = str(request.tenant_id)

        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware for adding security headers to responses.

    Implements comprehensive security headers for protection against
    various web vulnerabilities.
    """

    def process_response(self, request: HttpRequest, response: HttpResponse):
        """
        Add security headers to response.

        Args:
            request: Django HttpRequest object
            response: Django HttpResponse object

        Returns:
            Modified response with security headers
        """
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response["Content-Security-Policy"] = csp_policy

        # X-Frame-Options (clickjacking protection)
        response["X-Frame-Options"] = "DENY"

        # X-Content-Type-Options (MIME sniffing protection)
        response["X-Content-Type-Options"] = "nosniff"

        # X-XSS-Protection (XSS protection)
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        response["Permissions-Policy"] = permissions_policy

        # Strict Transport Security (HTTPS only in production)
        if request.is_secure():
            response["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Expect-CT (Certificate Transparency)
        if request.is_secure():
            response["Expect-CT"] = "max-age=86400, enforce"

        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware.

    Note: For production use, consider using Django-ratelimit or similar
    more sophisticated rate limiting solution.
    """

    def __init__(self, get_response):
        """Initialize rate limiting middleware."""
        self.get_response = get_response
        self.rate_limits = {}  # Simple in-memory storage (use Redis for production)
        super().__init__(get_response)

    def process_request(self, request: HttpRequest):
        """
        Check rate limits for incoming request.

        Args:
            request: Django HttpRequest object
        """
        import time

        from django.core.cache import cache
        from django.http import HttpResponse

        # Get client IP
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        # Define rate limits (requests per minute)
        rate_limits = {
            "default": 60,  # 60 requests per minute
            "auth": 10,  # 10 auth requests per minute
            "api": 100,  # 100 API requests per minute
        }

        # Determine rate limit type
        rate_limit_type = "default"
        if "/auth/" in request.path or "/login" in request.path:
            rate_limit_type = "auth"
        elif "/api/" in request.path:
            rate_limit_type = "api"

        limit = rate_limits[rate_limit_type]
        cache_key = f"rate_limit:{rate_limit_type}:{ip}"

        # Get current count
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for IP {ip} on {request.path}")
            return HttpResponse("Rate limit exceeded. Please try again later.", status=429)

        # Increment count
        cache.set(cache_key, current_count + 1, 60)  # 60 seconds window

        return None


class ModelAuditMiddleware(MiddlewareMixin):
    """
    Middleware for automatic model change auditing.

    Tracks Django model changes automatically by hooking into
    the ORM signals.
    """

    def __init__(self, get_response):
        """Initialize model audit middleware."""
        self.get_response = get_response
        self._setup_model_signals()
        super().__init__(get_response)

    def _setup_model_signals(self):
        """Set up Django model signals for audit logging."""
        import threading

        from django.db.models.signals import post_delete, post_save, pre_save
        from django.dispatch import receiver

        try:
            from .django_audit import audit_logger
        except ImportError:
            # Fallback if audit logger is not available
            class MockAuditLogger:
                def log_model_change(self, **kwargs):
                    pass
            audit_logger = MockAuditLogger()

        # Thread-local storage for tracking changes
        _thread_locals = threading.local()

        @receiver(pre_save)
        def track_model_changes(sender, instance, **kwargs):
            """Track model changes before save."""
            try:
                # Skip audit log model itself to prevent recursion
                if sender.__name__ == "AuditLog":
                    return

                # Get old values for existing instances
                if instance.pk:
                    try:
                        old_instance = sender.objects.get(pk=instance.pk)
                        old_values = {}
                        for field in instance._meta.fields:
                            field_name = field.name
                            old_values[field_name] = getattr(old_instance, field_name, None)

                        # Store in thread-local storage
                        if not hasattr(_thread_locals, "model_changes"):
                            _thread_locals.model_changes = {}
                        _thread_locals.model_changes[id(instance)] = old_values
                    except sender.DoesNotExist:
                        pass
            except Exception as e:
                logger.error(f"Failed to track model changes: {str(e)}")

        @receiver(post_save)
        def log_model_save(sender, instance, created, **kwargs):
            """Log model save events."""
            try:
                # Skip audit log model itself to prevent recursion
                if sender.__name__ == "AuditLog":
                    return

                action = "CREATE" if created else "UPDATE"
                old_values = None

                # Get old values from thread-local storage
                if hasattr(_thread_locals, "model_changes"):
                    old_values = _thread_locals.model_changes.get(id(instance))
                    # Clean up
                    if id(instance) in _thread_locals.model_changes:
                        del _thread_locals.model_changes[id(instance)]

                # Get user from current request if available
                user = getattr(_thread_locals, "current_user", None)
                request = getattr(_thread_locals, "current_request", None)

                audit_logger.log_model_change(
                    action=action, model_instance=instance, user=user, old_values=old_values, request=request
                )

            except Exception as e:
                logger.error(f"Failed to log model save: {str(e)}")

        @receiver(post_delete)
        def log_model_delete(sender, instance, **kwargs):
            """Log model delete events."""
            try:
                # Skip audit log model itself to prevent recursion
                if sender.__name__ == "AuditLog":
                    return

                # Get user from current request if available
                user = getattr(_thread_locals, "current_user", None)
                request = getattr(_thread_locals, "current_request", None)

                audit_logger.log_model_change(action="DELETE", model_instance=instance, user=user, request=request)

            except Exception as e:
                logger.error(f"Failed to log model delete: {str(e)}")

    def process_request(self, request: HttpRequest):
        """Store request context for model signals."""
        import threading

        _thread_locals = threading.local()

        # Store current request and user for model signals
        _thread_locals.current_request = request
        _thread_locals.current_user = (
            request.user if hasattr(request, "user") and request.user.is_authenticated else None
        )

        return None
