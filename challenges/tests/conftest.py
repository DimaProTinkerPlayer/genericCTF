import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

PASSWORD = "S0me-strong-pass"


@pytest.fixture
def auth_client():
    def make(user):
        client = APIClient()
        token = RefreshToken.for_user(user).access_token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    return make


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="player", password=PASSWORD)


@pytest.fixture
def admin_user():
    return get_user_model().objects.create_user(username="boss", password=PASSWORD, is_staff=True)


@pytest.fixture
def roles(auth_client, user, admin_user):
    return {
        "anon": APIClient(),
        "user": auth_client(user),
        "admin": auth_client(admin_user),
    }
