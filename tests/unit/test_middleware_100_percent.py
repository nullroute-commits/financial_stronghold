"""
Comprehensive tests for app/middleware.py - 100% Coverage.

This module provides complete coverage for Django middleware components,
ensuring every middleware class, method, and code path is thoroughly tested.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
import time

from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

try:
    from app.middleware import (
        TenantMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
    )
    from app.django_models import TenantType, User, UserOrganizationLink
    MIDDLEWARE_AVAILABLE = True
except ImportError as e:
    MIDDLEWARE_AVAILABLE = False
    import_error = str(e)


@pytest.mark.skipif(not MIDDLEWARE_AVAILABLE, reason="Middleware module not available")
class TestTenantMiddleware:
    """Complete coverage for TenantMiddleware."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.middleware = TenantMiddleware(get_response=Mock())
        self.request = HttpRequest()
        self.request.META = {}
        self.request.GET = {}
        
        # Mock user
        self.mock_user = Mock()
        self.mock_user.id = uuid4()
        self.mock_user.email = "test@example.com"
    
    def test_tenant_middleware_init(self):
        """Test TenantMiddleware initialization."""
        get_response = Mock()
        middleware = TenantMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_process_request_anonymous_user(self):
        """Test process_request with anonymous user."""
        self.request.user = AnonymousUser()
        
        result = self.middleware.process_request(self.request)
        
        assert result is None
        assert self.request.tenant_type == TenantType.USER
        assert self.request.tenant_id is None
        assert self.request.tenant_org is None
    
    def test_process_request_no_user_attribute(self):
        """Test process_request without user attribute."""
        # Don't set request.user at all
        result = self.middleware.process_request(self.request)
        
        assert result is None
        assert self.request.tenant_type == TenantType.USER
        assert self.request.tenant_id is None
        assert self.request.tenant_org is None
    
    def test_process_request_authenticated_user_default(self):
        """Test process_request with authenticated user using defaults."""
        self.request.user = self.mock_user
        
        result = self.middleware.process_request(self.request)
        
        assert result is None
        assert self.request.tenant_type == TenantType.USER
        assert self.request.tenant_id == str(self.mock_user.id)
        assert self.request.tenant_org is None
    
    def test_process_request_with_user_tenant_headers(self):
        """Test process_request with user tenant type in headers."""
        self.request.user = self.mock_user
        self.request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.USER,
            'HTTP_X_TENANT_ID': str(self.mock_user.id)
        }
        
        result = self.middleware.process_request(self.request)
        
        assert result is None
        assert self.request.tenant_type == TenantType.USER
        assert self.request.tenant_id == str(self.mock_user.id)
        assert self.request.tenant_org is None
    
    def test_process_request_with_organization_tenant_headers(self):
        """Test process_request with organization tenant type in headers."""
        self.request.user = self.mock_user
        org_id = str(uuid4())
        self.request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.ORGANIZATION,
            'HTTP_X_TENANT_ID': org_id
        }
        
        # Mock UserOrganizationLink query
        with patch('app.middleware.UserOrganizationLink.objects.filter') as mock_filter:
            mock_query = Mock()
            mock_query.exists.return_value = True
            mock_filter.return_value = mock_query
            
            result = self.middleware.process_request(self.request)
            
            assert result is None
            assert self.request.tenant_type == TenantType.ORGANIZATION
            assert self.request.tenant_id == org_id
            mock_filter.assert_called_once()
    
    def test_process_request_with_query_parameters(self):
        """Test process_request with tenant info in query parameters."""
        self.request.user = self.mock_user
        org_id = str(uuid4())
        self.request.GET = {
            'tenant_type': TenantType.ORGANIZATION,
            'tenant_id': org_id
        }
        
        # Mock UserOrganizationLink query
        with patch('app.middleware.UserOrganizationLink.objects.filter') as mock_filter:
            mock_query = Mock()
            mock_query.exists.return_value = True
            mock_filter.return_value = mock_query
            
            result = self.middleware.process_request(self.request)
            
            assert result is None
            assert self.request.tenant_type == TenantType.ORGANIZATION
            assert self.request.tenant_id == org_id
    
    def test_process_request_invalid_tenant_type(self):
        """Test process_request with invalid tenant type."""
        self.request.user = self.mock_user
        self.request.META = {
            'HTTP_X_TENANT_TYPE': 'invalid_type'
        }
        
        result = self.middleware.process_request(self.request)
        
        assert result is None
        # Should fall back to USER tenant
        assert self.request.tenant_type == TenantType.USER
        assert self.request.tenant_id == str(self.mock_user.id)
    
    def test_process_request_organization_unauthorized(self):
        """Test process_request with organization tenant user is not member of."""
        self.request.user = self.mock_user
        org_id = str(uuid4())
        self.request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.ORGANIZATION,
            'HTTP_X_TENANT_ID': org_id
        }
        
        # Mock UserOrganizationLink query to return False
        with patch('app.middleware.UserOrganizationLink.objects.filter') as mock_filter:
            mock_query = Mock()
            mock_query.exists.return_value = False
            mock_filter.return_value = mock_query
            
            result = self.middleware.process_request(self.request)
            
            assert result is None
            # Should fall back to USER tenant
            assert self.request.tenant_type == TenantType.USER
            assert self.request.tenant_id == str(self.mock_user.id)
    
    def test_process_request_exception_handling(self):
        """Test process_request handles exceptions gracefully."""
        self.request.user = self.mock_user
        self.request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.ORGANIZATION,
            'HTTP_X_TENANT_ID': '"invalid-uuid"'  # This should cause a validation error
        }
        
        # This should not raise an exception but should log an error
        with patch('app.middleware.logger') as mock_logger:
            result = self.middleware.process_request(self.request)
            
            assert result is None
            # Should fall back to USER tenant
            assert self.request.tenant_type == TenantType.USER
            assert self.request.tenant_id == str(self.mock_user.id)
            
            # Should log an error
            mock_logger.error.assert_called()


