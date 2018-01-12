from django.db import models

ORDER_STATUS_CHOICES = (
    ('created', 'Created'),
    ('in_progress', 'In Progress'),
    ('shipped', 'Shipped'),
    ('canceled', 'Cancelled'),
)

CITY_CHOICES = (
    ('moscow', 'Moscow'),
    ('moscow_region', 'Moscow region'),
)


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    cart_id = models.IntegerField()
    full_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=120, null=True, blank=True)
    status = models.CharField(choices=ORDER_STATUS_CHOICES, max_length=120, default='Created')
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    city = models.CharField(choices=CITY_CHOICES, max_length=120)
    street = models.CharField(max_length=255)

    class Meta:
        ordering = ['-created_at']