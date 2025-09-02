"""
Application monitoring and health check system.
Provides comprehensive monitoring for production readiness.

Created by Team Alpha (Infrastructure & DevOps) for Sprint 6
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from django.conf import settings
from django.core.cache import cache
from django.db import connection, connections
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class HealthCheckService:
    """Comprehensive health check service for monitoring."""
    
    def __init__(self):
        self.checks = {
            'database': self._check_database,
            'cache': self._check_cache,
            'storage': self._check_storage,
            'memory': self._check_memory,
            'dependencies': self._check_dependencies,
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        start_time = time.time()
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'framework': 'Django 5.1.3',
            'uptime': self._get_uptime(),
            'checks': {},
            'response_time_ms': 0
        }
        
        # Run all health checks
        for check_name, check_func in self.checks.items():
            try:
                check_result = check_func()
                health_data['checks'][check_name] = check_result
                
                if check_result['status'] != 'healthy':
                    health_data['status'] = 'degraded'
                    
            except Exception as e:
                logger.error(f"Health check {check_name} failed: {str(e)}")
                health_data['checks'][check_name] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                health_data['status'] = 'unhealthy'
        
        # Calculate response time
        health_data['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        return health_data
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            # Test query performance
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            migration_count = cursor.fetchone()[0]
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Check connection pool status
            db_settings = settings.DATABASES['default']
            
            return {
                'status': 'healthy' if result[0] == 1 else 'unhealthy',
                'response_time_ms': response_time,
                'migration_count': migration_count,
                'database_name': db_settings['NAME'],
                'host': db_settings['HOST'],
                'port': db_settings['PORT'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_cache(self) -> Dict[str, Any]:
        """Check cache system connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test cache write/read
            test_key = f'health_check_{int(time.time())}'
            test_value = 'health_check_value'
            
            cache.set(test_key, test_value, 60)
            retrieved_value = cache.get(test_key)
            cache.delete(test_key)
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                'status': 'healthy' if retrieved_value == test_value else 'unhealthy',
                'response_time_ms': response_time,
                'backend': settings.CACHES['default']['BACKEND'],
                'location': settings.CACHES['default']['LOCATION'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_storage(self) -> Dict[str, Any]:
        """Check file storage and disk space."""
        try:
            import shutil
            
            # Check disk space
            total, used, free = shutil.disk_usage('/')
            free_percentage = (free / total) * 100
            
            return {
                'status': 'healthy' if free_percentage > 10 else 'warning',
                'disk_free_gb': round(free / (1024**3), 2),
                'disk_total_gb': round(total / (1024**3), 2),
                'disk_free_percentage': round(free_percentage, 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            return {
                'status': 'healthy' if memory.percent < 90 else 'warning',
                'memory_used_percentage': round(memory.percent, 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                'status': 'info',
                'message': 'psutil not available for memory monitoring',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies and services."""
        dependencies = {}
        overall_status = 'healthy'
        
        # Check RabbitMQ (if configured)
        try:
            import pika
            
            rabbitmq_host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
            rabbitmq_port = getattr(settings, 'RABBITMQ_PORT', 5672)
            
            connection_params = pika.ConnectionParameters(
                host=rabbitmq_host,
                port=rabbitmq_port,
                connection_attempts=1,
                retry_delay=1
            )
            
            with pika.BlockingConnection(connection_params) as conn:
                dependencies['rabbitmq'] = {
                    'status': 'healthy',
                    'host': rabbitmq_host,
                    'port': rabbitmq_port
                }
                
        except Exception as e:
            dependencies['rabbitmq'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'degraded'
        
        return {
            'status': overall_status,
            'services': dependencies,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_uptime(self) -> str:
        """Get application uptime (simplified)."""
        try:
            # This would be more sophisticated in production
            return "Unknown (implement with process start time)"
        except Exception:
            return "Unknown"


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_request_time(self, view_name: str, duration_ms: float):
        """Record request processing time."""
        key = f'request_time_{view_name}'
        times = cache.get(key, [])
        times.append({
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 measurements
        if len(times) > 100:
            times = times[-100:]
        
        cache.set(key, times, 3600)  # 1 hour
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        return {
            'database_queries': self._get_database_metrics(),
            'cache_performance': self._get_cache_metrics(),
            'request_times': self._get_request_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            from django.db import connection
            
            queries = len(connection.queries)
            total_time = sum(float(q['time']) for q in connection.queries)
            
            return {
                'query_count': queries,
                'total_time_ms': round(total_time * 1000, 2),
                'average_time_ms': round((total_time / queries * 1000), 2) if queries > 0 else 0
            }
        except Exception:
            return {'error': 'Unable to collect database metrics'}
    
    def _get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        # This would integrate with actual cache statistics in production
        return {
            'hit_rate': 'Not implemented',
            'miss_rate': 'Not implemented',
            'eviction_rate': 'Not implemented'
        }
    
    def _get_request_metrics(self) -> Dict[str, Any]:
        """Get request performance metrics."""
        # This would collect actual request metrics in production
        return {
            'average_response_time_ms': 'Not implemented',
            'requests_per_minute': 'Not implemented',
            'error_rate': 'Not implemented'
        }


class SecurityMonitor:
    """Security monitoring and audit logging."""
    
    def __init__(self):
        self.security_events = []
    
    def log_security_event(self, event_type: str, user_id: str = None, 
                          ip_address: str = None, details: Dict = None):
        """Log security-related events."""
        event = {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Log to Django logging system
        logger.warning(f"Security event: {event_type}", extra=event)
        
        # Store in cache for monitoring dashboard
        events = cache.get('security_events', [])
        events.append(event)
        
        # Keep only last 1000 events
        if len(events) > 1000:
            events = events[-1000:]
        
        cache.set('security_events', events, 86400)  # 24 hours
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security monitoring summary."""
        events = cache.get('security_events', [])
        
        # Analyze events from last 24 hours
        recent_events = [
            e for e in events 
            if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(hours=24)
        ]
        
        # Count event types
        event_counts = {}
        for event in recent_events:
            event_type = event['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events_24h': len(recent_events),
            'event_types': event_counts,
            'last_event': events[-1] if events else None,
            'timestamp': datetime.now().isoformat()
        }


# Global instances
health_check_service = HealthCheckService()
performance_monitor = PerformanceMonitor()
security_monitor = SecurityMonitor()


# Monitoring middleware
class MonitoringMiddleware:
    """Middleware for request monitoring and metrics collection."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Record metrics
        duration_ms = (time.time() - start_time) * 1000
        view_name = getattr(request.resolver_match, 'view_name', 'unknown') if request.resolver_match else 'unknown'
        
        performance_monitor.record_request_time(view_name, duration_ms)
        
        # Log slow requests
        if duration_ms > 1000:  # > 1 second
            logger.warning(f"Slow request: {request.path} took {duration_ms:.2f}ms")
        
        return response