from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BasicUserAdmin

from users.models import Subscribe, User


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """
    Конфигурация админки для модели Subscribe (подписки пользователей).

    Отображает список подписок с указанием:
    - ID,
    - пользователя,
    - автора, на которого оформлена подписка.

    Добавлены:
    - фильтры по пользователю и автору,
    - поиск по email и username,
    - автозаполнение полей user и author.
    """

    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__email', 'user__username',
                     'author__email', 'author__username')
    autocomplete_fields = ('user', 'author')
    empty_value_display = '-пусто-'


@admin.register(User)
class UserAdmin(BasicUserAdmin):
    """
    Конфигурация админки для модели User (кастомного пользователя).

    Отображает список пользователей с полями:
    - ID,
    - username,
    - имя и фамилия,
    - email,
    - статус администратора (is_staff).

    Дополнительно:
    - поиск по username и email,
    - сортировка по ID,
    - в стандартные поля админки добавлено поле avatar.
    """

    list_display = ('id', 'username', 'first_name',
                    'last_name', 'email', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('id',)
    fieldsets = BasicUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar',)}),
    )
    add_fieldsets = BasicUserAdmin.add_fieldsets
    empty_value_display = '-пусто-'
