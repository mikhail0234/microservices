from django.db import models
from .category import Category

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    content = models.TextField(verbose_name='Content Description')
    created = models.DateTimeField(auto_now_add=True)
    category = models.ManyToManyField(Category, blank=True)

    _metadata = {
        'description': 'content',
    }

    class Meta:
        ordering = ('-created',)
