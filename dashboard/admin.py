from django.contrib import admin
from .models import Product,Category,Flavour,ProductImages

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Flavour)
admin.site.register(ProductImages)

