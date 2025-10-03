import uuid


def generate_code():
    """Для генерации короткой ссылки на рецепт."""
    return uuid.uuid4().hex[:6]
