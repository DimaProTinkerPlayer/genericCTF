import logging

from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Реєстрацію відхилено, поля з помилками: %s", list(serializer.errors))
            raise ValidationError(serializer.errors)

        user = serializer.save()
        logger.info("Зареєстровано нового користувача id=%s", user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
