from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    The request is authenticated as an admin - read/write,
    if as a user(even unauthenticated ones) - read-only request.
    """

    def has_permission(self, request, view):
        return bool(
            (request.method in SAFE_METHODS and request.user)
            or (request.user and request.user.is_staff)
        )
