from django.shortcuts import render
from rest_framework import generics

from .models import Cart, CartItem
from .serializer import  CartItemSerializer, CartSerializer

# Create your views here.

class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer



class CartDetailView(generics.RetrieveUpdateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    lookup_url_kwarg = "id"
    lookup_field = "id"




class CartItemView(generics.ListCreateAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer


class CartItemDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    lookup_url_kwarg = "id"
    lookup_field = "id"