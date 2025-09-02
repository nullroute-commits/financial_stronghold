"""
API Performance Optimization Configuration
Team Delta - Security Sprint 4
"""

from django.conf import settings
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.cache import cache
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status
import time
import json

class APIOptimizer:
    """API performance optimization and monitoring"""
    
    def __init__(self):
        self.response_time_threshold = 1.0  # seconds
        self.cache_enabled = True
        self.compression_enabled = True
    
    def optimize_response(self, data, cache_key=None, ttl=300):
        """Optimize API response with caching and compression"""
        if cache_key and self.cache_enabled:
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
        
        # Optimize data structure
        optimized_data = self.optimize_data_structure(data)
        
        # Cache response if enabled
        if cache_key and self.cache_enabled:
            cache.set(cache_key, optimized_data, ttl)
        
        return optimized_data
    
    def optimize_data_structure(self, data):
        """Optimize data structure for API responses"""
        if isinstance(data, dict):
            # Remove None values and empty strings
            return {k: v for k, v in data.items() if v is not None and v != ''}
        elif isinstance(data, list):
            # Optimize list items
            return [self.optimize_data_structure(item) for item in data]
        return data
    
    def paginate_response(self, queryset, page_size=20, page_param='page'):
        """Implement efficient pagination"""
        paginator = Paginator(queryset, page_size)
        page_number = request.GET.get(page_param, 1)
        
        try:
            page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page = paginator.page(1)
        
        return {
            'results': page.object_list,
            'pagination': {
                'count': paginator.count,
                'next': page.has_next(),
                'previous': page.has_previous(),
                'current_page': page.number,
                'total_pages': paginator.num_pages,
                'page_size': page_size,
            }
        }
    
    def monitor_api_performance(self, func):
        """Decorator to monitor API performance"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Log slow API calls
                if response_time > self.response_time_threshold:
                    logger.warning(
                        f"Slow API call: {func.__name__} took {response_time:.2f}s"
                    )
                
                # Cache performance metrics
                cache_key = f"performance:api:{func.__name__}"
                cache.set(cache_key, {
                    'response_time': response_time,
                    'timestamp': time.time()
                }, 3600)
                
                return result
                
            except Exception as e:
                logger.error(f"API performance monitoring error: {e}")
                raise
        
        return wrapper

# API throttling configuration
API_THROTTLING = {
    'user': {
        'rate': '1000/hour',
        'burst': '100/minute',
    },
    'anon': {
        'rate': '100/hour',
        'burst': '10/minute',
    },
    'upload': {
        'rate': '10/minute',
        'burst': '5/minute',
    },
    'admin': {
        'rate': '10000/hour',
        'burst': '1000/minute',
    }
}

# Response compression configuration
RESPONSE_COMPRESSION = {
    'enabled': True,
    'min_size': 1024,  # 1KB
    'algorithms': ['gzip', 'deflate'],
    'content_types': [
        'application/json',
        'text/html',
        'text/css',
        'application/javascript',
    ]
}

# API caching configuration
API_CACHING = {
    'enabled': True,
    'default_ttl': 300,  # 5 minutes
    'long_ttl': 3600,    # 1 hour
    'short_ttl': 60,     # 1 minute
    'cache_keys': {
        'user_profile': 'user:profile:{user_id}',
        'transaction_list': 'transactions:user:{user_id}:page:{page}',
        'tag_list': 'tags:user:{user_id}',
        'audit_log': 'audit:user:{user_id}:page:{page}',
    }
}

# Global API optimizer instance
api_optimizer = APIOptimizer()
