from django.db import models
from django.contrib.auth.models import User
from user_app.models import Address,UserContact
from django.utils.translation import gettext_lazy as _
from .constants import PaymentStatus


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('upi', 'UPI Payment'),
        ('paypal','paypal'),
        ('cod', 'Cash on Delivery'),
         ('wallet', 'Wallet'),
        
    )
    ORDER_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('REFUND', 'Refund'),
    ]

    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    user_address = models.ForeignKey('user_app.Address', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    cancellation_reason = models.TextField(max_length=200, null=True, blank=True)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES,null=False, blank=False, default='PENDING')
    cancellation_requested = models.BooleanField(default=False)
    CANCELLATION_PENDING = 'Pending'
    CANCELLATION_APPROVED = 'Approved'
    CANCELLATION_REJECTED = 'Rejected'

    CANCELLATION_STATUS_CHOICES = [
        (CANCELLATION_PENDING, 'Pending'),
        (CANCELLATION_APPROVED, 'Approved'),
        (CANCELLATION_REJECTED, 'Rejected'),
    ]

    cancellation_status = models.CharField(
        max_length=10,
        choices=CANCELLATION_STATUS_CHOICES,
        default=CANCELLATION_PENDING,
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    customer_name = models.CharField(_("Customer Name"), max_length=254, blank=False,default="N/A", null=False)
    payment_status = models.CharField(
        _("Payment Status"),
        default=PaymentStatus.PENDING,
        max_length=254,
        choices=PaymentStatus.CHOICES,
        blank=False,
        null=False,
    )
    provider_order_id = models.CharField(
        _("Order ID"), max_length=40,default="N/A", null=False, blank=False
    )
    payment_id = models.CharField(
        _("Payment ID"), max_length=36,default="N/A", null=False, blank=False
    )
    signature_id = models.CharField(
        _("Signature ID"), max_length=128,default="N/A", null=False, blank=False
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order {self.id} - {self.user.username} - {self.payment_status}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('dashboard.Product', on_delete=models.CASCADE)
    variants = models.ForeignKey('dashboard.Variant', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    size = models.CharField(max_length=10, null=True, blank=True)  

    def __str__(self):
        return f'{self.quantity}x {self.product.title} in Order {self.order.id}'