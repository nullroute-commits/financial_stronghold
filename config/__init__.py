# Configuration Module
# Last updated: 2025-01-02 by Sprint 7 Team Phi

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not available in production
    __all__ = ()
