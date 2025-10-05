import pytest

from .conftest import create_recipe

# from recipes.models import Favorite, ShoppingCart


@pytest.mark.django_db
def test_recipe_create_and_flags(auth, user, tags, ingredients, small_png_b64):
    payload = {
        "name": "Фриттата",
        "text": "Шаг 1, шаг 2",
        "cooking_time": 15,
        "tags": [tags[0].id, tags[1].id],
        "ingredients": [
            {"id": ingredients[0].id, "amount": "1.00"},
            {"id": ingredients[1].id, "amount": "2.00"},
        ],
        "image": small_png_b64,
    }
    resp = auth.post("/api/recipes/", data=payload, format="json")
    assert resp.status_code == 201, resp.content
    data = resp.json()
    assert data["name"] == "Фриттата"
    assert len(data["tags"]) == 2
    assert len(data["ingredients"]) == 2
    assert data["is_favorited"] is False
    assert data["is_in_shopping_cart"] is False


@pytest.mark.django_db
def test_favorite_and_cart_and_filters(auth, user, user2, tags, ingredients):
    # создадим чужой рецепт и добавим в избранное/корзину
    r = create_recipe(
        author=user2,
        name="Тост",
        ingredients=[(ingredients[0], 1)],
        tags=[tags[0]],
    )

    # избранное
    resp = auth.post(f"/api/recipes/{r.id}/favorite/")
    assert resp.status_code in (200, 201), resp.content

    # корзина
    resp = auth.post(f"/api/recipes/{r.id}/shopping_cart/")
    assert resp.status_code in (200, 201), resp.content

    # фильтры
    resp = auth.get("/api/recipes/?is_favorited=1")
    assert resp.status_code == 200
    ids = [x["id"] for x in resp.json()["results"]]
    assert r.id in ids

    resp = auth.get("/api/recipes/?is_in_shopping_cart=1")
    assert resp.status_code == 200
    ids = [x["id"] for x in resp.json()["results"]]
    assert r.id in ids

    # удаление
    assert auth.delete(
        f"/api/recipes/{r.id}/favorite/"
    ).status_code == 204
    assert auth.delete(
        f"/api/recipes/{r.id}/shopping_cart/"
    ).status_code == 204
