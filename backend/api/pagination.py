from rest_framework.pagination import PageNumberPagination


class PageNumberWithLimit(PageNumberPagination):
    """
    Кастомная пагинация для API.

    Особенности:
        - По умолчанию на странице отображается 6 объектов.
        - Параметр `page` управляет номером страницы.
        - Параметр `limit` - задать количество объектов на странице.
        - Максимальное количество объектов на странице — 100.
    """

    page_size = 6
    page_query_param = 'page'
    page_size_query_param = 'limit'
    max_page_size = 100
