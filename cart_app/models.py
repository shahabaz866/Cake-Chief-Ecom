# cart_app/models.py

from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Product  


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product, through='CartItem')
    created_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    def get_total_price(self):
        return sum(item.quantity * item.product.price for item in self.cartitem_set.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    def save(self, *args, **kwargs):
        # Automatically calculate the total price before saving
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)


