"""
Development Django settings.
Settings for development environment.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "web", "*"]

# Development-specific apps (commented out missing dependencies)
# INSTALLED_APPS += [
#     "django_extensions",
# ]

# Development middleware
# Remove invalid middleware that was causing issues
# MIDDLEWARE += [
#     "django.middleware.debug.MiddlewareNotUsed",
# ]

# Development database settings - use PostgreSQL for consistency
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "django_app_dev"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# Development cache settings - use dummy cache to avoid dependency issues
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development logging
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["root"]["level"] = "DEBUG"

# Disable HTTPS redirects for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Development-specific settings
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Django Debug Toolbar settings (if installed)
if "django_debug_toolbar" in INSTALLED_APPS:
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    }
