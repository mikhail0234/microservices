from django.conf.urls import url

from .views import ProductDetailView, ProductsListView
from .views import CategoryDetailView , CategoryListView


urlpatterns = [

    url(r'^category/$', CategoryListView.as_view(), name='category-list'),
    url(r'^category/(?P<category_id>[0-9]+)/$', CategoryDetailView.as_view(), name='category-detail'),
    url(r'^products/(?P<product_id>[0-9]+)/$', ProductDetailView.as_view(), name='product-detail'),
    url(r'^products/$', ProductsListView.as_view(), name='product-list')

]