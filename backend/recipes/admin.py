from django.contrib import admin
from django.db.models import Count

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, ShortLink, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """
    Инлайн-редактор ингредиентов рецепта.

    Позволяет добавлять и редактировать связи «рецепт ↔ ингредиент»
    прямо на странице рецепта. Включает автодополнение по ингредиентам,
    требует как минимум одну позицию.
    """

    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ('ingredient',)
    min_num = 1


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для связей «избранное».

    Отображает, кто какой рецепт добавил. Поддерживает фильтры,
    поиск по пользователю и названию рецепта и автодополнение полей.
    """

    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для ингредиентов.

    Показывает название и единицу измерения,
    поддерживает поиск по названию и фильтрацию по единице измерения.
    """

    list_display = ('id', 'name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для рецептов.

    В списке отображает автора, теги, ингредиенты, время приготовления,
    короткое описание и количество добавлений в избранное. Поддерживает
    поиск по автору/названию/ингредиентам/тегам и редактирование состава
    через инлайн RecipeIngredientInline.
    """

    list_display = (
        'id', 'name', 'author',
        'get_ingredients', 'get_tags',
        'cooking_time', 'favorites_count', 'text_short',
    )
    search_fields = (
        'name', 'author__username',
        'author__first_name', 'author__last_name',
        'ingredients__name', 'tags__name',
    )
    list_filter = ('author', 'tags')
    inlines = (RecipeIngredientInline,)
    autocomplete_fields = ('ingredients', 'tags')
    readonly_fields = ('favorites_count',)
    empty_value_display = '-пусто-'

    def get_queryset(self, request):
        """
        Оптимизирует выборку рецептов для списка в админке.

        Добавляет select_related к автору, prefetch_related
        к ингредиентам и тегам, а также аннотирует `_favorites_count`
        — количество добавлений рецепта в избранное (distinct).
        """
        qs = super().get_queryset(request)
        return (
            qs.select_related('author')
              .prefetch_related('ingredients', 'tags')
              .annotate(_favorites_count=Count('favorite_by', distinct=True))
        )

    def favorites_count(self, obj):
        """
        Возвращает число добавлений рецепта в избранное (из аннотации).
        """
        return obj._favorites_count
    favorites_count.short_description = 'В избранном'

    def get_tags(self, obj):
        """
        Возвращает строку со списком тегов, разделённых запятыми.
        """
        return ', '.join(tag.name for tag in obj.tags.all())
    get_tags.short_description = 'Теги'

    def get_ingredients(self, obj):
        """
        Возвращает строку со списком ингредиентов, разделённых запятыми.
        """
        return ', '.join(i.name for i in obj.ingredients.all())
    get_ingredients.short_description = 'Ингредиенты'

    def text_short(self, obj):
        """
        Возвращает укороченную версию описания рецепта (50 символов).
        """
        return (obj.text or '')[:50]
    text_short.short_description = 'Описание'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для списка покупок.

    Показывает связи «пользователь ↔ рецепт»,
    с фильтром по пользователю, поиском и автодополнением.
    """

    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')
    empty_value_display = '-пусто-'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для тегов.

    Отображает имя и слаг, поддерживает поиск и автогенерацию слага
    по названию (prepopulated_fields).
    """

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    empty_value_display = '-пусто-'


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для коротких ссылок на рецепты.

    Позволяет искать по коду, автору и названию рецепта.
    """

    list_display = ('id', 'code', 'recipe', 'created_at')
    search_fields = ('code', 'recipe__author__username',
                     'recipe__name', 'recipe__author__email')
    autocomplete_fields = ('recipe',)
    empty_value_display = '-пусто-'
