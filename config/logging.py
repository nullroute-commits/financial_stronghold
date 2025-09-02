"""
Production-ready logging configuration.
Structured logging with JSON format for production monitoring.

Created by Team Alpha (Infrastructure & DevOps) for Sprint 6
"""

import os
import logging.config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_logging_config():
    """Get logging configuration based on environment."""
    
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    django_log_level = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')
    
    # Create logs directory
    log_dir = BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'django.log',
                'maxBytes': 1024 * 1024 * int(os.environ.get('LOG_MAX_SIZE', '10')),  # Default 10MB
                'backupCount': int(os.environ.get('LOG_BACKUP_COUNT', '5')),
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'django_errors.log',
                'maxBytes': 1024 * 1024 * 5,  # 5MB
                'backupCount': 10,
                'formatter': 'json',
            },
            'security_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'security.log',
                'maxBytes': 1024 * 1024 * 5,  # 5MB
                'backupCount': 20,
                'formatter': 'json',
            },
            'performance_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'performance.log',
                'maxBytes': 1024 * 1024 * 5,  # 5MB
                'backupCount': 10,
                'formatter': 'json',
            },
            'audit_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'audit.log',
                'maxBytes': 1024 * 1024 * 10,  # 10MB
                'backupCount': 30,
                'formatter': 'json',
            },
        },
        'root': {
            'handlers': ['console', 'file', 'error_file'],
            'level': log_level,
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': django_log_level,
                'propagate': False,
            },
            'django.security': {
                'handlers': ['security_file', 'console'],
                'level': 'WARNING',
                'propagate': False,
            },
            'app.monitoring': {
                'handlers': ['performance_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'app.django_audit': {
                'handlers': ['audit_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
            'app.django_rbac': {
                'handlers': ['security_file', 'console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }


# Production-specific logging enhancements
class StructuredLogger:
    """Structured logging utility for production monitoring."""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_request(self, request, response, duration_ms):
        """Log request information for monitoring."""
        self.logger.info(
            'request_processed',
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'user_id': str(request.user.id) if request.user.is_authenticated else None,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
    
    def log_security_event(self, event_type, user_id=None, ip_address=None, details=None):
        """Log security events for monitoring."""
        self.logger.warning(
            'security_event',
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'ip_address': ip_address,
                'details': details or {},
            }
        )
    
    def log_performance_metric(self, metric_name, value, unit='ms', details=None):
        """Log performance metrics."""
        self.logger.info(
            'performance_metric',
            extra={
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'details': details or {},
            }
        )
    
    def log_business_event(self, event_type, entity_type, entity_id, details=None):
        """Log business events for audit trail."""
        self.logger.info(
            'business_event',
            extra={
                'event_type': event_type,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'details': details or {},
            }
        )
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Global structured logger instances
request_logger = StructuredLogger('app.requests')
security_logger = StructuredLogger('app.security')
performance_logger = StructuredLogger('app.performance')
business_logger = StructuredLogger('app.business')