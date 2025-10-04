"""
API маршруты проекта Foodgram.

Здесь регистрируются viewset’ы для основных моделей проекта:
- ингредиенты,
- теги,
- рецепты,
- пользователи.

Также подключаются эндпоинты для аутентификации через djoser.
"""

from django.urls import include, path
# from rest_framework_nested.routers import DefaultRouter
from rest_framework.routers import DefaultRouter

from api.views import (CustomUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

v1_router = DefaultRouter(trailing_slash='/?')
v1_router.register(r'ingredients', IngredientViewSet, basename='ingredient')
v1_router.register(r'tags', TagViewSet, basename='tag')
v1_router.register(r'recipes', RecipeViewSet, basename='recipe')
v1_router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

# api_v1_patterns = [
#     path('', include(v1_router.urls)),
# ]

# urlpatterns = [
#     path('/v1/', include(api_v1_patterns)),
#     path('/auth/', include('djoser.urls.authtoken')),
# ]
