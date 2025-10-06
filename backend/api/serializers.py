import base64
from binascii import Error as B64Error
from collections import Counter

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from recipes.constants import MAX_COUNT, MIN_COUNT
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

User = get_user_model()


class ImageBase64(serializers.FileField):
    """
    Поле для приёма изображений в Base64 без проверки PIL на уровне DRF.

    Поддерживает:
      - 'data:image/<ext>;base64,<payload>'
      - «голые» base64-данные
    Нормализует переносы/пробелы и дополняет паддинг.
    """

    def to_internal_value(self, data):
        if isinstance(data, str):
            b64data = data
            ext = 'jpg'

            if data.startswith('data:image'):
                # парсим заголовок и полезную часть
                try:
                    header, b64data = data.split('base64,', 1)
                except ValueError:
                    raise serializers.ValidationError(
                        'Не удалось обработать фото'
                    )
                # пытаемся вытащить расширение из mime
                try:
                    mime = header.split(':', 1)[1].split(';', 1)[0]
                    ext = (mime.split('/', 1)[1] or 'jpg').lower()
                except Exception:
                    ext = 'jpg'

            # убрать пробелы/переносы + допаддить до кратности 4
            b64data = ''.join(b64data.split())
            missing_padding = (-len(b64data)) % 4
            if missing_padding:
                b64data += '=' * missing_padding

            try:
                decoded = base64.b64decode(b64data)  # validate=False
            except (B64Error, ValueError):
                raise serializers.ValidationError('Не удалось обработать фото')

            # Возвращаем файл без доп. проверки PIL/DRF
            return ContentFile(decoded, name=f'upload.{ext}')

        # на случай если пришёл уже файл
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов (список/детали)."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения тегов (список/детали)."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиента внутри рецепта (режим чтения).

    Отдаёт id, name и measurement_unit из связанного Ingredient,
    плюс количество (amount).
    """

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeIngredientWriteSerializer(serializers.Serializer):
    """
    Сериализатор ингредиента внутри рецепта (режим записи).

    Принимает:
        - id: PK ингредиента (поле 'ingredient')
        - amount: Int от 1 до 32000
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=MIN_COUNT,
        max_value=MAX_COUNT
    )


