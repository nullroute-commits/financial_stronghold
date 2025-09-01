"""
URL configuration for the application.
Main URL routing configuration.

Last updated: 2025-08-30 22:40:55 UTC by nullroute-commits
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
from datetime import datetime
import os


@never_cache
def health_check(request):
    """Comprehensive health check endpoint for deployment validation."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'django-app',
        'version': '1.0.0',
        'environment': os.environ.get('ENVIRONMENT', 'unknown'),
        'checks': {}
    }
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Cache health check
    try:
        test_key = 'health_check_test'
        test_value = 'ok'
        cache.set(test_key, test_value, 10)
        cached_value = cache.get(test_key)
        if cached_value == test_value:
            health_status['checks']['cache'] = 'healthy'
        else:
            health_status['checks']['cache'] = 'unhealthy: cache test failed'
            health_status['status'] = 'degraded'
    except Exception as e:
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Basic application check
    try:
        # Test that Django is working properly
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_count = User.objects.count()
        health_status['checks']['application'] = 'healthy'
        health_status['user_count'] = user_count
    except Exception as e:
        health_status['checks']['application'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Set appropriate HTTP status code
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    
    # Authentication URLs
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    
    # Web and API URLs
    path("", include("app.urls")),
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Add Django Debug Toolbar URLs if available
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
