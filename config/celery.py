"""
Celery configuration for Financial Stronghold application.
Handles background task processing for file imports and analysis.

Created by Team Phi (Infrastructure & Performance) - Sprint 7
"""

import os
from celery import Celery
from django.conf import settings

# Set default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('financial_stronghold')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Broker settings
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routing
    task_routes={
        'app.tasks.import_tasks.process_file_import_task': {'queue': 'file_processing'},
        'app.tasks.import_tasks.send_import_completion_notification': {'queue': 'notifications'},
        'app.tasks.import_tasks.send_import_failure_notification': {'queue': 'notifications'},
        'app.tasks.import_tasks.cleanup_old_import_files': {'queue': 'maintenance'},
        'app.tasks.import_tasks.generate_import_analytics': {'queue': 'analytics'},
    },
    
    # Queue settings
    task_default_queue='default',
    task_queues={
        'file_processing': {
            'exchange': 'file_processing',
            'routing_key': 'file_processing',
        },
        'notifications': {
            'exchange': 'notifications',
            'routing_key': 'notifications',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'routing_key': 'maintenance',
        },
        'analytics': {
            'exchange': 'analytics',
            'routing_key': 'analytics',
        },
    },
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-old-import-files': {
        'task': 'app.tasks.import_tasks.cleanup_old_import_files',
        'schedule': 86400.0,  # Daily
    },
    'generate-import-analytics': {
        'task': 'app.tasks.import_tasks.generate_import_analytics',
        'schedule': 3600.0,  # Hourly
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
    return 'Celery is working!'