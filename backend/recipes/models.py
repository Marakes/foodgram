from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import Truncator

from recipes.constants import MAX_COUNT, MIN_COUNT, TRUNCATE_TEXT

User = get_user_model()


class Tag(models.Model):
    """
    Модель для тегов рецептов.

    Хранит название и уникальный slug тега.
    Используется для категоризации и фильтрации рецептов.
    """

    name = models.CharField(
        'Тэг', unique=True, max_length=64
    )
    slug = models.SlugField('Слаг', unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return Truncator(self.name).chars(TRUNCATE_TEXT)


class Ingredient(models.Model):
    """
    Модель для ингредиентов.

    Содержит название и единицу измерения.
    Гарантирует уникальность комбинации «название + единица измерения».
    """

    name = models.CharField('Ингредиент', max_length=128)  # unique=True,
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='uniq_ingredient_name_unit'
            )
        ]
        ordering = ('name',)

    def __str__(self):
        return Truncator(self.name).chars(TRUNCATE_TEXT)


class Recipe(models.Model):
    """
    Модель для рецептов.

    Хранит информацию о рецепте: название, автора, описание,
    изображение, ингредиенты (через промежуточную модель),
    теги и время приготовления.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    name = models.CharField('Рецепт', max_length=256)
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
        null=True,
        blank=True,
    )
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        validators=[
            MinValueValidator(MIN_COUNT),
            MaxValueValidator(MAX_COUNT)
        ]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-id',)

    def __str__(self):
        return (f'Рецепт: {Truncator(self.name).chars(TRUNCATE_TEXT)}. '
                f'Автор: {self.author}.')


class RecipeIngredient(models.Model):
    """
    Промежуточная модель «рецепт ↔ ингредиент».

    Сохраняет связь рецепта и ингредиента с указанием количества.
    Гарантирует уникальность пары «рецепт + ингредиент».
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(MIN_COUNT),
            MaxValueValidator(MAX_COUNT)
        ]
    )

    class Meta:
        ordering = ('ingredient__name',)
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.ingredient} – {self.amount}'


class Favorite(models.Model):
    """
    Модель для избранных рецептов пользователя.

    Позволяет хранить рецепты, которые пользователь добавил в избранное.
    Уникальность обеспечивается парой «пользователь + рецепт».
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorite_by',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class ShoppingCart(models.Model):
    """
    Модель для корзины покупок пользователя.

    Хранит рецепты, которые пользователь добавил в список покупок.
    Гарантируется уникальность комбинации «пользователь + рецепт».
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='cart_items',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='in_carts',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.recipe}'


class ShortLink(models.Model):
    """
    Модель для коротких ссылок на рецепты.

    Сохраняет уникальный код и связанную с ним ссылку на рецепт.
    Используется для генерации сокращённых URL.
    """

    code = models.CharField(
        'Код короткой ссылки',
        unique=True,
        db_index=True,
        max_length=10,
    )
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='short_link',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.code} -> {self.recipe}'
