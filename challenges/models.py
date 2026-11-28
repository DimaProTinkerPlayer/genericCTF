import hashlib
import hmac

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Lower


def hash_flag(raw_flag):
    """SHA-256 від флагу. Пробіли по краях прибираємо, регістр не чіпаємо."""
    return hashlib.sha256(raw_flag.strip().encode()).hexdigest()


class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "категорія"
        verbose_name_plural = "категорії"
        constraints = [
            models.UniqueConstraint(Lower("name"), name="category_name_ci_unique"),
        ]

    def __str__(self):
        return self.name


class Challenge(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Легка"
        MEDIUM = "medium", "Середня"
        HARD = "hard", "Складна"

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        REVIEW = "review", "На модерації"
        ACTIVE = "active", "Опублікована"
        REJECTED = "rejected", "Відхилена"

    title = models.CharField(max_length=128)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="challenges")
    difficulty = models.CharField(max_length=16, choices=Difficulty, default=Difficulty.EASY)
    points = models.PositiveIntegerField(default=500, validators=[MinValueValidator(1)])
    flag = models.CharField(max_length=64, editable=False)
    connection_info = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status, default=Status.DRAFT)
    is_private = models.BooleanField(
        default=False,
        help_text="Приватна задача видима лише учасникам CTF під час змагання.",
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="challenges")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "задача"
        verbose_name_plural = "задачі"
        indexes = [
            models.Index(fields=["status", "category"], name="challenge_status_category_idx"),
            models.Index(fields=["difficulty"], name="challenge_difficulty_idx"),
            models.Index(fields=["created_at"], name="challenge_created_at_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(points__gte=1), name="challenge_points_positive"),
            models.CheckConstraint(condition=~models.Q(flag=""), name="challenge_flag_not_empty"),
        ]

    def __str__(self):
        return self.title

    def set_flag(self, raw_flag):
        if not raw_flag or not raw_flag.strip():
            raise ValueError("Флаг не може бути порожнім.")
        self.flag = hash_flag(raw_flag)

    def check_flag(self, raw_flag):
        return hmac.compare_digest(self.flag, hash_flag(raw_flag))
