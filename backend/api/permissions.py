from rest_framework import permissions


class RecipePermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ('PATCH', 'DELETE'):
            return obj.author == request.user
        elif (
            request.method in ('PATCH', 'DELETE')
            and request.user.is_authenticated
        ):
            return request.user.is_admin
