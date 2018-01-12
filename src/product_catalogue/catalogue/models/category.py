from django.db import models


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    _metadata = {
        'description': 'description',
    }

    class Meta:
        ordering = ('-created',)