class AuthorSerializer(serializers.ModelSerializer):
    """
    Краткие данные об авторе рецепта.

    Включает признак подписки текущего пользователя и аватар.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        """Возвращает True, если пользователь подписан на автора."""
        user = getattr(self.context.get('request'), 'user', None)
        if not user or not user.is_authenticated:
            return False
        return obj.subscribers.filter(user=user).exists()


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор рецепта для чтения.

    Включает теги, автора, ингредиенты и вычисляемые флаги:
    is_favorited и is_in_shopping_cart.
    """

    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = fields

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов с единицами измерения."""
        queryset = obj.recipe_ingredients.select_related('ingredient')
        return RecipeIngredientReadSerializer(queryset, many=True).data

    def _helper_flag(self, obj, annotated_attr, qs_model):
        """Хелпер: безопасно получить булев флаг.

        Если в queryset есть аннотация (annotated_attr) — используем её.
        Иначе делаем точечный exists() по связанному queryset.
        """
        annotated = getattr(obj, annotated_attr, None)
        if annotated is not None:
            return bool(annotated)
        user = getattr(self.context.get('request'), 'user', None)
        if not user or not user.is_authenticated:
            return False
        return qs_model.filter(user=user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        """True, если рецепт в избранном у текущего пользователя."""
        return self._helper_flag(obj, '_is_favorited', Favorite.objects)

    def get_is_in_shopping_cart(self, obj):
        """True, если рецепт в списке покупок у пользователя."""
        return self._helper_flag(obj, '_is_in_cart', ShoppingCart.objects)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания/редактирования рецепта.

    Принимает теги (PK), список ингредиентов, изображение (base64),
    название, текст и время приготовления.
    """

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)
    image = ImageBase64(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COUNT,
        max_value=MAX_COUNT
    )

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')

    def validate(self, attrs):
        """
        Проверяет уникальность тегов и ингредиентов и непустые списки.

        Исключения:
            serializers.ValidationError: при пустых списках, дубликатах
            или иных нарушениях формата.
        """
        tag_ids = [tag.id if isinstance(tag, Tag)
                   else tag for tag in attrs.get('tags', [])]
        if not tag_ids:
            raise serializers.ValidationError(
                {'tags': 'Нужно указать хотя бы один тег.'}
            )
        dup_tags = [tag for tag, count in Counter(tag_ids).items()
                    if count > 1]
        if dup_tags:
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        ingredients = attrs.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Список ингредиентов не может быть пустым.'}
            )
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        dup_ingredients = [i for i, count in Counter(ingredient_ids).items()
                           if count > 1]
        if dup_ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        return attrs

    @transaction.atomic
    def _set_ingredients(self, recipe, ingredients_payload):
        """Полностью пересобирает состав ингредиентов рецепта."""
        recipe.recipe_ingredients.all().delete()
        bulk = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients_payload
        ]
        RecipeIngredient.objects.bulk_create(bulk)

    @transaction.atomic
    def create(self, validated_data):
        """
        Создаёт рецепт от имени пользователя.

        Возвращает:
            Recipe: созданный объект.
        """
        tags = validated_data.pop('tags')
        ingredients_payload = validated_data.pop('ingredients')

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({
                'detail': 'Нужно авторизироваться'}
            )
        author = request.user

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients_payload)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет поля рецепта, теги и состав ингредиентов."""
        tags = validated_data.pop('tags', None)
        ingredients_payload = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        if ingredients_payload is not None:
            self._set_ingredients(instance, ingredients_payload)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта (для избранного/корзины)."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Публичный профиль пользователя в контексте подписок.

    Включает: признак «подписан ли я на автора», список его рецептов
    (опционально урезается параметром ?recipes_limit), и общее их число.
    """

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
        read_only_fields = ('id', 'recipes', 'avatar')

    def get_is_subscribed(self, obj):
        """True, если пользователь подписан на данного пользователя."""
        user = getattr(self.context.get('request'), 'user', None)
        if not user or not user.is_authenticated:
            return False
        return user.subscriptions.filter(author=obj).exists()

    def get_recipes(self, obj):
        """
        Возвращает список последних рецептов автора.

        Учитывает query-параметр recipes_limit (если передан корректно).
        """
        request = self.context.get('request', None)
        recipes_limit = None
        if request:
            rl = request.query_params.get('recipes_limit')
            try:
                recipes_limit = int(rl) if rl is not None else None
                if recipes_limit is not None and recipes_limit < 0:
                    recipes_limit = None
            except (ValueError, TypeError):
                recipes_limit = None
        qs = obj.recipes.order_by('-id')
        if recipes_limit is not None:
            qs = qs[:recipes_limit]
        return RecipeShortSerializer(qs, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов у пользователя."""
        return obj.recipes.count()


class UserReadSerializer(serializers.ModelSerializer):
    """
    Публичные данные пользователя.

    Включает признак подписки (кроме случая просмотра себя) и аватар.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        """True, если текущий пользователь подписан (не на себя)."""
        user = getattr(self.context.get('request'), 'user', None)
        if not user or not user.is_authenticated or user == obj:
            return False
        return obj.subscribers.filter(user=user).exists()

    def get_avatar(self, obj):
        """Вернёт URL аватара или пустую строку, если аватара нет."""
        if obj.avatar:
            return obj.avatar.url
        return ''


class UserCreateSerializer(serializers.ModelSerializer):
    """Создание пользователя с хешированием пароля."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def create(self, validated_data):
        """Создаёт пользователя и устанавливает ему хэш пароль."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Обновление аватара пользователя (base64 → ImageField)."""

    avatar = ImageBase64(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def to_representation(self, instance):
        """Возвращает абсолютный URL аватара."""
        return {'avatar': self.context['request'].build_absolute_uri(
            instance.avatar.url) if instance.avatar else None}
