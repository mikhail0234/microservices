from django.contrib import admin

from .models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ('cart_id','email', 'phone', 'status', 'city', 'street')


admin.site.register(Order, OrderAdmin)


