import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.validators import PasswordComplexityValidator

User = get_user_model()

URL = "/api/v1/auth/register/"


def valid_data():
    return {
        "username": "player1",
        "email": "player1@example.com",
        "password": "StrongPass123",
        "password_confirm": "StrongPass123",
    }


def register(data):
    return APIClient().post(URL, data, format="json")


@pytest.mark.django_db
def test_register_success():
    response = register(valid_data())

    assert response.status_code == 201
    assert response.data["username"] == "player1"
    assert response.data["email"] == "player1@example.com"
    assert "password" not in response.data
    assert "password_confirm" not in response.data


@pytest.mark.django_db
def test_password_is_hashed():
    register(valid_data())

    user = User.objects.get(username="player1")
    assert user.password != "StrongPass123"
    assert user.check_password("StrongPass123")


@pytest.mark.django_db
def test_first_and_last_name_are_saved():
    data = valid_data()
    data["first_name"] = "Іван"
    data["last_name"] = "Петренко"

    response = register(data)

    assert response.status_code == 201
    assert response.data["first_name"] == "Іван"
    assert response.data["last_name"] == "Петренко"


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["username", "email", "password", "password_confirm"])
def test_required_fields(field):
    data = valid_data()
    del data[field]

    response = register(data)

    assert response.status_code == 400
    assert field in response.data["fields"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field, length",
    [("username", 151), ("first_name", 151), ("last_name", 151), ("password", 129)],
)
def test_max_length(field, length):
    data = valid_data()
    data[field] = "a" * length

    response = register(data)

    assert response.status_code == 400
    assert field in response.data["fields"]


@pytest.mark.django_db
def test_email_max_length():
    data = valid_data()
    data["email"] = "a" * 250 + "@example.com"

    response = register(data)

    assert response.status_code == 400
    assert "email" in response.data["fields"]


@pytest.mark.django_db
def test_invalid_email():
    data = valid_data()
    data["email"] = "not-an-email"

    response = register(data)

    assert response.status_code == 400
    assert "email" in response.data["fields"]


@pytest.mark.django_db
def test_email_unique_ignore_case():
    User.objects.create_user(username="other", email="player1@example.com", password="StrongPass123")
    data = valid_data()
    data["email"] = "PLAYER1@Example.com"

    response = register(data)

    assert response.status_code == 400
    assert "email" in response.data["fields"]


@pytest.mark.django_db
def test_username_unique_ignore_case():
    User.objects.create_user(username="player1", email="other@example.com", password="StrongPass123")
    data = valid_data()
    data["username"] = "PLAYER1"

    response = register(data)

    assert response.status_code == 400
    assert "username" in response.data["fields"]


@pytest.mark.django_db
def test_invalid_username_characters():
    data = valid_data()
    data["username"] = "bad name!"

    response = register(data)

    assert response.status_code == 400
    assert "username" in response.data["fields"]


@pytest.mark.django_db
def test_passwords_do_not_match():
    data = valid_data()
    data["password_confirm"] = "OtherPass123"

    response = register(data)

    assert response.status_code == 400
    assert response.data["fields"]["password_confirm"] == ["Паролі не збігаються."]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "password",
    ["Ab1", "12345678901", "password123", "OnlyLetters", "Player1abc"],
)
def test_weak_password(password):
    data = valid_data()
    data["password"] = password
    data["password_confirm"] = password

    response = register(data)

    assert response.status_code == 400
    assert "password" in response.data["fields"]


@pytest.mark.django_db
def test_user_not_created_on_error():
    data = valid_data()
    data["password_confirm"] = "OtherPass123"

    register(data)

    assert not User.objects.filter(username="player1").exists()


def test_complexity_validator_help_text():
    assert PasswordComplexityValidator().get_help_text() == "Пароль має містити хоча б одну літеру і одну цифру."
