from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=64,
        validators=[
            UniqueValidator(
                queryset=Category.objects.all(),
                lookup="iexact",
                message="Категорія з такою назвою вже існує.",
            )
        ],
    )

    class Meta:
        model = Category
        fields = ["id", "name"]
