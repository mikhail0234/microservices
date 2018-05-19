from django.contrib import admin

from .models import Cart, CartItem
from .models import Order
#
class CartItemInline(admin.TabularInline):
    model = CartItem

class CartAdmin(admin.ModelAdmin):
    model = Cart
    list_display = ('id', 'created', )
    inlines = [
        CartItemInline
    ]

class OrderAdmin(admin.ModelAdmin):
    list_display = ('cart_id','email', 'phone', 'status', 'city', 'street')



admin.site.register(Order, OrderAdmin)

admin.site.register(Cart, CartAdmin)
