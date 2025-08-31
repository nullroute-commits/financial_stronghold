"""
Django app configuration for the financial stronghold application.

Last updated: 2025-08-31 by AI Assistant
"""

from django.apps import AppConfig


class AppConfig(AppConfig):
    """Application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Financial Stronghold"

    def ready(self):
        """
        Called when the app is ready.
        Initialize default roles and permissions.
        """
        # Skip initialization during migrations and management commands
        import sys

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return

        import logging

        logger = logging.getLogger(__name__)

        try:
            # Import here to avoid circular imports
            from .django_rbac import initialize_default_permissions, initialize_default_roles, sync_roles_with_groups

            # Initialize default system roles and permissions
            initialize_default_roles()
            initialize_default_permissions()
            sync_roles_with_groups()

            logger.info("Successfully initialized default RBAC system")

        except Exception as e:
            # Don't fail app startup if RBAC initialization fails
            logger.warning(f"Failed to initialize RBAC system: {str(e)}")
