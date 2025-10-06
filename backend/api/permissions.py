from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """
    Разрешения для автора объекта, админов и только чтения.

    Поведение:
        - Чтение (GET, HEAD, OPTIONS) доступно всем пользователям.
        - Создание и изменение доступны только авторам.
        - Изменять или удалять объект может его автор или админ.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        is_read_only = request.method in SAFE_METHODS
        author = getattr(obj, 'author', None)
        user = request.user

        return (
            (author is not None and author == user)
            or is_read_only or user.is_staff or user.is_superuser
        )
