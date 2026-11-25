import logging

from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from .models import Event
from .permissions import IsOrganizerOrAdminOrReadOnly
from .serializers import EventSerializer

logger = logging.getLogger(__name__)


class EventList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]  # temporary

    def get(self, request):
        events = Event.objects.select_related("organizer")
        serializer = EventSerializer(events, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = EventSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        event = serializer.save(organizer=request.user)
        logger.info("Event %s created by user %s", event.id, request.user.id)
        return Response(serializer.data, status=HTTP_201_CREATED)


class EventDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOrganizerOrAdminOrReadOnly]

    def get_event(self, pk):
        try:
            event = Event.objects.select_related("organizer").get(pk=pk)
        except Event.DoesNotExist:
            raise NotFound("Змагання не знайдено.") from None

        self.check_object_permissions(self.request, event)
        return event

    def get(self, request, pk):
        event = self.get_event(pk)
        return Response(EventSerializer(event, context={"request": request}).data)

    def patch(self, request, pk):
        event = self.get_event(pk)

        serializer = EventSerializer(event, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Event %s updated by user %s", pk, request.user.id)
        return Response(serializer.data)

    def delete(self, request, pk):
        event = self.get_event(pk)

        logger.info("Event %s deleted by user %s", pk, request.user.id)
        event.delete()
        return Response(status=HTTP_204_NO_CONTENT)
