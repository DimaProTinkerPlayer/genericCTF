from unittest import mock

import pytest
from django.db.models import ProtectedError

from challenges.models import Category, Challenge

LIST_URL = "/api/v1/categories/"


def detail_url(pk):
    return f"/api/v1/categories/{pk}/"


@pytest.fixture
def web():
    return Category.objects.create(name="Web")


def add_challenges(category, author, count):
    for number in range(count):
        item = Challenge(title=f"task {number}", description="x", category=category, author=author)
        item.set_flag("CTF{x}")
        item.save()


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["anon", "user", "admin"])
def test_list_is_public(roles, role, web):
    Category.objects.create(name="Crypto")

    response = roles[role].get(LIST_URL)

    assert response.status_code == 200
    assert [item["name"] for item in response.data] == ["Crypto", "Web"]


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["anon", "user", "admin"])
def test_detail_is_public(roles, role, web):
    response = roles[role].get(detail_url(web.id))

    assert response.status_code == 200
    assert response.data == {"id": web.id, "name": "Web"}


@pytest.mark.django_db
def test_detail_not_found(roles):
    response = roles["anon"].get(detail_url(999))

    assert response.status_code == 404
    assert response.data["error"] == "Категорію не знайдено."


@pytest.mark.django_db
@pytest.mark.parametrize("role, expected", [("anon", 401), ("user", 403), ("admin", 201)])
def test_create_permissions(roles, role, expected):
    response = roles[role].post(LIST_URL, {"name": "Pwn"}, format="json")

    assert response.status_code == expected
    assert Category.objects.filter(name="Pwn").exists() == (expected == 201)


@pytest.mark.django_db
def test_forbidden_message(roles):
    response = roles["user"].post(LIST_URL, {"name": "Pwn"}, format="json")

    assert response.data["error"] == "Цю дію може виконати лише адміністратор."


@pytest.mark.django_db
def test_create_returns_category(roles):
    response = roles["admin"].post(LIST_URL, {"name": "  Forensics  "}, format="json")

    assert response.status_code == 201
    assert response.data["name"] == "Forensics"
    assert Category.objects.get(id=response.data["id"]).name == "Forensics"


@pytest.mark.django_db
@pytest.mark.parametrize("name", ["Web", "web", "WEB"])
def test_create_duplicate_name(roles, web, name):
    response = roles["admin"].post(LIST_URL, {"name": name}, format="json")

    assert response.status_code == 400
    assert response.data["fields"]["name"] == ["Категорія з такою назвою вже існує."]
    assert Category.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("data", [{}, {"name": ""}, {"name": "   "}, {"name": "a" * 65}])
def test_create_invalid_name(roles, data):
    response = roles["admin"].post(LIST_URL, data, format="json")

    assert response.status_code == 400
    assert "name" in response.data["fields"]


@pytest.mark.django_db
@pytest.mark.parametrize("role, expected", [("anon", 401), ("user", 403), ("admin", 200)])
def test_update_permissions(roles, role, expected, web):
    response = roles[role].patch(detail_url(web.id), {"name": "Web Security"}, format="json")

    assert response.status_code == expected
    web.refresh_from_db()
    assert (web.name == "Web Security") == (expected == 200)


@pytest.mark.django_db
def test_update_duplicate_name(roles, web):
    crypto = Category.objects.create(name="Crypto")

    response = roles["admin"].patch(detail_url(crypto.id), {"name": "WEB"}, format="json")

    assert response.status_code == 400
    assert "name" in response.data["fields"]


@pytest.mark.django_db
def test_update_same_name_with_other_case(roles, web):
    response = roles["admin"].patch(detail_url(web.id), {"name": "WEB"}, format="json")

    assert response.status_code == 200
    assert response.data["name"] == "WEB"


@pytest.mark.django_db
def test_update_not_found(roles):
    response = roles["admin"].patch(detail_url(999), {"name": "x"}, format="json")

    assert response.status_code == 404


@pytest.mark.django_db
def test_put_not_allowed(roles, web):
    response = roles["admin"].put(detail_url(web.id), {"name": "x"}, format="json")

    assert response.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("role, expected", [("anon", 401), ("user", 403), ("admin", 204)])
def test_delete_permissions(roles, role, expected, web):
    response = roles[role].delete(detail_url(web.id))

    assert response.status_code == expected
    assert Category.objects.filter(id=web.id).exists() == (expected != 204)


@pytest.mark.django_db
def test_delete_not_found(roles):
    response = roles["admin"].delete(detail_url(999))

    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_with_challenges_conflict(roles, web, user):
    add_challenges(web, user, 3)

    response = roles["admin"].delete(detail_url(web.id))

    assert response.status_code == 409
    assert response.data["challenges_count"] == 3
    assert "3" in response.data["error"]
    assert Category.objects.filter(id=web.id).exists()


@pytest.mark.django_db
def test_delete_race_with_new_challenge(roles, web, user):
    add_challenges(web, user, 1)

    with mock.patch.object(Category, "delete", side_effect=ProtectedError("protected", set())):
        with mock.patch("django.db.models.QuerySet.count", side_effect=[0, 1]):
            response = roles["admin"].delete(detail_url(web.id))

    assert response.status_code == 409
    assert response.data["challenges_count"] == 1
