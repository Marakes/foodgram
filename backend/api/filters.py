import django_filters
from django.db.models import Subquery
from rest_framework import filters

from recipes.models import Recipe, Tag, Favorite, ShoppingCart


class RecipeFilter(django_filters.FilterSet):
    """
    Набор фильтров для списка рецептов.

    Поддерживает:
    - author: числовой ID автора или специальное значение 'me';
    - tags: фильтрацию по slug-ам тегов (множественный выбор);
    - is_favorited: выбор рецептов из избранного пользователя;
    - is_in_shopping_cart: выбор рецептов из корзины пользователя.
    """

    author = django_filters.CharFilter(method='filter_author')
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_author(self, qs, name, value):
        """
        Фильтрация по автору.

        Поддерживает два формата:
        - 'me' — возвращает рецепты аутентифицированного пользователя;
        - числовой ID — возвращает рецепты указанного автора.

        Если пользователь не аутентифицирован и передано 'me',
        возвращает пустой queryset.
        При некорректном значении — тоже пустой queryset.
        """
        val = (str(value).strip().lower() if value is not None else '')
        if val == 'me':
            user = getattr(self.request, 'user', None)
            return (qs.filter(author=user)
                    if (user and user.is_authenticated)
                    else qs.none())
        try:
            return qs.filter(author__id=int(val))
        except (TypeError, ValueError):
            return qs.none()

    def _helper_fav_shop(self, qs, model_cls, value):
        """
        Вспомогательный метод для фильтров по избранному/корзине.

        Возвращает queryset, отфильтрованный по рецептам, связанным с
        пользователем через переданную модель связи.

        Параметры:
            qs (QuerySet): базовый список рецептов.
            model_cls (Model): модель связи (Favorite или ShoppingCart).
            value (Any): булево значение фильтра.
        """
        if value in (None, False, 0, '0'):
            return qs
        user = getattr(self.request, 'user', None)
        if not user or not user.is_authenticated:
            return qs.none()
        obj_ids = model_cls.objects.filter(user=user).values('recipe_id')
        return qs.filter(pk__in=Subquery(obj_ids))

    def filter_is_favorited(self, qs, name, value):
        """
        Фильтр «только избранные».

        При истинном value оставляет в выборке рецепты, добавленные
        в избранное текущим пользователем. Для анонима — пустая выборка.
        """
        return self._helper_fav_shop(qs, Favorite, value)

    def filter_is_in_cart(self, qs, name, value):
        """
        Фильтр «только в корзине».

        При истинном value оставляет в выборке рецепты, добавленные
        в корзину текущим пользователем. Для анонима — пустая выборка.
        """
        return self._helper_fav_shop(qs, ShoppingCart, value)

    # def filter_is_favorited(self, qs, name, value):
    #     if value in (None, False, 0, '0'):
    #         return qs
    #     user = getattr(self.request, 'user', None)
    #     if not user or not user.is_authenticated:
    #         return qs.none()
    #     fav_ids = Favorite.objects.filter(user=user).values('recipe_id')
    #     return qs.filter(pk__in=Subquery(fav_ids))
    #
    # def filter_is_in_cart(self, qs, name, value):
    #     if value in (None, False, 0, '0'):
    #         return qs
    #     user = getattr(self.request, 'user', None)
    #     if not user or not user.is_authenticated:
    #         return qs.none()
    #     cart_ids = ShoppingCart.objects.filter(user=user).values('recipe_id')
    #     return qs.filter(pk__in=Subquery(cart_ids))


class NameSearchFilter(filters.SearchFilter):
    """
    Фильтр поиска по имени.

    Переопределяет имя параметра запроса на `name`,
    чтобы поиск выполнялся по ?name=<строка>.
    """

    search_param = 'name'
