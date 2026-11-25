from django import forms
from django.contrib import admin

from .models import Category, Challenge


class ChallengeAdminForm(forms.ModelForm):
    raw_flag = forms.CharField(
        label="Флаг",
        required=False,
        help_text="Зберігається лише SHA-256 хеш. Залиште порожнім, щоб не змінювати.",
    )

    class Meta:
        model = Challenge
        fields = ["title", "description", "category", "difficulty", "points", "connection_info", "status", "author"]

    def clean(self):
        cleaned_data = super().clean()
        raw_flag = cleaned_data.get("raw_flag", "").strip()
        if not raw_flag and not self.instance.flag:
            self.add_error("raw_flag", "Для нової задачі флаг обов'язковий.")
        return cleaned_data

    def save(self, commit=True):
        raw_flag = self.cleaned_data.get("raw_flag", "").strip()
        if raw_flag:
            self.instance.set_flag(raw_flag)
        return super().save(commit=commit)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "id"]
    search_fields = ["name"]


class ChallengeAdmin(admin.ModelAdmin):
    form = ChallengeAdminForm
    list_display = ["title", "category", "difficulty", "points", "status", "author", "created_at"]
    list_filter = ["status", "difficulty", "category"]
    search_fields = ["title", "description"]
    list_select_related = ["category", "author"]
    readonly_fields = ["created_at"]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Challenge, ChallengeAdmin)
