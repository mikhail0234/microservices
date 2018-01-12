from django.conf.urls import url

from .views import OrderDetailView, OrderListView


urlpatterns = [

    url(r'^orders/(?P<order_id>[0-9]+)/$', OrderDetailView.as_view(), name='order-list'),
    url(r'^orders/$', OrderListView.as_view(), name='order-detail'),
]