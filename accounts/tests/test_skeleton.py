import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from config.exceptions import custom_exception_handler


def call_view_that_raises(exc):
    class BrokenView(APIView):
        def get(self, request):
            raise exc

    request = APIRequestFactory().get("/")
    return BrokenView.as_view()(request)


@pytest.mark.django_db
def test_custom_user_model():
    user = get_user_model().objects.create_user(username="alice", password="S0me-strong-pass")
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert str(user) == "alice"
    assert user.check_password("S0me-strong-pass")


def test_field_errors_format():
    response = call_view_that_raises(ValidationError({"email": ["Обов'язкове поле."]}))
    assert response.status_code == 400
    assert response.data == {
        "error": "Помилка валідації",
        "fields": {"email": ["Обов'язкове поле."]},
    }


def test_non_field_errors_format():
    response = call_view_that_raises(ValidationError({"non_field_errors": ["Паролі не збігаються."]}))
    assert response.status_code == 400
    assert response.data == {"error": "Паролі не збігаються.", "fields": {}}


def test_list_validation_error_format():
    response = call_view_that_raises(ValidationError("Щось не так."))
    assert response.status_code == 400
    assert response.data == {"error": "Щось не так.", "fields": {}}


def test_not_found_format():
    response = call_view_that_raises(NotFound("Не знайдено."))
    assert response.status_code == 404
    assert response.data == {"error": "Не знайдено.", "fields": {}}


def test_unknown_exception_is_not_handled():
    assert custom_exception_handler(ValueError("boom"), {}) is None


def test_non_field_errors_as_string_is_not_cut():
    response = call_view_that_raises(ValidationError({"non_field_errors": "Паролі не збігаються."}))
    assert response.status_code == 400
    assert response.data == {"error": "Паролі не збігаються.", "fields": {}}


def test_empty_validation_error_list():
    response = call_view_that_raises(ValidationError([]))
    assert response.status_code == 400
    assert response.data == {"error": "Помилка валідації", "fields": {}}


def test_error_detail_as_list():
    response = call_view_that_raises(PermissionDenied(["Немає доступу."]))
    assert response.status_code == 403
    assert response.data == {"error": "Немає доступу.", "fields": {}}


def test_error_detail_as_dict_without_detail_key():
    response = call_view_that_raises(APIException({"code": "щось"}))
    assert response.status_code == 500
    assert response.data == {"error": "Помилка", "fields": {}}
