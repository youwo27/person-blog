"""Custom DRF permission classes.

Permission hierarchy: ADMIN > EDITOR > AUTHOR > USER (authenticated) > Any (anonymous).
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminUser(BasePermission):
    """Allow access only to users with ADMIN role."""

    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == "ADMIN"
        )


class IsEditorOrAdmin(BasePermission):
    """Allow access to users with EDITOR or ADMIN role."""

    message = "Only editors and administrators can perform this action."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        return role in ("ADMIN", "EDITOR")


class IsAuthorOrReadOnly(BasePermission):
    """
    Read-only for all users; write access only for the object's author.

    Expects the model instance to have an `author` field.
    """

    message = "Only the author can modify this resource."

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author
        return getattr(obj, "author", None) == request.user


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: owner or admin can access.

    Expects the model instance to have either a `user` or `owner` field.
    """

    message = "Only the resource owner or an administrator can perform this action."

    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False

        # Admin can do anything
        if getattr(request.user, "role", None) == "ADMIN":
            return True

        # Check ownership via common field names
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user


class CanManageComments(BasePermission):
    """Permission to moderate comments — editors and admins."""

    message = "Only editors and administrators can manage comments."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        role = getattr(request.user, "role", None)
        return role in ("ADMIN", "EDITOR")
