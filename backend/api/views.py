import base64
from collections import defaultdict
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import (BooleanField, Exists, OuterRef, Prefetch,
                              Subquery, Value)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientUniversalSearchFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly, IsAuthorOrAdminOrReadOnly
from api.serializers import (AvatarUpdateSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeShortSerializer,
                             RecipeWriteSerializer, SubscribeSerializer,
                             TagSerializer, UserCreateSerializer)
from api.utils import generate_code
from recipes.models import (Favorite, Ingredient, Recipe, ShoppingCart,
                            ShortLink, Tag)
from users.models import Subscribe

User = get_user_model()


class ReadOnlyBase(viewsets.ReadOnlyModelViewSet):
    """
    Базовый read-only viewset для справочников (теги, ингредиенты).

    Разрешает только безопасные методы; права выдаются через
    :class:`IsAdminOrReadOnly`. Пагинация отключена.
    """

    # permission_classes = (IsAuthenticatedOrReadOnly, IsAdminOrReadOnly,)
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ReadOnlyBase):
    """
    Вьюсет ингредиентов.

    Выдаёт список и детали ингредиентов. Поиск — по началу названия
    (search_fields='^name') через кастомный :class:`NameSearchFilter`.
    """

    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (IngredientUniversalSearchFilter,)


