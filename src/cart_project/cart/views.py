from django.shortcuts import render
from rest_framework import generics

from .models import Cart, CartItem
from .serializer import  CartItemSerializer, CartSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework_expiring_authtoken.authentication import ExpiringTokenAuthentication

from django.contrib.auth.models import User as User2
from rest_framework.authtoken.models import Token

for user in User2.objects.all():
    Token.objects.get_or_create(user=user)

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