from rest_framework import pagination


class ProductsPagination(pagination.PageNumberPagination):
       page_size = 2
