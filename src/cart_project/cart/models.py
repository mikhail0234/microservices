from django.db import models

ORDER_STATUS_CHOICES = (
    ('created', 'Created'),
    ('in_progress', 'In Progress'),
    ('shipped', 'Shipped'),
    ('canceled', 'Cancelled'),
    ('pending', 'Pending'),
)

CITY_CHOICES = (
    ('moscow', 'Moscow'),
    ('moscow_region', 'Moscow region'),
)



class Cart(models.Model):
    session_key = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False)

    def __str__(self):
        return "Cart id: {id}".format(id=self.pk)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_id = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['date_added']

    def get_absolute_url(self):
        return self.product.get_absolute_url()


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