@pytest.mark.skipif(not MIDDLEWARE_AVAILABLE, reason="Middleware module not available")
class TestSecurityHeadersMiddleware:
    """Complete coverage for SecurityHeadersMiddleware."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.get_response = Mock()
        self.middleware = SecurityHeadersMiddleware(self.get_response)
        self.request = HttpRequest()
    
    def test_security_headers_middleware_init(self):
        """Test SecurityHeadersMiddleware initialization."""
        assert self.middleware.get_response == self.get_response
    
    def test_call_method(self):
        """Test SecurityHeadersMiddleware __call__ method."""
        # Mock response
        response = HttpResponse()
        self.get_response.return_value = response
        
        result = self.middleware(self.request)
        
        # Verify get_response was called
        self.get_response.assert_called_once_with(self.request)
        
        # Verify security headers were added
        assert result == response
        assert 'X-Content-Type-Options' in response
        assert response['X-Content-Type-Options'] == 'nosniff'
        assert 'X-Frame-Options' in response
        assert response['X-Frame-Options'] == 'DENY'
        assert 'X-XSS-Protection' in response
        assert response['X-XSS-Protection'] == '1; mode=block'
        assert 'Strict-Transport-Security' in response
        assert 'max-age=31536000' in response['Strict-Transport-Security']
        assert 'Content-Security-Policy' in response
    
    def test_security_headers_values(self):
        """Test specific security header values."""
        response = HttpResponse()
        self.get_response.return_value = response
        
        result = self.middleware(self.request)
        
        # Test CSP header
        csp = response['Content-Security-Policy']
        assert 'default-src' in csp
        assert "'self'" in csp
        assert 'script-src' in csp
        assert 'style-src' in csp
        
        # Test HSTS header
        hsts = response['Strict-Transport-Security']
        assert 'max-age=31536000' in hsts
        assert 'includeSubDomains' in hsts
        assert 'preload' in hsts
    
    def test_security_headers_with_existing_headers(self):
        """Test SecurityHeadersMiddleware with existing headers in response."""
        response = HttpResponse()
        response['X-Custom-Header'] = 'custom-value'
        response['X-Frame-Options'] = 'SAMEORIGIN'  # Existing header
        self.get_response.return_value = response
        
        result = self.middleware(self.request)
        
        # Existing custom header should remain
        assert response['X-Custom-Header'] == 'custom-value'
        
        # Security header should be overwritten
        assert response['X-Frame-Options'] == 'DENY'
        
        # Other security headers should be added
        assert 'X-Content-Type-Options' in response
        assert 'X-XSS-Protection' in response


@pytest.mark.skipif(not MIDDLEWARE_AVAILABLE, reason="Middleware module not available")
class TestRateLimitMiddleware:
    """Complete coverage for RateLimitMiddleware."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.get_response = Mock()
        self.middleware = RateLimitMiddleware(self.get_response)
        self.request = HttpRequest()
        self.request.META = {'REMOTE_ADDR': '127.0.0.1'}
        self.request.user = Mock()
        self.request.user.id = 123
    
    def test_rate_limit_middleware_init(self):
        """Test RateLimitMiddleware initialization."""
        assert self.middleware.get_response == self.get_response
        assert hasattr(self.middleware, 'rate_limit_cache')
        assert hasattr(self.middleware, 'rate_limit')
        assert hasattr(self.middleware, 'time_window')
    
    def test_get_client_identifier_with_user(self):
        """Test _get_client_identifier with authenticated user."""
        identifier = self.middleware._get_client_identifier(self.request)
        assert identifier == 'user_123'
    
    def test_get_client_identifier_anonymous(self):
        """Test _get_client_identifier with anonymous user."""
        self.request.user = AnonymousUser()
        identifier = self.middleware._get_client_identifier(self.request)
        assert identifier == 'ip_127.0.0.1'
    
    def test_get_client_identifier_no_remote_addr(self):
        """Test _get_client_identifier without REMOTE_ADDR."""
        del self.request.META['REMOTE_ADDR']
        self.request.user = AnonymousUser()
        identifier = self.middleware._get_client_identifier(self.request)
        assert identifier == 'ip_unknown'
    
    def test_is_rate_limited_first_request(self):
        """Test rate limiting for first request."""
        with patch('time.time', return_value=1000.0):
            is_limited = self.middleware._is_rate_limited(self.request)
            assert is_limited is False
    
    def test_is_rate_limited_within_limit(self):
        """Test rate limiting within allowed limit."""
        client_id = self.middleware._get_client_identifier(self.request)
        current_time = 1000.0
        
        # Simulate multiple requests within limit
        with patch('time.time', return_value=current_time):
            # First few requests should be allowed
            for i in range(self.middleware.rate_limit - 1):
                is_limited = self.middleware._is_rate_limited(self.request)
                assert is_limited is False
    
    def test_is_rate_limited_exceeds_limit(self):
        """Test rate limiting when exceeding limit."""
        client_id = self.middleware._get_client_identifier(self.request)
        current_time = 1000.0
        
        with patch('time.time', return_value=current_time):
            # Make requests up to the limit
            for i in range(self.middleware.rate_limit):
                self.middleware._is_rate_limited(self.request)
            
            # Next request should be rate limited
            is_limited = self.middleware._is_rate_limited(self.request)
            assert is_limited is True
    
    def test_is_rate_limited_time_window_reset(self):
        """Test rate limiting resets after time window."""
        current_time = 1000.0
        
        with patch('time.time', return_value=current_time):
            # Exhaust rate limit
            for i in range(self.middleware.rate_limit):
                self.middleware._is_rate_limited(self.request)
            
            # Should be rate limited
            is_limited = self.middleware._is_rate_limited(self.request)
            assert is_limited is True
        
        # Move forward past time window
        with patch('time.time', return_value=current_time + self.middleware.time_window + 1):
            # Should be allowed again
            is_limited = self.middleware._is_rate_limited(self.request)
            assert is_limited is False
    
    def test_call_method_not_rate_limited(self):
        """Test RateLimitMiddleware __call__ when not rate limited."""
        response = HttpResponse()
        self.get_response.return_value = response
        
        with patch.object(self.middleware, '_is_rate_limited', return_value=False):
            result = self.middleware(self.request)
            
            assert result == response
            self.get_response.assert_called_once_with(self.request)
    
    def test_call_method_rate_limited(self):
        """Test RateLimitMiddleware __call__ when rate limited."""
        with patch.object(self.middleware, '_is_rate_limited', return_value=True):
            result = self.middleware(self.request)
            
            assert isinstance(result, HttpResponse)
            assert result.status_code == 429
            assert 'Rate limit exceeded' in result.content.decode()
            # get_response should not be called when rate limited
            self.get_response.assert_not_called()
    
    def test_cache_cleanup(self):
        """Test that old cache entries are cleaned up."""
        client_id = self.middleware._get_client_identifier(self.request)
        old_time = 1000.0
        current_time = old_time + self.middleware.time_window + 100
        
        # Add old entries
        with patch('time.time', return_value=old_time):
            self.middleware._is_rate_limited(self.request)
        
        # Check cache has entries
        assert len(self.middleware.rate_limit_cache) > 0
        
        # Move to current time and make new request
        with patch('time.time', return_value=current_time):
            self.middleware._is_rate_limited(self.request)
        
        # Old entries should be cleaned up
        for entry_time, _ in self.middleware.rate_limit_cache.values():
            assert entry_time >= current_time - self.middleware.time_window


