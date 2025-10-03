# import base64
# import io
# import json
# from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
# from django.core.files.base import ContentFile
# from django.urls import reverse
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


User = get_user_model()


@pytest.fixture
def api():
    """Анонимный API-клиент."""
    return APIClient()


@pytest.fixture
def user(db):
    """Обычный пользователь."""
    return User.objects.create_user(
        email="user@example.com",
        username="user",
        first_name="User",
        last_name="One",
        password="pass1234",
    )


@pytest.fixture
def user2(db):
    """Второй пользователь (для авторов/подписок)."""
    return User.objects.create_user(
        email="author@example.com",
        username="author",
        first_name="Auth",
        last_name="Or",
        password="pass1234",
    )


@pytest.fixture
def auth(api, user):
    """Авторизованный клиент под `user`."""
    # берём токен через djoser
    resp = api.post(
        "/api/auth/token/login/",
        data={"email": user.email, "password": "pass1234"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    token = resp.data["auth_token"]
    api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    return api


@pytest.fixture
def auth2(api, user2):
    """Авторизованный клиент под `user2` (автор)."""
    resp = api.post(
        "/api/auth/token/login/",
        data={"email": user2.email, "password": "pass1234"},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    token = resp.data["auth_token"]
    api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    return api


@pytest.fixture
def small_png_b64():
    """Крошечный валидный PNG 1x1 base64 (data URL)."""
    return (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
        "AAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
    )


@pytest.fixture
def tags(db):
    """Два тега."""
    t1 = Tag.objects.create(name="Завтрак", slug="breakfast")
    t2 = Tag.objects.create(name="Ужин", slug="dinner")
    return [t1, t2]


@pytest.fixture
def ingredients(db):
    """Пара ингредиентов."""
    i1 = Ingredient.objects.create(name="Яблоко", measurement_unit="шт")
    i2 = Ingredient.objects.create(name="Яйцо", measurement_unit="шт")
    return [i1, i2]


def create_recipe(*, author, name, ingredients, tags, image=None, text="txt", time=5):
    """Хелпер для быстрого создания рецепта."""
    r = Recipe.objects.create(
        author=author,
        name=name,
        text=text,
        cooking_time=time,
        image=None,  # изображение в тестах API проверим через сериализатор
    )
    r.tags.set(tags)
    for ing, amount in ingredients:
        RecipeIngredient.objects.create(recipe=r, ingredient=ing, amount=amount)
    return r
