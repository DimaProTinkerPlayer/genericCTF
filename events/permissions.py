from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsOrganizerOrAdminOrReadOnly(permissions.BasePermission):
    message = "Змінювати може лише організатор змагання або адміністратор."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.organizer == request.user or request.user.is_staff
