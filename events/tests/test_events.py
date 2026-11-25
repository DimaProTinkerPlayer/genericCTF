from datetime import timedelta

import pytest
from django.urls import reverse

from events.models import Event

from .conftest import WEBHOOK

LIST_URL = reverse("events:event_list")


def detail_url(event_id):
    return reverse("events:individual_event", kwargs={"pk": event_id})


def event_body(now, **overrides):
    body = {
        "title": "H4ck3r CTF",
        "description": "Змагання для справжніх хацкерів",
        "start": (now + timedelta(days=1)).isoformat(),
        "end": (now + timedelta(days=2)).isoformat()
    }
    return {**body, **overrides}


@pytest.mark.django_db
def test_list_is_public(api_client, future_event, started_event):
    response = api_client.get(LIST_URL)

    assert response.status_code == 200
    assert {e["id"] for e in response.data} == {future_event.id, started_event.id}


@pytest.mark.django_db
def test_detail_not_found(api_client):
    response = api_client.get(detail_url(6767))

    assert response.status_code == 404
    assert response.data["error"] == "Змагання не знайдено."


@pytest.mark.parametrize(
    "role, sees_webhook",
    [("anon", False), ("other_user", False), ("admin", False), ("organizer", True)],
)
@pytest.mark.django_db
def test_webhook_visible_only_to_organizer(role, sees_webhook, roles, future_event):
    response = roles[role].get(detail_url(future_event.id))

    assert response.status_code == 200
    assert ("discord_webhook" in response.data) == sees_webhook


@pytest.mark.django_db
def test_create_requires_auth(api_client, now):
    response = api_client.post(LIST_URL, event_body(now), format="json")

    assert response.status_code == 401
    assert not Event.objects.exists()


@pytest.mark.django_db
def test_create_event(roles, organizer, now):
    response = roles["organizer"].post(LIST_URL, event_body(now, discord_webhook=WEBHOOK), format="json")

    assert response.status_code == 201
    assert response.data["organizer"]["id"] == organizer.id
    assert response.data["discord_webhook"] == WEBHOOK
    assert Event.objects.get(id=response.data["id"]).organizer == organizer


@pytest.mark.django_db
def test_create_end_before_start(roles, now):
    body = event_body(
        now,
        start=(now + timedelta(days=2)).isoformat(),
        end=(now + timedelta(days=1)).isoformat(),
    )

    response = roles["organizer"].post(LIST_URL, body, format="json")

    assert response.status_code == 400
    assert "end" in response.data["fields"]
    assert not Event.objects.exists()


@pytest.mark.django_db
def test_create_end_before_now(roles, now):
    body = event_body(
        now,
        start=(now + timedelta(days=2)),
        end=(now - timedelta(hours=1))
    )

    response = roles["organizer"].post(LIST_URL, body, format="json")

    assert response.status_code == 400
    assert "end" in response.data["fields"]
    assert not Event.objects.exists()


@pytest.mark.parametrize(
    "webhook",
    [
        "https://discord.com.evil.com/api/webhooks/1/somecesrte",
        "http://discord.com/api/webhooks/1/thanksforlight",
        "https://example.com/hook"
    ],
)
@pytest.mark.django_db
def test_create_rejects_non_discord_webhook(roles, now, webhook):
    response = roles["organizer"].post(LIST_URL, event_body(now, discord_webhook=webhook), format="json")

    assert response.status_code == 400
    assert "discord_webhook" in response.data["fields"]


@pytest.mark.parametrize(
    "webhook",
    [
        "https://discord.com/api/webhooks/1/thanksforlight",
        "https://discordapp.com/api/webhooks/67/workinglegit"
    ],
)
@pytest.mark.django_db
def test_create_rejects_non_discord_webhook(roles, now, webhook):
    response = roles["organizer"].post(LIST_URL, event_body(now, discord_webhook=webhook), format="json")

    assert response.status_code == 201
    assert "discord_webhook" in response.data["fields"]


@pytest.mark.parametrize(
    "role, expected",
    [("anon", 401), ("other_user", 403), ("organizer", 200), ("admin", 200)],
)
@pytest.mark.django_db
def test_update_permissions(role, expected, roles, future_event):
    response = roles[role].patch(detail_url(future_event.id), {"title": "Renamed"}, format="json")

    assert response.status_code == expected
    future_event.refresh_from_db()
    assert future_event.title == ("Renamed" if expected == 200 else "MohylaCTF")


@pytest.mark.django_db
def test_update_only_end_before_existing_start(roles, future_event, now):
    old_end = future_event.end

    response = roles["organizer"].patch(
        detail_url(future_event.id),
        {"end": (now + timedelta(hours=1)).isoformat()},
        format="json",
    )

    assert response.status_code == 400
    assert "end" in response.data["fields"]
    future_event.refresh_from_db()
    assert future_event.end == old_end


@pytest.mark.django_db
def test_update_start_after_event_started(roles, started_event, now):
    old_start = started_event.start

    response = roles["organizer"].patch(
        detail_url(started_event.id),
        {"start": (now + timedelta(hours=2)).isoformat()},
        format="json",
    )

    assert response.status_code == 409
    started_event.refresh_from_db()
    assert started_event.start == old_start


@pytest.mark.django_db
def test_update_end_after_event_started(roles, started_event, now):
    new_end = now + timedelta(days=3)

    response = roles["organizer"].patch(detail_url(started_event.id), {"end": new_end.isoformat()}, format="json")

    assert response.status_code == 200
    started_event.refresh_from_db()
    assert started_event.end == new_end


@pytest.mark.django_db
def test_update_not_found(roles):
    response = roles["admin"].patch(detail_url(6767), {"title": "HACKEDYOUSITEmuhahaha"}, format="json")

    assert response.status_code == 404


@pytest.mark.django_db
def test_update_end_before_now(roles, started_event, now):
    new_end = now - timedelta(hours=1)
    response = roles["admin"].patch(detail_url(started_event), {"end": new_end})

    assert response.status_code == 200
    started_event.refresh_from_db()
    assert started_event.end == new_end


@pytest.mark.parametrize(
    "role, expected",
    [("anon", 401), ("other_user", 403), ("organizer", 204), ("admin", 204)],
)
@pytest.mark.django_db
def test_delete_permissions(role, expected, roles, future_event):
    response = roles[role].delete(detail_url(future_event.id))

    assert response.status_code == expected
    assert Event.objects.filter(id=future_event.id).exists() == (expected != 204)
