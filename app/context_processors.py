"""
Django context processors for injecting common UI context.
"""

from __future__ import annotations

from typing import Dict

from .services import ThemeService


def theme(request) -> Dict[str, str]:
    """
    Inject the active theme into all templates.
    """
    try:
        active_theme = ThemeService.resolve_theme_for_request(request)
    except Exception:
        active_theme = 'system'

    return {
        'active_theme': active_theme,
    }

