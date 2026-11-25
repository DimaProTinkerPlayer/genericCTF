import logging

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from .models import CTFEvent
from .permissions import IsOrganizerOrAdminOrReadOnly
from .serializers import EventSerializer

logger = logging.getLogger(__name__)


class EventList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]  # temporary

    def get(self, request):
        events = CTFEvent.objects.select_related("organizer")
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

    def get(self, request, pk):
        event = get_object_or_404(CTFEvent.objects.select_related("organizer"), id=pk)
        return Response(EventSerializer(event, context={"request": request}).data)

    def patch(self, request, pk):
        event = get_object_or_404(CTFEvent, id=pk)
        self.check_object_permissions(request, event)
        serializer = EventSerializer(
            event, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        event = get_object_or_404(CTFEvent, id=pk)
        self.check_object_permissions(request, event)
        logger.info("Event %s deleted by user %s", pk, request.user.id)
        event.delete()
        return Response(status=HTTP_204_NO_CONTENT)
