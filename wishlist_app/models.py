from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Product,Variant


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

 