from rest_framework.pagination import PageNumberPagination


class NoPagination(PageNumberPagination):
    page_size = None
