import pytest

from .conftest import create_recipe


@pytest.mark.django_db
def test_download_shopping_cart_returns_text(
        auth, user, user2, tags, ingredients
):
    r = create_recipe(
        author=user2,
        name="Смузи",
        ingredients=[(ingredients[0], 2)],
        tags=[tags[0]],
    )
    add_resp = auth.post(f"/api/recipes/{r.id}/shopping_cart/")
    assert add_resp.status_code in (200, 201), add_resp.content

    # качаем список покупок
    resp = auth.get("/api/recipes/download_shopping_cart/")
    assert resp.status_code == 200

    # заголовки
    ct = resp.headers.get("Content-Type", "")
    cd = resp.headers.get("Content-Disposition", "")
    assert ct.startswith("text/plain")
    assert "charset=utf-8" in ct
    assert "attachment;" in cd and "shopping_list.txt" in cd

    # содержимое
    body = resp.content.decode("utf-8")
    # формат без экспоненты
    assert "E+" not in body and "e+" not in body
    # ожидаем конкретную строку по нашему ингредиенту
    # ingredients[0] из фикстуры = ("Яблоко", "шт")
    assert "Яблоко (шт) - 2" in body
