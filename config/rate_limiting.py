"""
Rate Limiting Configuration
Team Delta - Security Sprint 4
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from django.utils import timezone
import time

class RateLimitMiddleware:
    """Rate limiting middleware for API endpoints"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'default': 100,      # requests per minute
            'api': 1000,         # API requests per minute
            'auth': 5,           # authentication attempts per minute
            'upload': 10,        # file uploads per minute
            'admin': 1000,       # admin requests per minute
        }
    
    def __call__(self, request):
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check rate limit
        if not self.check_rate_limit(request, client_id):
            return HttpResponseTooManyRequests(
                'Rate limit exceeded. Please try again later.',
                content_type='text/plain'
            )
        
        response = self.get_response(request)
        return response
    
    def get_client_id(self, request):
        """Get unique client identifier"""
        # Use IP address as primary identifier
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Add user ID if authenticated
        if request.user.is_authenticated:
            return f"{ip}:{request.user.id}"
        
        return ip
    
    def check_rate_limit(self, request, client_id):
        """Check if request is within rate limit"""
        # Determine endpoint type
        endpoint_type = self.get_endpoint_type(request)
        limit = self.rate_limits.get(endpoint_type, self.rate_limits['default'])
        
        # Create cache key
        cache_key = f"rate_limit:{endpoint_type}:{client_id}"
        
        # Get current requests count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, 60)  # 60 seconds TTL
        return True
    
    def get_endpoint_type(self, request):
        """Determine endpoint type for rate limiting"""
        path = request.path.lower()
        
        if path.startswith('/api/'):
            return 'api'
        elif path.startswith('/auth/') or path.startswith('/login/'):
            return 'auth'
        elif path.startswith('/upload/') or 'upload' in path:
            return 'upload'
        elif path.startswith('/admin/'):
            return 'admin'
        
        return 'default'

# Rate limiting decorator for views
def rate_limit(limit_type='default', limit_value=None):
    """Decorator to apply rate limiting to specific views"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Get client identifier
            client_id = RateLimitMiddleware.get_client_id(request)
            
            # Use custom limit if provided, otherwise use default
            limit = limit_value or RateLimitMiddleware.rate_limits.get(limit_type, 100)
            
            # Check rate limit
            cache_key = f"rate_limit:{limit_type}:{client_id}"
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                return HttpResponseTooManyRequests(
                    'Rate limit exceeded. Please try again later.',
                    content_type='text/plain'
                )
            
            # Increment counter
            cache.set(cache_key, current_count + 1, 60)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
