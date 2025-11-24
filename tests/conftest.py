"""Test configuration for Financial Stronghold."""

import pytest
from django.conf import settings

# Configure Django settings for pytest
pytest_plugins = ['pytest_django']


@pytest.fixture(scope="session")
def django_db_setup():
    """Setup test database."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def api_client():
    """Create API client for testing."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, django_user_model):
    """Create authenticated API client."""
    user = django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=user)
    return api_client, user