import pytest
from bs4 import BeautifulSoup

from django.contrib.auth.models import User
from django.test import Client

from django.urls import reverse


@pytest.mark.django_db
def test_index_redirects_development():
    """
    Tests that going to root / redirects to /overview
    """
    client = Client()
    user = User.objects.create(username="super", password="super")
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")

    response = client.get("/")

    assert response.status_code == 302  # Redirect
    assert response.url == reverse("overview")


@pytest.mark.django_db
def test_overview_shows_instruments():
    """
    Tests that the expected number of instruments is shown on the overview page.
    """
    client = Client(
        HTTP_USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36')
    user = User.objects.create(username="super", password="super")
    client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")

    response = client.get("/overview/")

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, "html.parser")
    instrument_btns = soup.find_all("div", {"class": "instrument-btn"})

    # assert the expected instruments are present
    assert len(instrument_btns) == 12
    expected_instruments = ["ENGINX", "GEM", "HRPD", "LARMOR", "MAPS", "MARI", "MERLIN", "MUSR", "OSIRIS", "POLARIS",
                            "POLREF", "WISH"]

    # check their actual names
    for instrument in instrument_btns:
        assert instrument.find("a").text in expected_instruments
