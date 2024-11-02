from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator

class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(r'^\d{6}$', message="Pincode must be 6 digits.")]
    )
    locality = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state}"


class UserMobile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mobile_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Mobile number must be 10 digits.")]
    )

    def __str__(self):
        return self.mobile_number
    



