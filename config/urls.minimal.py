"""
Minimal URL configuration for Django testing.
Basic URLs without app-specific routes.

Last updated: 2025-09-02 by AI Assistant
"""

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from datetime import datetime


def health_check(request):
    """Basic health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "django-app",
        "version": "1.0.0",
        "environment": "testing",
        "checks": {
            "application": "healthy"
        }
    }
    return JsonResponse(health_status, status=200)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
]