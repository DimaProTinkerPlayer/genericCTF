from django.contrib import admin
from .models import CTFEvent


class CTFEventAdmin(admin.ModelAdmin):
    list_display = ["title", "start", "end", "organizer"]


admin.site.register(CTFEvent, CTFEventAdmin)
