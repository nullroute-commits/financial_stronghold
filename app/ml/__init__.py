"""
Machine Learning package for Financial Stronghold application.
AI-powered transaction categorization and analysis.
"""

from .categorization_service import categorization_service, get_categorization_service

__all__ = [
    'categorization_service',
    'get_categorization_service'
]