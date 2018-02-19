from rest_framework import generics
from .models import Order
from .serializer import OrderSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework_expiring_authtoken.authentication import ExpiringTokenAuthentication

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

for user in User.objects.all():
    Token.objects.get_or_create(user=user)



class OrderListView(generics.ListCreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    lookup_url_kwarg = "order_id"
    lookup_field = "order_id"
