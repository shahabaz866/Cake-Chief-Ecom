from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator

class Address(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ('HOME', 'Home'),
        ('OFFICE', 'Office'),
        ('OTHER', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='HOME')
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
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Address'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.get_address_type_display()} - {self.address}, {self.city}"

    def save(self, *args, **kwargs):
        # If this address is being set as default, remove default status from other addresses
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        # If this is the user's first address, make it default
        elif not self.pk and not Address.objects.filter(user=self.user).exists():
            self.is_default = True
        super().save(*args, **kwargs)

class UserContact(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('PRIMARY', 'Primary'),
        ('SECONDARY', 'Secondary'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    mobile_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Mobile number must be 10 digits.")]
    )
    contact_type = models.CharField(max_length=10, choices=CONTACT_TYPE_CHOICES, default='PRIMARY')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'mobile_number']

    def __str__(self):
        return f"{self.mobile_number} ({self.get_contact_type_display()})"

    def save(self, *args, **kwargs):
        # If this is primary contact, remove primary status from other contacts
        if self.contact_type == 'PRIMARY':
            UserContact.objects.filter(
                user=self.user, 
                contact_type='PRIMARY'
            ).update(contact_type='SECONDARY')
        super().save(*args, **kwargs)
  