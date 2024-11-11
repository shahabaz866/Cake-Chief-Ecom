from django.db import models
from django.contrib.auth.models import User
from user_app.models import Address,UserContact


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('upi', 'UPI Payment'),
        ('cod', 'Cash on Delivery'),
    )
    ORDER_STATUS_CHOICES=[
       ('PENDING', 'Pending'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED','Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
    ('REFUND', 'Refund'),
    ('DISPATCH', 'Dispatch'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    user_address =models.ForeignKey(Address,on_delete=models.CASCADE,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    cancelation_reson =models.TextField(max_length=200,null=True)
    order_status= models.CharField(max_length=20,choices=ORDER_STATUS_CHOICES,default='Pending')
    grand_total =models.DecimalField(max_digits=10,decimal_places=2,default=0.00,null=True)
    shipping_price=models.DecimalField(max_digits=10,decimal_places=2,default=0.00,null=True)
    tax= models.DecimalField(max_digits=10,decimal_places=2,default=0.00,null=True)

    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f'Order {self.id} - {self.user.username}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('dashboard.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null= True,blank=None)
    price = models.DecimalField(max_digits=10, decimal_places=2) 
    size = models.CharField(max_length=10,null=True)
    
    def __str__(self):
        return f'{self.quantity}x {self.product.title} in Order {self.order.id}'
