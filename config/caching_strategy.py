"""
Caching Strategy Configuration
Team Delta - Security Sprint 4
"""

from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.redis import RedisCache
from django.core.cache.backends.memcached import MemcachedCache
import hashlib
import json
import time

class CacheManager:
    """Advanced caching strategy with multiple backends"""
    
    def __init__(self):
        self.default_ttl = 3600  # 1 hour
        self.short_ttl = 300     # 5 minutes
        self.long_ttl = 86400    # 24 hours
        
        # Cache backends
        self.redis_cache = cache
        self.memcached_cache = cache
    
    def get_cache_key(self, prefix, *args, **kwargs):
        """Generate consistent cache keys"""
        # Create a hash of the arguments
        key_data = f"{prefix}:{':'.join(map(str, args))}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def cache_function_result(self, ttl=None, key_prefix=None):
        """Decorator to cache function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_prefix:
                    cache_key = self.get_cache_key(key_prefix, *args, **kwargs)
                else:
                    cache_key = self.get_cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl or self.default_ttl)
                
                return result
            return wrapper
        return decorator
    
    def cache_queryset(self, ttl=None, key_prefix=None):
        """Cache queryset results with intelligent invalidation"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_prefix:
                    cache_key = self.get_cache_key(key_prefix, *args, **kwargs)
                else:
                    cache_key = self.get_cache_key(func.__name__, *args, **kwargs)
                
                # Try to get from cache
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                
                # Cache the queryset
                cache.set(cache_key, result, ttl or self.default_ttl)
                
                # Set up cache invalidation
                self.setup_cache_invalidation(cache_key, result)
                
                return result
            return wrapper
        return decorator
    
    def setup_cache_invalidation(self, cache_key, queryset):
        """Set up intelligent cache invalidation"""
        # This would integrate with Django signals to invalidate cache
        # when related models are updated
        pass
    
    def bulk_cache_operations(self, operations):
        """Perform bulk cache operations for efficiency"""
        # Use pipeline for Redis or bulk operations for Memcached
        if hasattr(cache, 'pipeline'):
            # Redis pipeline
            pipe = cache.pipeline()
            for op_type, key, value, ttl in operations:
                if op_type == 'set':
                    pipe.set(key, value, ttl)
                elif op_type == 'delete':
                    pipe.delete(key)
            pipe.execute()
        else:
            # Memcached bulk operations
            for op_type, key, value, ttl in operations:
                if op_type == 'set':
                    cache.set(key, value, ttl)
                elif op_type == 'delete':
                    cache.delete(key)

# Cache configuration for different environments
CACHE_CONFIGURATION = {
    'development': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    },
    'production': {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'TIMEOUT': 3600,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            }
        },
        'session': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/2',
            'TIMEOUT': 86400,
        },
        'static': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/3',
            'TIMEOUT': 31536000,  # 1 year
        }
    }
}

# Cache invalidation strategies
CACHE_INVALIDATION_STRATEGIES = {
    'time_based': {
        'enabled': True,
        'default_ttl': 3600,
        'short_ttl': 300,
        'long_ttl': 86400,
    },
    'event_based': {
        'enabled': True,
        'model_signals': True,
        'custom_events': True,
    },
    'pattern_based': {
        'enabled': True,
        'wildcard_invalidation': True,
        'prefix_invalidation': True,
    }
}

# Global cache manager instance
cache_manager = CacheManager()
