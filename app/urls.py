"""
URL configuration for the app module.
Includes both API and web interface URL patterns using Django REST Framework.

Last updated: 2025-01-02 by Team Beta (Architecture & Backend Agents)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    UserViewSet, AccountViewSet, TransactionViewSet, BudgetViewSet,
    OrganizationViewSet, AuditLogViewSet, HealthCheckViewSet
)
from .api.import_views import (
    FileUploadViewSet, ImportJobViewSet, ImportedTransactionViewSet,
    ImportTemplateViewSet, ImportAnalyticsViewSet, ImportHealthCheckViewSet
)

# Create DRF router for API endpoints
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'accounts', AccountViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'organizations', OrganizationViewSet)
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'health', HealthCheckViewSet, basename='health')

# Import feature API endpoints
router.register(r'import/files', FileUploadViewSet, basename='fileupload')
router.register(r'import/jobs', ImportJobViewSet, basename='importjob')
router.register(r'import/transactions', ImportedTransactionViewSet, basename='importedtransaction')
router.register(r'import/templates', ImportTemplateViewSet, basename='importtemplate')
router.register(r'import/analytics', ImportAnalyticsViewSet, basename='importanalytics')
router.register(r'import/health', ImportHealthCheckViewSet, basename='importhealth')

urlpatterns = [
    # Web interface URLs
    path("", include("app.web_urls")),
    # API URLs using Django REST Framework
    path("api/v1/", include(router.urls)),
    # API authentication
    path("api-auth/", include("rest_framework.urls")),
]
