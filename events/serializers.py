from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .exceptions import Conflict
from .models import CTFEvent

DISCORD_WEBHOOK_PREFIX = "https://discord.com/api/webhooks/"


class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username"]


class EventSerializer(serializers.ModelSerializer):
    organizer = OrganizerSerializer(read_only=True)

    class Meta:
        model = CTFEvent
        fields = [
            "id",
            "title",
            "description",
            "start",
            "end",
            "organizer",
            "discord_webhook",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_discord_webhook(self, value: str):
        if value and not value.startswith(DISCORD_WEBHOOK_PREFIX):
            raise serializers.ValidationError("Невалідна адреса діскорд вебхуку")
        return value

    def validate(self, attrs):
        start = attrs.get("start", self.instance.start if self.instance else None)
        end = attrs.get("end", self.instance.end if self.instance else None)

        if (
            self.instance is not None
            and "start" in attrs
            and attrs["start"] != self.instance.start
            and self.instance.start <= timezone.now()
        ):
            raise Conflict(
                "Час початку неможливо змінити, тому що змагання вже розпочалося."
            )

        if start >= end:
            raise serializers.ValidationError(
                {"end": "Неможливі значення початку та закінчення змагання."}
            )

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request is None or request.user != instance.organizer:
            data.pop("discord_webhook")
        return data
