from django.contrib import admin

from .models import Cart, CartItem
#
class CartItemInline(admin.TabularInline):
    model = CartItem

class CartAdmin(admin.ModelAdmin):
    model = Cart
    list_display = ('id', 'created', )
    inlines = [
        CartItemInline
    ]

admin.site.register(Cart, CartAdmin)