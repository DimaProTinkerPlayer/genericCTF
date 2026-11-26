from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from events.models import Event

PASSWORD = "omegagoodunhackablepassword"
WEBHOOK = "https://discord.com/api/webhooks/67/somesecret"


@pytest.fixture
def now():
    return timezone.now()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organizer():
    return get_user_model().objects.create_user(username="organizer", password=PASSWORD)


@pytest.fixture
def other_user():
    return get_user_model().objects.create_user(username="other", password=PASSWORD)


@pytest.fixture
def admin():
    return get_user_model().objects.create_user(username="admin", password=PASSWORD, is_staff=True)


@pytest.fixture
def auth_client():
    def make(user):
        client = APIClient()
        token = RefreshToken.for_user(user).access_token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return make


@pytest.fixture
def roles(api_client, auth_client, organizer, other_user, admin):
    return {
        "anon": api_client,
        "organizer": auth_client(organizer),
        "other_user": auth_client(other_user),
        "admin": auth_client(admin),
    }


@pytest.fixture
def future_event(organizer, now):
    return Event.objects.create(
        title="MohylaCTF",
        start=now + timedelta(days=1),
        end=now + timedelta(days=2),
        organizer=organizer,
        discord_webhook=WEBHOOK,
    )


@pytest.fixture
def started_event(organizer, now):
    return Event.objects.create(
        title="CTF NOW",
        start=now - timedelta(hours=1),
        end=now + timedelta(days=1),
        organizer=organizer,
    )
