"""
Services package for Financial Stronghold application.
Business logic and service layer implementations.
"""

from .file_import_service import FileImportService, CSVParserService, ImportDataValidator


class ThemeService:
    """
    Utilities for reading and writing user theme preferences and resolving
    the effective theme for a request context.
    """

    DEFAULT_THEME_KEY = "ui.default_theme"
    COOKIE_NAME = "ui_theme"

    @staticmethod
    def get_system_default_theme() -> str:
        from app.django_models import SystemConfiguration

        try:
            cfg = SystemConfiguration.objects.filter(key=ThemeService.DEFAULT_THEME_KEY, is_active=True).first()
            if cfg and isinstance(cfg.value, str) and cfg.value:
                return cfg.value
        except Exception:
            pass
        return "system"

    @staticmethod
    def get_user_theme(user) -> str | None:
        try:
            if user and getattr(user, 'is_authenticated', False) and hasattr(user, 'preference') and user.preference:
                return user.preference.theme
        except Exception:
            return None
        return None

    @staticmethod
    def resolve_theme_for_request(request) -> str:
        # 1) user preference
        theme = ThemeService.get_user_theme(getattr(request, 'user', None))
        if theme:
            return theme

        # 2) cookie/local guest
        cookie_theme = getattr(request, 'COOKIES', {}).get(ThemeService.COOKIE_NAME)
        if cookie_theme in {"light", "dark", "system", "high-contrast"}:
            return cookie_theme

        # 3) system default
        return ThemeService.get_system_default_theme()


__all__ = [
    'FileImportService',
    'CSVParserService', 
    'ImportDataValidator',
    'ThemeService',
]