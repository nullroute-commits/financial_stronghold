import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.mark.django_db
def test_theme_settings_get_and_post(client):
    User = get_user_model()
    user = User.objects.create_user(email='t@example.com', password='p', first_name='T', last_name='U')
    client.login(email='t@example.com', password='p')

    # GET the page
    resp = client.get(reverse('settings_theme'))
    assert resp.status_code == 200

    # POST update to dark
    resp = client.post(reverse('settings_theme'), {'theme': 'dark'}, follow=True)
    assert resp.status_code == 200
    # Cookie set for ui_theme
    assert any(c.key == 'ui_theme' for c in resp.cookies.values())

