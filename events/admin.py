from django.contrib import admin

from .models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "start", "end", "organizer"]


admin.site.register(Event, EventAdmin)
