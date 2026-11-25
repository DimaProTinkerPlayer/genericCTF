from django.conf import settings
from django.db import models


class Event(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    start = models.DateTimeField()
    end = models.DateTimeField()
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organized_events",
    )
    discord_webhook = models.URLField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start__lt=models.F("end")),
                name="event_start_before_end",
            )
        ]

    def __str__(self):
        return self.title
