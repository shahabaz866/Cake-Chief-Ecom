from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Product  

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product,through='CartItem')
    created_at = models.DateTimeField(auto_now=True)

    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(default=0.00,max_digits=10,decimal_places=2)

