from django.contrib import admin
from .models import Address
from .models import UserContact
# Register your models here.

admin.site.register(Address)
admin.site.register(UserContact)