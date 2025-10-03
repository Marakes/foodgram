import pytest

from recipes.models import Ingredient


@pytest.mark.django_db
def test_ingredients_search_prefix_returns_all_matching(api):
    """
    Поиск по префиксу (?name=мо) должен вернуть все названия,
    начинающиеся с 'мо' (регистронезависимо).
    """
    Ingredient.objects.create(name="Молоко", measurement_unit="л")
    Ingredient.objects.create(name="Молотый перец", measurement_unit="г")
    Ingredient.objects.create(name="Соль", measurement_unit="г")

    resp = api.get("/api/ingredients/?name=мо")
    assert resp.status_code == 200

    names = [i["name"] for i in resp.json()]
    assert "Молоко" in names
    assert "Молотый перец" in names
    assert "Соль" not in names


@pytest.mark.django_db
def test_ingredients_search_prefix_narrowing(api):
    """
    Уточнение префикса (?name=молок) должно сузить список до 'Молоко'.
    """
    Ingredient.objects.create(name="Молоко", measurement_unit="л")
    Ingredient.objects.create(name="Молотый перец", measurement_unit="г")

    resp = api.get("/api/ingredients/?name=молок")
    assert resp.status_code == 200

    payload = resp.json()
    assert len(payload) == 1
    assert payload[0]["name"] == "Молоко"
