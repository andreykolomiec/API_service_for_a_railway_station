from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminAllORIsAuthenticatedReadOnly(BasePermission):
    """
    Permissions:
    - Administrators - full access
    - Authenticated users - only SAFE_METHODS (GET, HEAD, OPTIONS)
    - Anonymous - no access
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        if (
            request.method in SAFE_METHODS
            and request.user
            and request.user.is_authenticated
        ):
            return True
        return False
