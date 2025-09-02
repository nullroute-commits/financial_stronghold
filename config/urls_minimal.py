"""
Minimal URL configuration for basic deployment test.
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

def home_view(request):
    return HttpResponse("<h1>Financial Stronghold - Production Deployment Successful!</h1><p>Django is running successfully.</p>")

def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health-check"),
    path("", home_view, name="home"),
]