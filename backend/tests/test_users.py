import pytest
from django.contrib.auth import get_user_model

from .conftest import create_recipe

# from recipes.models import Subscribe

User = get_user_model()


@pytest.mark.django_db
def test_users_me_returns_recipes(auth, user, user2, tags, ingredients):
    # у user2 есть рецепты; проверим, что у user (me) — пусто
    # создадим рецепты для user (me), чтобы они появились в /users/me/
    r1 = create_recipe(
        author=user,
        name="Омлет",
        ingredients=[(ingredients[1], 2)],
        tags=[tags[0]],
    )
    r2 = create_recipe(
        author=user,
        name="Запеченное яблоко",
        ingredients=[(ingredients[0], 1)],
        tags=[tags[1]],
    )

    resp = auth.get("/api/users/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user.id
    assert data["recipes_count"] == 2
    got_ids = [r["id"] for r in data["recipes"]]
    assert set(got_ids) == {r1.id, r2.id}


@pytest.mark.django_db
def test_users_retrieve_anonymous_can_view_profile(api, user2, tags, ingredients):
    # у user2 есть рецепт; аноним может смотреть профиль с рецептами
    r = create_recipe(
        author=user2,
        name="Яблочный смузи",
        ingredients=[(ingredients[0], 2)],
        tags=tags,
    )
    resp = api.get(f"/api/users/{user2.id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == user2.id
    assert data["recipes_count"] == 1
    assert data["recipes"][0]["id"] == r.id


@pytest.mark.django_db
def test_subscribe_flow(auth, user, user2, tags, ingredients):
    # подписка
    resp = auth.post(f"/api/users/{user2.id}/subscribe/")
    assert resp.status_code in (200, 201, 400)  # может быть 400 если уже подписан
    # список подписок
    resp = auth.get("/api/users/subscriptions/")
    assert resp.status_code == 200
    results = resp.json()["results"]
    ids = [u["id"] for u in results]
    assert user2.id in ids
    # отписка
    resp = auth.delete(f"/api/users/{user2.id}/subscribe/")
    assert resp.status_code == 204
