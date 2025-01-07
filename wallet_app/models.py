from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after_transaction = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    transaction_type = models.CharField(max_length=50)
    description = models.CharField(max_length=255,blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"