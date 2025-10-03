from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import Truncator

from recipes.constants import TRUNCATE_TEXT


class User(AbstractUser):
    """
    Кастомная модель пользователя.

    Наследует стандартную модель Django `AbstractUser` и добавляет:
    - поле `avatar`: изображение профиля (опционально),
    - уникальный `email`, как основной идентификатор при логине.

    Изменения:
    - `USERNAME_FIELD` переопределён на `email`,
    - `REQUIRED_FIELDS` дополнен username, first_name и last_name.

    В админке и списках отображается обрезанный username до 30 символов.
    """

    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True, blank=True,
        verbose_name='Аватар'
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return Truncator(self.username).chars(TRUNCATE_TEXT)


class Subscribe(models.Model):
    """
    Модель подписки пользователя на других пользователей.

    Поля:
    - `user`: кто подписывается,
    - `author`: на кого оформлена подписка.

    Ограничения:
    - уникальная пара (user, author),
    - запрещена подписка на самого себя (`user != author`).

    Используется для формирования ленты и списка подписок в сервисе.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribe'
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('author')),
                name='no_self_subscribe'
            ),
        ]

    def __str__(self):
        return f'{self.user} -> {self.author}'
