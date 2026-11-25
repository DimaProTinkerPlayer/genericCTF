import hashlib

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from challenges.admin import ChallengeAdminForm
from challenges.models import Category, Challenge, hash_flag


@pytest.fixture
def author():
    return get_user_model().objects.create_user(username="author", password="S0me-strong-pass")


@pytest.fixture
def category():
    return Category.objects.create(name="Web")


@pytest.fixture
def challenge(author, category):
    item = Challenge(title="SQLi 101", description="Знайди флаг", category=category, author=author)
    item.set_flag("CTF{secret}")
    item.save()
    return item


@pytest.mark.django_db
def test_category_name_unique(category):
    with pytest.raises(IntegrityError):
        Category.objects.create(name="Web")


@pytest.mark.django_db
def test_str(category, challenge):
    assert str(category) == "Web"
    assert str(challenge) == "SQLi 101"


@pytest.mark.django_db
def test_defaults(challenge):
    assert challenge.status == Challenge.Status.DRAFT
    assert challenge.difficulty == Challenge.Difficulty.EASY
    assert challenge.points == 500
    assert challenge.connection_info == ""
    assert challenge.created_at is not None


def test_choices():
    assert Challenge.Status.values == ["draft", "review", "active", "rejected"]
    assert Challenge.Difficulty.values == ["easy", "medium", "hard"]


@pytest.mark.django_db
def test_flag_stored_as_sha256(challenge):
    challenge.refresh_from_db()
    assert challenge.flag == hashlib.sha256(b"CTF{secret}").hexdigest()
    assert "CTF{secret}" not in challenge.flag
    assert len(challenge.flag) == 64


@pytest.mark.django_db
def test_check_flag(challenge):
    assert challenge.check_flag("CTF{secret}")
    assert challenge.check_flag("  CTF{secret}\n")
    assert not challenge.check_flag("CTF{SECRET}")
    assert not challenge.check_flag("")


def test_hash_flag_strips_whitespace():
    assert hash_flag(" abc ") == hash_flag("abc")


@pytest.mark.django_db
def test_category_delete_protected(challenge, category):
    with pytest.raises(ProtectedError):
        category.delete()


@pytest.mark.django_db
def test_author_delete_protected(challenge, author):
    with pytest.raises(ProtectedError):
        author.delete()


@pytest.mark.django_db
def test_points_must_be_positive(author, category):
    with pytest.raises(IntegrityError), transaction.atomic():
        Challenge.objects.create(title="x", description="x", category=category, author=author, points=0, flag="h")


@pytest.mark.django_db
def test_related_names(challenge, author, category):
    assert list(category.challenges.all()) == [challenge]
    assert list(author.challenges.all()) == [challenge]


def test_indexes():
    indexed = [tuple(index.fields) for index in Challenge._meta.indexes]
    assert ("status", "category") in indexed
    assert ("difficulty",) in indexed
    assert Challenge._meta.get_field("category").db_index
    assert Challenge._meta.get_field("author").db_index


def test_admin_registered():
    assert admin.site.is_registered(Category)
    assert admin.site.is_registered(Challenge)
    assert "status" in admin.site._registry[Challenge].list_display


def form_data(category, author, **extra):
    data = {
        "title": "Rev",
        "description": "Опис",
        "category": category.pk,
        "difficulty": "hard",
        "points": 300,
        "connection_info": "",
        "status": "draft",
        "author": author.pk,
    }
    data.update(extra)
    return data


@pytest.mark.django_db
def test_admin_form_hashes_flag(category, author):
    form = ChallengeAdminForm(data=form_data(category, author, raw_flag="CTF{admin}"))
    assert form.is_valid(), form.errors
    item = form.save()
    assert item.flag == hash_flag("CTF{admin}")


@pytest.mark.django_db
def test_admin_form_requires_flag_for_new(category, author):
    form = ChallengeAdminForm(data=form_data(category, author))
    assert not form.is_valid()
    assert "raw_flag" in form.errors


@pytest.mark.django_db
def test_admin_form_keeps_flag_when_empty(challenge, category, author):
    old_flag = challenge.flag
    form = ChallengeAdminForm(data=form_data(category, author, title="Нова назва"), instance=challenge)
    assert form.is_valid(), form.errors
    form.save()
    challenge.refresh_from_db()
    assert challenge.flag == old_flag
    assert challenge.title == "Нова назва"
