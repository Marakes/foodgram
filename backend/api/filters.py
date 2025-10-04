import operator
import re
import django_filters
from django.db.models import Case, IntegerField, Q, Subquery, Sum, Value, When
from functools import reduce
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


class IngredientUniversalSearchFilter(filters.SearchFilter):
    """
    Поиск по ?name=... с поддержкой нескольких термов и ранжированием.

    Приоритет на каждый терм:
      +3  name ISTARTSWITH term
      +2  term начинается с границы слова (любой позиции в name)
      +1  name ICONTAINS term

    Итоговый ранг = сумма баллов по всем термам.
    Фильтрация — AND по всем термам (каждый терм должен встретиться).
    Сортировка — по рангу (убывание), затем по name.
    """

    search_param = "name"

    # делаем собственный парсинг термов — игнорируем дефисы/подчёркивания и т.п.
    def get_search_terms(self, request):
        raw = request.query_params.get(self.search_param, "") or ""
        cleaned = re.sub(r"[-_.,;:/\\|]+", " ", raw, flags=re.U)
        return [t for t in cleaned.split() if t]

    def filter_queryset(self, request, queryset, view):
        terms = self.get_search_terms(request)
        if not terms:
            return queryset

        # 1) базовая фильтрация: все термы обязаны встретиться (AND)
        base_q = Q()
        for t in terms:
            base_q &= Q(name__icontains=t)
        queryset = queryset.filter(base_q)

        # 2) ранжирование: startswith > word-boundary > contains
        # границы слов: начало строки или типовые разделители/пробел
        boundary = r"(?:^|[\s\-,._/])"

        score_exprs = []
        for t in terms:
            esc = re.escape(t)
            score_exprs.append(
                Case(
                    When(name__istartswith=t, then=Value(3)),
                    When(name__iregex=fr"{boundary}{esc}", then=Value(2)),
                    When(name__icontains=t, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )

        # аккуратно складываем выражения (+ поддерживает сложение Case-выражений)
        total_score = reduce(operator.add, score_exprs)

        return (
            queryset
            .annotate(_rank=total_score)
            .order_by("-_rank", "name")
        )


# class NameSearchFilter(filters.SearchFilter):
#     """
#     Поиск ингредиентов по нескольким терминам + ранжирование:
#
#     - name ISTARTSWITH term  → +3 балла
#     - name REGEX (?<=^|разделитель)term → +2
#     - name ICONTAINS term    → +1
#
#     Итоговый _rank = сумма по всем термам.
#     Сортировка: по _rank убыв., затем по name.
#     """
#
#     search_param = 'name'
#
#     def get_search_fields(self, view, request):
#         # Ищем только по полю name, без '^' — будет icontains.
#         return ('name',)
#
#     def get_search_terms(self, request):
#         raw = request.query_params.get(self.search_param, '') or ''
#         # Разделяем по пробелам и типичным разделителям, чтобы
#         # запрос вида "сыр-тв" == "сыр тв"
#         cleaned = re.sub(r'[-_.,;:/\\|]+', ' ', raw, flags=re.U)
#         return [t for t in cleaned.split() if t]
#
#     def filter_queryset(self, request, queryset, view):
#         terms = self.get_search_terms(request)
#         if not terms:
#             return queryset
#
#         # AND-фильтрация: все термы должны встретиться
#         for t in terms:
#             queryset = queryset.filter(name__icontains=t)
#
#         # Ранжирование: startswith > word-boundary > contains
#         # Разделители слов для «границы слова»
#         boundary = r'(^|[\s\-,._/])'
#
#         score_exprs = []
#         for t in terms:
#             # Для регекспа экранируем терм
#             t_esc = re.escape(t)
#
#             score_exprs.append(
#                 Case(
#                     When(name__istartswith=t, then=Value(3)),
#                     When(name__iregex=fr'{boundary}{t_esc}', then=Value(2)),
#                     When(name__icontains=t, then=Value(1)),
#                     default=Value(0),
#                     output_field=IntegerField(),
#                 )
#             )
#
#         # Суммируем баллы по всем термам → _rank
#         queryset = queryset.annotate(
#             _rank=Sum(*score_exprs)
#         ).order_by('-_rank', 'name')
#
#         return queryset
#
#
# class IngredientSmartSearchFilter(filters.SearchFilter):
#     """
#     Поиск ингредиентов по ?name=...:
#     - первый терм — по началу слова (istartswith)
#     - последующие — вхождение где угодно (icontains)
#     - результаты с начальным совпадением идут выше.
#     """
#     search_param = "name"
#
#     def filter_queryset(self, request, queryset, view):
#         terms = [t for t in self.get_search_terms(request) if t]
#         if not terms:
#             return queryset
#
#         # где встречается первый терм — начало/не начало
#         first = terms[0]
#         rank = Case(
#             When(name__istartswith=first, then=Value(0)),
#             default=Value(1),
#             output_field=IntegerField(),
#         )
#
#         # первый терм: только начало
#         q = Q(name__istartswith=first)
#         # остальные термы: просто вхождения
#         for t in terms[1:]:
#             q &= Q(name__icontains=t)
#
#         return (queryset
#                 .filter(q)
#                 .annotate(_rank=rank)
#                 .order_by("_rank", "name"))