class TagViewSet(ReadOnlyBase):
    """
    Вьюсет тегов.

    Позволяет получить список и детали тегов. Только чтение.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    # permission_classes = (IsAuthenticatedOrReadOnly,)


class CustomUserViewSet(UserViewSet):
    """
    Кастомный вьюсет пользователей на базе Djoser.

    Поддерживает:
      - получение профиля пользователя (retrieve),
      - эндпоинт текущего пользователя ``/users/me/``,
      - управление аватаром ``/users/me/avatar/``,
      - подписки: список ``/users/subscriptions/`` и
        POST/DELETE ``/users/{id}/subscribe/``.
    """

    queryset = User.objects.all().order_by('id')
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email']
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'avatar':
            return AvatarUpdateSerializer
        if self.action in ('subscriptions', 'subscribe', 'me', 'retrieve'):
            return SubscribeSerializer
        return super().get_serializer_class()

    def _helper_retrieve(self, request, user_obj):
        """
        Сериализует пользователя с префетчем его рецептов.
        """
        recipes_qs = Recipe.objects.filter(author=user_obj).order_by('-id')
        user_with_recipes = (
            User.objects.filter(pk=user_obj.pk)
            .prefetch_related(Prefetch('recipes', queryset=recipes_qs))
            .get()
        )
        serializer = self.get_serializer(
            user_with_recipes, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Вернуть профиль пользователя по ``pk`` c его рецептами.
        """
        user_obj = get_object_or_404(
            self.get_queryset(),
            pk=kwargs.get(self.lookup_field, kwargs.get('pk'))
        )
        return self._helper_retrieve(request, user_obj)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """
        Вернуть профиль текущего аутентифицированного пользователя.
        """
        user_obj = request.user
        return self._helper_retrieve(request, user_obj)

    @action(
        detail=False,
        methods=['get', 'put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def avatar(self, request, *args, **kwargs):
        """
        Получить/обновить/удалить аватар текущего пользователя.
        """
        user = request.user

        if request.method == 'GET':
            data = {
                'avatar': (
                    request.build_absolute_uri(user.avatar.url)
                    if user.avatar else None
                )
            }
            return Response(data, status=status.HTTP_200_OK)

        if request.method == 'PUT':
            data = request.data.get('avatar')
            if not data:
                return Response({'avatar': ['Это поле обязательное!']},
                                status=status.HTTP_400_BAD_REQUEST)

            try:
                if isinstance(data, str) and data.startswith('data:image'):
                    header, b64 = data.split(';base64,', 1)
                    ext = (header.split('/')[-1] or 'jpg').lower()
                else:
                    b64, ext = data, 'jpg'

                raw = base64.b64decode(b64, validate=True)
            except Exception:
                raise ValidationError({
                    'avatar': ['Не удалось обработать фото']
                })

            # сохраняем напрямую, минуя DRF ImageField validation
            filename = f'avatar_{user.pk}.{ext}'
            user.avatar.save(filename, ContentFile(raw), save=True)

            absolute_url = request.build_absolute_uri(user.avatar.url)
            return Response(
                {'avatar': absolute_url}, status=status.HTTP_200_OK
            )

        # if request.method == 'PUT':
        #     if 'avatar' not in request.data:
        #         return Response(
        #             {'avatar': ['Это поле обязательное!']},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )
        #     try:
        #         serializer = self.get_serializer(
        #             user,
        #             data=request.data,
        #             # partial=False
        #         )
        #         serializer.is_valid(raise_exception=True)
        #         serializer.save()
        #     except ValidationError:
        #         raise
        #     except OSError:
        #         raise ValidationError(
        #             {'avatar': ['Не удалось обработать фото']}
        #         )
        #     return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)

    def _recipes_limit(self, request):
        """
        Извлекает ?recipes_limit из query params и приводит к int/None.
        """
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 0:
                    recipes_limit = None
            except ValueError:
                recipes_limit = None
        return recipes_limit

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Список авторов, на которых подписан текущий пользователь.
        """
        # recipes_limit = self._recipes_limit(request)
        base_qs = User.objects.filter(
            subscribers__user=request.user
        ).distinct().order_by('id')
        recipes_qs = Recipe.objects.order_by('-id')
        # if recipes_limit is not None:
        #     recipes_qs = recipes_qs[:recipes_limit]
        qs = base_qs.prefetch_related(
            Prefetch('recipes', queryset=recipes_qs)
        )
        page = self.paginate_queryset(qs)
        context = {'request': request}
        if page is not None:
            serializer = self.get_serializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, *args, **kwargs):
        """
        Оформить или отменить подписку на автора.
        """
        user = request.user
        author = self.get_object()

        if request.method == 'POST' and user.pk == author.pk:
            return Response({'detail': 'На себя подписаться нельзя!!!'},
                            status=status.HTTP_400_BAD_REQUEST)

        exists = Subscribe.objects.filter(user=user, author=author).exists()
        if request.method == 'POST':
            if exists:
                return Response({'detail': 'Подписка уже оформлена!'},
                                status=status.HTTP_400_BAD_REQUEST)
            Subscribe.objects.create(user=user, author=author)
            recipes_limit = self._recipes_limit(request)
            recipes_qs = author.recipes.order_by('-id')
            if recipes_limit is not None:
                recipes_qs = recipes_qs[:recipes_limit]

            author_obj = (
                self.get_queryset().filter(pk=author.pk)
                .prefetch_related(Prefetch('recipes', queryset=recipes_qs))
                .get()
            )
            serializer = self.get_serializer(
                author_obj, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not exists:
            return Response({'detail': 'Вы не подписаны!'},
                            status=status.HTTP_400_BAD_REQUEST)
        Subscribe.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет рецептов (CRUD + действия).

    Поддерживает фильтрацию (django-filter), поиск и сортировку.
    """

    # queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer
    filter_backends = (
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    )
    filterset_class = RecipeFilter
    ordering_fields = ('id', 'name')
    ordering = ('-id',)
    search_fields = ('name',)

    def get_queryset(self):
        """
        Построить queryset рецептов с оптимизациями и аннотациями.

        - ``select_related('author')``,
        ``prefetch_related('tags', 'recipe_ingredients__ingredient')``;
        - фильтрация по избранному/корзину;
        - аннотации булевых флагов для текущего пользователя.

        Returns:
            QuerySet: оптимизированный и уникальный набор рецептов.
        """
        request = getattr(self, 'request', None)
        user = getattr(request, 'user', None)

        qs = (
            Recipe.objects.all()
            .select_related('author')
            .prefetch_related('tags', 'recipe_ingredients__ingredient')
        )

        if user and user.is_authenticated:
            fav_ids = Favorite.objects.filter(user=user).values('recipe_id')
            cart_ids = ShoppingCart.objects.filter(
                user=user).values('recipe_id')

            is_fav = request.query_params.get('is_favorited')
            if is_fav in ('1', 'true', 'True', True):
                qs = qs.filter(pk__in=Subquery(fav_ids))

            is_cart = request.query_params.get('is_in_shopping_cart')
            if is_cart in ('1', 'true', 'True', True):
                qs = qs.filter(pk__in=Subquery(cart_ids))

            qs = qs.annotate(
                _is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user, recipe_id=OuterRef('pk')
                    )
                ),
                _is_in_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe_id=OuterRef('pk')
                    )
                ),
            )
        else:
            qs = qs.annotate(
                _is_favorited=Value(False, output_field=BooleanField()),
                _is_in_cart=Value(False, output_field=BooleanField()),
            )

        return qs.distinct()

    def get_permissions(self):
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthorOrAdminOrReadOnly()]
        if self.action == 'create':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        if self.action in ('shopping_cart', 'favorite'):
            return RecipeShortSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'code': generate_code()}
        )
        url = request.build_absolute_uri(f'/s/{short_link.code}/')
        return Response({'short-link': url}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Скачать агрегированный список покупок текущего пользователя.

        Подсчитывает общие количества ингредиентов
        по всем рецептам в корзине и отдаёт текстовый файл.

        Returns:
            HttpResponse: файл с построчным списком
            «ингредиент (ед.) — количество».
        """
        user = request.user

        recipes_qs = (
            self.get_queryset().filter(in_carts__user=user)
            .prefetch_related('recipe_ingredients__ingredient')
        )
        totals = defaultdict(Decimal)

        for recipe in recipes_qs:
            for rec_ing in recipe.recipe_ingredients.all():
                key = (rec_ing.ingredient.name,
                       rec_ing.ingredient.measurement_unit)
                totals[key] += rec_ing.amount

        if not totals:
            content = 'Список покупок пуст, пора набирать!'
        else:
            lines = []
            for (name, unit), amount in sorted(
                    totals.items(), key=lambda x: x[0][0].lower()
            ):
                amount_str = (f'{amount.normalize()}'
                              if amount == amount.to_integral()
                              else f'{amount}')
                lines.append(f'{name} ({unit}) - {amount_str}')
            content = '\n'.join(lines)

        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8',
            status=status.HTTP_200_OK
        )
        response['Content-Disposition'] = ('attachment; '
                                           'filename="shopping_list.txt"')
        return response

    def _helper_shop_fav(self, request, model_cls, name):
        """
        Вспомогательный обработчик для избранного и корзины.

        В зависимости от метода запроса добавляет/удаляет запись
        в модели (Favorite/ShoppingCart) для текущего пользователя
        и текущего рецепта.

        Args:
            request: текущий запрос.
            model_cls: модель связи (Favorite или ShoppingCart).
            name (str): человекочитаемое имя сущности для сообщений.

        Returns:
            Response: 201 с кратким рецептом или 204 при удалении.
        """
        user = request.user
        recipe = self.get_object()

        exists = model_cls.objects.filter(
            user=user, recipe=recipe).exists()

        if request.method == 'POST':
            if exists:
                return Response({'detail': f'Рецепт уже в {name}!'},
                                status=status.HTTP_400_BAD_REQUEST)
            model_cls.objects.create(user=user, recipe=recipe)
            data = self.get_serializer(recipe).data
            return Response(data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if not exists:
                return Response({'detail': f'Рецепта нет в {name}!'},
                                status=status.HTTP_400_BAD_REQUEST)
            model_cls.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт в список покупок."""
        return self._helper_shop_fav(
            request, ShoppingCart, 'списке покупок'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт в избранное."""
        return self._helper_shop_fav(
            request, Favorite, 'избранном'
        )


def short_link_redirect(request, code):
    """
    Редирект по короткой ссылке ``/s/<code>/`` на страницу рецепта.
    """
    short_link = get_object_or_404(ShortLink, code=code)
    return redirect(f'/recipes/{short_link.recipe.id}')
