from django.conf.urls import url

from .views import ProductDetailView, ProductsListView
# from .views import CategoryDetailView , CategoryListView
from .views import CartListView, CartDetailView
from .views import CheckoutListView, CheckoutDetailView, CheckoutDetailView2, CheckoutChangeStatus, CartItem
from .views import ProductsListApiView, ProductDetailApiView
from .views import CartDetailApiView, CartItemApi
from .views import CheckoutDetailApiView, CheckoutDetailApiView2

from .views import TokenAPIView, TokenView, AuthView, AuthAPIView

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
    url(r'^checkout3/(?P<order_id>[0-9]+)/$', CheckoutChangeStatus.as_view(), name='order-detail3'),
    url(r'^checkout/$', CheckoutListView.as_view(), name='order-list'),
    url(r'^token/$', TokenView.as_view(), name='token'),
    url(r'^auth/$', AuthView.as_view(), name='auth'),



    url(r'^api/products/$', ProductsListApiView.as_view(), name='product-list-api'),
    url(r'^api/products/(?P<product_id>[0-9]+)/$', ProductDetailApiView.as_view(), name='product-detail-api'),
    url(r'^api/cart/(?P<cart_id>[0-9]+)/$', CartDetailApiView.as_view(), name='cart-api'),
    url(r'^api/cart/item/(?P<item_id>[0-9]+)/$', CartItemApi.as_view(), name='cart-item-api'),
    url(r'^api/checkout/(?P<order_id>[0-9]+)/$', CheckoutDetailApiView.as_view(), name='order-detail-api'),
    url(r'^api/checkout2/(?P<order_id>[0-9]+)/$', CheckoutDetailApiView2.as_view(), name='order-detail2-api'),
    url(r'^api/checkout3/(?P<order_id>[0-9]+)/$', CheckoutChangeStatus.as_view(), name='order-detail3'),
    url(r'^api/token/$', TokenAPIView.as_view(), name='token-api'),
    url(r'^api/auth/$', AuthAPIView.as_view(), name='auth-api'),
]





