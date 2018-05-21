from django.shortcuts import render
from rest_framework import generics

from .models import Cart, CartItem
from .models import Order
from .serializer import  CartItemSerializer, CartSerializer
from .serializer import OrderSerializer

# from rest_framework.permissions import IsAuthenticated
# from rest_framework_expiring_authtoken.authentication import ExpiringTokenAuthentication


from rest_framework import permissions, routers, serializers, viewsets

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope

# from django.contrib.auth.models import User as User2
# from rest_framework.authtoken.models import Token

# for user in User2.objects.all():
#     Token.objects.get_or_create(user=user)

class CartView(generics.ListCreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = Cart.objects.all()
    serializer_class = CartSerializer



class CartDetailView(generics.RetrieveUpdateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    lookup_url_kwarg = "id"
    lookup_field = "id"




class CartItemView(generics.ListCreateAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer


class CartItemDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (ExpiringTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    lookup_url_kwarg = "id"
    lookup_field = "id"


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
