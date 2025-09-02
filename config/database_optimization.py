"""
Database Optimization Configuration
Team Delta - Security Sprint 4
"""

from django.conf import settings
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Database query optimization and performance monitoring"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds
        self.query_count_threshold = 100
    
    def optimize_queries(self, queryset, select_related=None, prefetch_related=None):
        """Optimize database queries with select_related and prefetch_related"""
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        return queryset
    
    def monitor_query_performance(self, func):
        """Decorator to monitor query performance"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            initial_queries = len(connection.queries)
            
            try:
                result = func(*args, **kwargs)
                
                # Calculate performance metrics
                execution_time = time.time() - start_time
                query_count = len(connection.queries) - initial_queries
                
                # Log slow queries
                if execution_time > self.slow_query_threshold:
                    logger.warning(
                        f"Slow query detected: {func.__name__} took {execution_time:.2f}s "
                        f"with {query_count} queries"
                    )
                
                # Log excessive queries
                if query_count > self.query_count_threshold:
                    logger.warning(
                        f"Excessive queries detected: {func.__name__} executed {query_count} queries"
                    )
                
                # Cache performance metrics
                cache_key = f"performance:db:{func.__name__}"
                cache.set(cache_key, {
                    'execution_time': execution_time,
                    'query_count': query_count,
                    'timestamp': time.time()
                }, 3600)
                
                return result
                
            except Exception as e:
                logger.error(f"Query performance monitoring error: {e}")
                raise
        
        return wrapper
    
    def get_performance_stats(self, func_name=None):
        """Get database performance statistics"""
        if func_name:
            cache_key = f"performance:db:{func_name}"
            return cache.get(cache_key)
        
        # Get all performance stats
        stats = {}
        for key in cache.keys("performance:db:*"):
            func_name = key.split(":")[-1]
            stats[func_name] = cache.get(key)
        
        return stats

# Database indexing configuration
DATABASE_INDEXES = {
    'app_user': [
        'username',
        'email',
        'is_active',
        'date_joined',
    ],
    'app_transaction': [
        'user_id',
        'amount',
        'created_at',
        'status',
        'category',
    ],
    'app_tag': [
        'name',
        'category',
        'user_id',
    ],
    'app_audit_log': [
        'user_id',
        'action',
        'timestamp',
        'ip_address',
    ],
}

# Query optimization patterns
QUERY_OPTIMIZATION_PATTERNS = {
    'bulk_operations': {
        'enabled': True,
        'batch_size': 1000,
        'use_transactions': True,
    },
    'lazy_loading': {
        'enabled': True,
        'max_depth': 3,
    },
    'connection_pooling': {
        'enabled': True,
        'max_connections': 20,
        'min_connections': 5,
    },
}

# Database connection optimization
DATABASE_CONNECTION_OPTIMIZATION = {
    'CONN_MAX_AGE': 600,  # 10 minutes
    'OPTIONS': {
        'MAX_CONNS': 20,
        'MIN_CONNS': 5,
        'CONNECT_TIMEOUT': 10,
        'READ_TIMEOUT': 30,
        'WRITE_TIMEOUT': 30,
    },
    'ATOMIC_REQUESTS': False,  # Disable for performance
    'AUTOCOMMIT': True,
}
