"""
Comprehensive middleware tests to achieve 100% coverage.

Following the SOP in FEATURE_DEPLOYMENT_GUIDE.md for containerized testing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.models import AnonymousUser


class TestTenantMiddlewareComplete:
    """Complete coverage for TenantMiddleware."""
    
    def test_tenant_middleware_init(self):
        """Test TenantMiddleware initialization."""
        from app.middleware import TenantMiddleware
        
        get_response = Mock()
        middleware = TenantMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_tenant_middleware_call(self):
        """Test TenantMiddleware __call__ method."""
        from app.middleware import TenantMiddleware
        
        mock_response = HttpResponse("OK")
        get_response = Mock(return_value=mock_response)
        middleware = TenantMiddleware(get_response)
        
        request = HttpRequest()
        request.user = AnonymousUser()
        request.META = {}
        request.GET = {}
        
        response = middleware(request)
        assert response == mock_response
        get_response.assert_called_once_with(request)
    
    def test_process_request_authenticated_user(self):
        """Test process_request with authenticated user."""
        from app.middleware import TenantMiddleware
        from app.django_models import TenantType
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        # Create authenticated user
        mock_user = Mock()
        mock_user.id = 123
        
        request = HttpRequest()
        request.user = mock_user
        request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.USER,
            'HTTP_X_TENANT_ID': '123'
        }
        request.GET = {}
        
        result = middleware.process_request(request)
        assert result is None
        assert hasattr(request, 'tenant_type')
        assert hasattr(request, 'tenant_id')
    
    def test_process_request_with_query_params(self):
        """Test process_request with tenant info in query params."""
        from app.middleware import TenantMiddleware
        from app.django_models import TenantType
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        mock_user = Mock()
        mock_user.id = 123
        
        request = HttpRequest()
        request.user = mock_user
        request.META = {}
        request.GET = {
            'tenant_type': TenantType.ORGANIZATION,
            'tenant_id': '456'
        }
        
        result = middleware.process_request(request)
        assert result is None
    
    def test_process_request_invalid_tenant_type(self):
        """Test process_request with invalid tenant type."""
        from app.middleware import TenantMiddleware
        from app.django_models import TenantType
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        mock_user = Mock()
        mock_user.id = 123
        
        request = HttpRequest()
        request.user = mock_user
        request.META = {'HTTP_X_TENANT_TYPE': 'invalid_type'}
        request.GET = {}
        
        result = middleware.process_request(request)
        assert result is None
        assert request.tenant_type == TenantType.USER  # Should fallback
    
    def test_process_request_organization_validation(self):
        """Test process_request with organization tenant validation."""
        from app.middleware import TenantMiddleware
        from app.django_models import TenantType
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        mock_user = Mock()
        mock_user.id = 123
        
        request = HttpRequest()
        request.user = mock_user
        request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.ORGANIZATION,
            'HTTP_X_TENANT_ID': '789'
        }
        request.GET = {}
        
        # Mock UserOrganizationLink check
        with patch('app.middleware.UserOrganizationLink') as mock_link:
            mock_link.objects.filter.return_value.exists.return_value = True
            
            result = middleware.process_request(request)
            assert result is None
            assert request.tenant_type == TenantType.ORGANIZATION
    
    def test_process_request_organization_access_denied(self):
        """Test process_request organization access denied."""
        from app.middleware import TenantMiddleware
        from app.django_models import TenantType
        from django.core.exceptions import PermissionDenied
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        mock_user = Mock()
        mock_user.id = 123
        
        request = HttpRequest()
        request.user = mock_user
        request.META = {
            'HTTP_X_TENANT_TYPE': TenantType.ORGANIZATION,
            'HTTP_X_TENANT_ID': '789'
        }
        request.GET = {}
        
        # Mock UserOrganizationLink check to return False
        with patch('app.middleware.UserOrganizationLink') as mock_link:
            mock_link.objects.filter.return_value.exists.return_value = False
            
            with pytest.raises(PermissionDenied):
                middleware.process_request(request)
    
    def test_process_response_with_tenant_context(self):
        """Test process_response with tenant context."""
        from app.middleware import TenantMiddleware
        from app.django_models import TenantType
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.tenant_type = TenantType.USER
        request.tenant_id = "123"
        
        response = HttpResponse("OK")
        
        result = middleware.process_response(request, response)
        
        assert result == response
        assert response["X-Tenant-Type"] == "TenantType.USER"
        assert response["X-Tenant-ID"] == "123"
    
    def test_process_response_without_tenant_context(self):
        """Test process_response without tenant context."""
        from app.middleware import TenantMiddleware
        
        middleware = TenantMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        response = HttpResponse("OK")
        
        result = middleware.process_response(request, response)
        
        assert result == response
        assert "X-Tenant-Type" not in response
        assert "X-Tenant-ID" not in response


class TestSecurityHeadersMiddlewareComplete:
    """Complete coverage for SecurityHeadersMiddleware."""
    
    def test_security_headers_middleware_init(self):
        """Test SecurityHeadersMiddleware initialization."""
        from app.middleware import SecurityHeadersMiddleware
        
        get_response = Mock()
        middleware = SecurityHeadersMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_security_headers_middleware_call(self):
        """Test SecurityHeadersMiddleware __call__ method."""
        from app.middleware import SecurityHeadersMiddleware
        
        mock_response = HttpResponse("OK")
        get_response = Mock(return_value=mock_response)
        middleware = SecurityHeadersMiddleware(get_response)
        
        request = HttpRequest()
        response = middleware(request)
        
        assert response == mock_response
        get_response.assert_called_once_with(request)
    
    def test_process_response_security_headers(self):
        """Test process_response adds all required security headers."""
        from app.middleware import SecurityHeadersMiddleware
        
        middleware = SecurityHeadersMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        response = HttpResponse("OK")
        
        result = middleware.process_response(request, response)
        
        # Check all security headers are added
        assert result == response
        assert "Content-Security-Policy" in response
        assert "X-Content-Type-Options" in response
        assert "X-Frame-Options" in response
        assert "X-XSS-Protection" in response
        assert "Strict-Transport-Security" in response
        assert "Referrer-Policy" in response
        assert "Permissions-Policy" in response
        
        # Check header values
        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["X-Frame-Options"] == "DENY"
        assert response["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=" in response["Strict-Transport-Security"]
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_csp_policy_content(self):
        """Test Content Security Policy header content."""
        from app.middleware import SecurityHeadersMiddleware
        
        middleware = SecurityHeadersMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        response = HttpResponse("OK")
        
        result = middleware.process_response(request, response)
        
        csp_value = response["Content-Security-Policy"]
        assert "default-src 'self'" in csp_value
        assert "script-src 'self'" in csp_value
        assert "style-src 'self'" in csp_value
        assert "img-src 'self'" in csp_value
        assert "connect-src 'self'" in csp_value


class TestRateLimitMiddlewareComplete:
    """Complete coverage for RateLimitMiddleware."""
    
    def test_rate_limit_middleware_init(self):
        """Test RateLimitMiddleware initialization."""
        from app.middleware import RateLimitMiddleware
        
        get_response = Mock()
        middleware = RateLimitMiddleware(get_response)
        assert middleware.get_response == get_response
    
    def test_rate_limit_middleware_call(self):
        """Test RateLimitMiddleware __call__ method."""
        from app.middleware import RateLimitMiddleware
        
        mock_response = HttpResponse("OK")
        get_response = Mock(return_value=mock_response)
        middleware = RateLimitMiddleware(get_response)
        
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        request.path = '/api/test'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 0
            mock_cache.set.return_value = True
            
            response = middleware(request)
            assert response == mock_response
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_normal_rate(self, mock_time):
        """Test process_request with normal request rate."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.path = '/api/test'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 10  # Within limit
            mock_cache.set.return_value = True
            
            result = middleware.process_request(request)
            assert result is None  # Request allowed
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_rate_limit_exceeded(self, mock_time):
        """Test process_request when rate limit is exceeded."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.path = '/api/test'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 65  # Exceeds limit of 60
            
            result = middleware.process_request(request)
            assert result is not None
            assert result.status_code == 429
            assert "Rate limit exceeded" in result.content.decode()
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_x_forwarded_for(self, mock_time):
        """Test process_request with X-Forwarded-For header."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '10.0.0.1, 192.168.1.1',
            'REMOTE_ADDR': '192.168.1.1'
        }
        request.path = '/api/test'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 5
            mock_cache.set.return_value = True
            
            result = middleware.process_request(request)
            assert result is None
            
            # Should use first IP from X-Forwarded-For
            expected_key = "rate_limit_10.0.0.1_60"
            mock_cache.get.assert_called_with(expected_key, 0)
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_different_endpoints(self, mock_time):
        """Test process_request with different endpoint limits."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        # Test login endpoint (stricter limit)
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.path = '/api/auth/login'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 4  # Within login limit of 5
            mock_cache.set.return_value = True
            
            result = middleware.process_request(request)
            assert result is None
        
        # Test register endpoint (stricter limit)
        request.path = '/api/auth/register'
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 2  # Within register limit of 3
            mock_cache.set.return_value = True
            
            result = middleware.process_request(request)
            assert result is None
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_login_rate_limit_exceeded(self, mock_time):
        """Test process_request when login rate limit is exceeded."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.path = '/api/auth/login'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 6  # Exceeds login limit of 5
            
            result = middleware.process_request(request)
            assert result is not None
            assert result.status_code == 429
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_cache_error_handling(self, mock_time):
        """Test process_request handles cache errors gracefully."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.path = '/api/test'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.side_effect = Exception("Cache error")
            
            result = middleware.process_request(request)
            # Should allow request when cache fails
            assert result is None
    
    @patch('time.time', return_value=1000.0)
    def test_process_request_cache_set_error(self, mock_time):
        """Test process_request handles cache set errors gracefully."""
        from app.middleware import RateLimitMiddleware
        
        middleware = RateLimitMiddleware(lambda req: Mock())
        
        request = HttpRequest()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        request.path = '/api/test'
        
        with patch('django.core.cache.cache') as mock_cache:
            mock_cache.get.return_value = 5
            mock_cache.set.side_effect = Exception("Cache set error")
            
            result = middleware.process_request(request)
            # Should still allow request even if cache.set fails
            assert result is None