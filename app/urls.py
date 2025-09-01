"""
URL configuration for the app module.
Includes both API and web interface URL patterns.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""

from django.http import JsonResponse
from django.urls import path, include


def api_home_view(request):
    """Basic API home view."""
    return JsonResponse(
        {"message": "Welcome to Django 5 Multi-Architecture CI/CD Pipeline", "status": "running", "version": "1.0.0"}
    )


urlpatterns = [
    # Web interface URLs
    path("", include("app.web_urls")),
    
    # API URLs (keep existing API home for backward compatibility)
    path("api/", api_home_view, name="api_home"),
]
