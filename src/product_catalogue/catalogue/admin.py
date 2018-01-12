from django.contrib import admin

from .models.product import Product
from .models.category import Category



class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ('name',)}


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ('name',)}
    list_display = ('name', 'price', 'slug', )


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)