from django.db import models
from django.contrib.auth.models import User
from dashboard.models import Product,Variant 
from django.utils.timezone import now
from django.utils.timezone import make_aware



class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product, through='CartItem')
    created_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    tax = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    delivery_charge = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    packaging_charge = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    coupon = models.ForeignKey('Coupon', null=True, blank=True, on_delete=models.SET_NULL)


    def get_total_price(self):
        return sum(item.quantity * item.product.price for item in self.cartitem_set.all())
    def calculate_grand_total(self):
        subtotal = self.get_total_price()
        discount = (subtotal * self.coupon.discount / 100) if self.coupon else 0
        return subtotal - discount + self.tax + self.delivery_charge + self.packaging_charge

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, null=True, blank=True, on_delete=models.SET_NULL, related_name='variant_cart')
    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if self.variant:
            self.total_price = self.variant.price * self.quantity
        else:
            self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)  
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.valid_from and self.valid_to:
            self.valid_from = make_aware(self.valid_from)
            self.valid_to = make_aware(self.valid_to)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code