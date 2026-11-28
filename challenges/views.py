import logging

from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminOrReadOnly

from .models import Category
from .serializers import CategorySerializer

logger = logging.getLogger(__name__)


def category_in_use_response(challenges_count):
    return Response(
        {
            "error": f"Неможливо видалити категорію, у ній є задачі: {challenges_count}.",
            "fields": {},
            "challenges_count": challenges_count,
        },
        status=status.HTTP_409_CONFLICT,
    )


class CategoryList(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        serializer = CategorySerializer(Category.objects.all(), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        logger.info("Category %s created by user %s", category.id, request.user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryDetail(APIView):
    permission_classes = [IsAdminOrReadOnly]

    def get_category(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            raise NotFound("Категорію не знайдено.") from None

    def get(self, request, pk):
        return Response(CategorySerializer(self.get_category(pk)).data)

    def patch(self, request, pk):
        category = self.get_category(pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Category %s updated by user %s", pk, request.user.id)
        return Response(serializer.data)

    def delete(self, request, pk):
        category = self.get_category(pk)
        challenges_count = category.challenges.count()
        if challenges_count:
            return category_in_use_response(challenges_count)

        try:
            category.delete()
        except ProtectedError:
            # задачу могли додати між count() і delete()
            return category_in_use_response(category.challenges.count())

        logger.info("Category %s deleted by user %s", pk, request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
