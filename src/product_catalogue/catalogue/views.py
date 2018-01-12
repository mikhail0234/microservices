from rest_framework import generics
from .models.product import Product
from .models.category import Category
from .pagination import ProductsPagination
from .serializer import ProductSerializer, CategorySerializer




class ProductsListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = ProductsPagination



class ProductDetailView(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    lookup_url_kwarg = "product_id"
    lookup_field = "product_id"

class CategoryListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = CategorySerializer


class CategoryDetailView(generics.RetrieveUpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    lookup_url_kwarg = "category_id"
    lookup_field = "category_id"



