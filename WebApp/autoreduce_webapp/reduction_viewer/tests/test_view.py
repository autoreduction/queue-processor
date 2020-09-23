import pytest
from django.contrib.auth.models import User
from django.test import Client

from django.urls import reverse

@pytest.mark.django_db
def test_index_redirects_development():
    client = Client()
    user = User.objects.create(username="super", password="super")
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")

    response = client.get("/")

    assert response.status_code == 302 # Redirect
    assert response.url == reverse("overview")
