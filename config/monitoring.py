"""
Monitoring and Observability Configuration
Team Delta - Security Sprint 4
"""

import logging
import json
import time
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

# Configure structured logging
class StructuredLoggingMiddleware(MiddlewareMixin):
    """Middleware for structured logging with security events"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        # Calculate response time
        response_time = time.time() - request.start_time
        
        # Log security events
        self.log_security_event(request, response, response_time)
        
        return response
    
    def log_security_event(self, request, response, response_time):
        """Log security-related events"""
        log_data = {
            'timestamp': time.time(),
            'request_id': getattr(request, 'id', None),
            'client_ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'response_time': response_time,
            'user_id': getattr(request.user, 'id', None) if request.user.is_authenticated else None,
            'session_id': request.session.session_key if hasattr(request, 'session') else None,
            'security_flags': self.get_security_flags(request, response),
        }
        
        # Log based on security level
        if self.is_security_event(request, response):
            logging.warning(f"SECURITY_EVENT: {json.dumps(log_data)}")
        else:
            logging.info(f"REQUEST_LOG: {json.dumps(log_data)}")
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
    
    def get_security_flags(self, request, response):
        """Get security-related flags"""
        flags = []
        
        # Check for suspicious patterns
        if self.contains_suspicious_patterns(request):
            flags.append('suspicious_input')
        
        # Check for rate limiting
        if response.status_code == 429:
            flags.append('rate_limited')
        
        # Check for authentication
        if not request.user.is_authenticated and request.path.startswith('/admin/'):
            flags.append('unauthorized_admin_access')
        
        # Check for CSRF
        if request.method == 'POST' and not getattr(request, 'csrf_processing_done', False):
            flags.append('csrf_missing')
        
        return flags
    
    def is_security_event(self, request, response):
        """Determine if this is a security event"""
        return (
            response.status_code in [401, 403, 429, 500] or
            self.contains_suspicious_patterns(request) or
            request.path.startswith('/admin/') and not request.user.is_authenticated
        )
    
    def contains_suspicious_patterns(self, request):
        """Check for suspicious patterns in request"""
        suspicious_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)",
            r"<script[^>]*>",
            r"javascript:",
            r"\.\./",
            r"[;&|`$()]",
        ]
        
        # Check URL parameters
        for key, value in request.GET.items():
            for pattern in suspicious_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return True
        
        # Check POST data
        if request.method == 'POST':
            for key, value in request.POST.items():
                for pattern in suspicious_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
        
        return False

# Security metrics collection
class SecurityMetrics:
    """Collect and track security metrics"""
    
    @staticmethod
    def increment_security_event(event_type):
        """Increment security event counter"""
        cache_key = f"security_metrics:{event_type}:{int(time.time() / 3600)}"
        cache.incr(cache_key, 1)
        cache.expire(cache_key, 86400)  # 24 hours
    
    @staticmethod
    def get_security_stats(hours=24):
        """Get security statistics for the last N hours"""
        stats = {}
        current_hour = int(time.time() / 3600)
        
        for hour in range(current_hour - hours, current_hour + 1):
            for event_type in ['sql_injection', 'xss', 'rate_limit', 'unauthorized_access']:
                cache_key = f"security_metrics:{event_type}:{hour}"
                count = cache.get(cache_key, 0)
                if count > 0:
                    if event_type not in stats:
                        stats[event_type] = {}
                    stats[event_type][hour] = count
        
        return stats

# Performance monitoring
class PerformanceMonitor:
    """Monitor application performance"""
    
    @staticmethod
    def record_response_time(path, response_time):
        """Record response time for a path"""
        cache_key = f"performance:{path}:{int(time.time() / 300)}"  # 5-minute buckets
        cache.incr(cache_key, 1)
        cache.expire(cache_key, 3600)  # 1 hour
    
    @staticmethod
    def get_performance_stats(path, minutes=60):
        """Get performance statistics for a path"""
        stats = []
        current_bucket = int(time.time() / 300)
        
        for bucket in range(current_bucket - (minutes // 5), current_bucket + 1):
            cache_key = f"performance:{path}:{bucket}"
            count = cache.get(cache_key, 0)
            if count > 0:
                stats.append({
                    'bucket': bucket,
                    'count': count,
                    'timestamp': bucket * 300
                })
        
        return stats
