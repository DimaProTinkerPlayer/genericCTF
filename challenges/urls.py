from django.urls import path

from . import views

app_name = "challenges"

urlpatterns = [
    path("categories/", views.CategoryList.as_view(), name="category_list"),
    path("categories/<int:pk>/", views.CategoryDetail.as_view(), name="category_detail"),
]