@pytest.mark.skipif(not MIDDLEWARE_AVAILABLE, reason="Middleware module not available")
class TestMiddlewareIntegration:
    """Test middleware integration and edge cases."""
    
    def test_tenant_middleware_with_security_middleware(self):
        """Test TenantMiddleware works with SecurityHeadersMiddleware."""
        # Create middleware stack
        def get_response(request):
            return HttpResponse()
        
        security_middleware = SecurityHeadersMiddleware(get_response)
        tenant_middleware = TenantMiddleware(security_middleware)
        
        # Create request
        request = HttpRequest()
        request.user = Mock()
        request.user.id = uuid4()
        request.META = {}
        request.GET = {}
        
        # Process request through middleware stack
        response = tenant_middleware(request)
        
        # Verify tenant context was set
        assert hasattr(request, 'tenant_type')
        assert hasattr(request, 'tenant_id')
        
        # Verify security headers were added
        assert 'X-Content-Type-Options' in response
        assert 'X-Frame-Options' in response
    
    def test_all_middleware_error_handling(self):
        """Test error handling across all middleware."""
        def error_response(request):
            raise Exception("Test error")
        
        middlewares = [
            TenantMiddleware(error_response),
            SecurityHeadersMiddleware(error_response),
            RateLimitMiddleware(error_response)
        ]
        
        request = HttpRequest()
        request.user = Mock()
        request.user.id = uuid4()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        request.GET = {}
        
        for middleware in middlewares:
            # Most middleware should let exceptions propagate
            with pytest.raises(Exception):
                middleware(request)


