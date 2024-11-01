from django.contrib.auth.models import User
from django.db import models

class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    pincode = models.CharField(max_length=6)
    locality = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.address
    
class UserMobile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=10)

    def __str__(self):
        return self.mobile_number