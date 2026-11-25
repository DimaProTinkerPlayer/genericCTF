from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventList.as_view(), name="event_list"),
    path("<int:pk>/", views.EventDetail.as_view(), name="individual_event")
]
