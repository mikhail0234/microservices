from django.db import models

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


