from django.conf.urls import url

from .views import ProductDetailView, ProductsListView
# from .views import CategoryDetailView , CategoryListView
from .views import CartListView, CartDetailView
from .views import CheckoutListView, CheckoutDetailView, CheckoutDetailView2, CartItem

app_name = 'gateway'
urlpatterns = [

    url(r'^products/$', ProductsListView.as_view(), name='product-list'),
    url(r'^products/(?P<product_id>[0-9]+)/$', ProductDetailView.as_view(), name='product-detail'),

    # url(r'^category/$', CategoryListView.as_view(), name='category-list'),
    # url(r'^category/(?P<category_id>[0-9]+)/$', CategoryDetailView.as_view(), name='category-detail'),

    url(r'^cart/$', CartListView.as_view(), name='cart-list'),
    url(r'^cart/(?P<cart_id>[0-9]+)/$', CartDetailView.as_view(), name='cart'),
    url(r'^cart/item/(?P<item_id>[0-9]+)/$', CartItem.as_view(), name='cart-item'),

    url(r'^checkout/(?P<order_id>[0-9]+)/$', CheckoutDetailView.as_view(), name='order-detail'),
    url(r'^checkout2/(?P<order_id>[0-9]+)/$', CheckoutDetailView2.as_view(), name='order-detail2'),
    url(r'^checkout/$', CheckoutListView.as_view(), name='order-list'),


]