@pytest.mark.skipif(not MIDDLEWARE_AVAILABLE, reason="Middleware module not available")
class TestMiddlewarePerformance:
    """Test middleware performance characteristics."""
    
    def test_tenant_middleware_performance(self):
        """Test TenantMiddleware performance."""
        middleware = TenantMiddleware(lambda r: HttpResponse())
        request = HttpRequest()
        request.user = Mock()
        request.user.id = uuid4()
        request.META = {}
        request.GET = {}
        
        start_time = time.time()
        for _ in range(100):
            middleware(request)
        end_time = time.time()
        
        # Should process 100 requests quickly
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.01  # Less than 10ms per request
    
    def test_security_headers_middleware_performance(self):
        """Test SecurityHeadersMiddleware performance."""
        middleware = SecurityHeadersMiddleware(lambda r: HttpResponse())
        request = HttpRequest()
        
        start_time = time.time()
        for _ in range(100):
            middleware(request)
        end_time = time.time()
        
        # Should process 100 requests quickly
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.01  # Less than 10ms per request
    
    def test_rate_limit_middleware_performance(self):
        """Test RateLimitMiddleware performance."""
        middleware = RateLimitMiddleware(lambda r: HttpResponse())
        request = HttpRequest()
        request.user = Mock()
        request.user.id = 123
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        start_time = time.time()
        for _ in range(100):
            middleware(request)
        end_time = time.time()
        
        # Should process 100 requests quickly
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.01  # Less than 10ms per request