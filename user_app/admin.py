from django.contrib import admin
from .models import UserAddress
from .models import UserMobile
# Register your models here.

admin.site.register(UserAddress)
admin.site.register(UserMobile)