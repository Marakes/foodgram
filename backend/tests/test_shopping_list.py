import pytest


@pytest.mark.django_db
def test_download_shopping_cart_returns_text(
        auth, user, user2, tags, ingredients
):
    # создадим рецепт и положим в корзину
    # (используем API из предыдущего теста)
    from .conftest import create_recipe
    r = create_recipe(
        author=user2,
        name="Смузи",
        ingredients=[(ingredients[0], 2)],
        tags=[tags[0]],
    )
    assert auth.post(
        f"/api/recipes/{r.id}/shopping_cart/"
    ).status_code in (200, 201)

    resp = auth.get("/api/recipes/download_shopping_cart/")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/plain")
    assert "Content-Disposition" in resp
    assert "Список покупок" in resp.content.decode("utf-8") or resp.content
