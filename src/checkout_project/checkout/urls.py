from django.conf.urls import url

from .views import OrderDetailView, OrderListView
from rest_framework_expiring_authtoken import views as auth_views


urlpatterns = [

    url(r'^orders/(?P<order_id>[0-9]+)/$', OrderDetailView.as_view(), name='order-list'),
    url(r'^orders/$', OrderListView.as_view(), name='order-detail'),
    url(r'^token/$', auth_views.obtain_expiring_auth_token)
]