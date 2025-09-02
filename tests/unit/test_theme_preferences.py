import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory


@pytest.mark.django_db
def test_theme_service_resolution_user_preference(client):
    from app.services import ThemeService
    from app.django_models import UserPreference

    User = get_user_model()
    user = User.objects.create_user(email='u@example.com', password='x', first_name='U', last_name='S')
    UserPreference.objects.create(user=user, theme='dark')

    rf = RequestFactory()
    req = rf.get('/')
    req.user = user

    assert ThemeService.resolve_theme_for_request(req) == 'dark'


@pytest.mark.django_db
def test_theme_service_resolution_cookie(client):
    from app.services import ThemeService

    rf = RequestFactory()
    req = rf.get('/')
    req.COOKIES = {'ui_theme': 'high-contrast'}
    req.user = type('Anon', (), {'is_authenticated': False})()

    assert ThemeService.resolve_theme_for_request(req) == 'high-contrast'


@pytest.mark.django_db
def test_theme_context_processor_injects_active_theme(settings):
    from app.context_processors import theme

    rf = RequestFactory()
    req = rf.get('/')
    req.user = type('Anon', (), {'is_authenticated': False})()

    ctx = theme(req)
    assert 'active_theme' in ctx
    assert ctx['active_theme'] in {'light', 'dark', 'system', 'high-contrast'}

