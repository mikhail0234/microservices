from django.conf.urls import url

from .views import CartView, CartDetailView, CartItemView, CartItemDetail
from .views import OrderDetailView, OrderListView

# from rest_framework_expiring_authtoken import views as auth_views

urlpatterns = [

    url(r'^cart/$', CartView.as_view(), name='cart-list'),
    url(r'^cart/(?P<id>[0-9]+)/$', CartDetailView.as_view(), name='cart-detail'),
    url(r'^item/$', CartItemView.as_view(), name='cart-detail'),
    url(r'^item/add/$', CartItemView.as_view(), name='cart-add'),
    url(r'^item/(?P<id>[0-9]+)/$', CartItemDetail.as_view(), name='cart-detail'),

    url(r'^orders/(?P<order_id>[0-9]+)/$', OrderDetailView.as_view(), name='order-list'),
    url(r'^orders/$', OrderListView.as_view(), name='order-detail'),
    # url(r'^token/$', auth_views.obtain_expiring_auth_token),
]
