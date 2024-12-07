from django.contrib import admin
from .models import Product,Category,Flavour,ProductImages,Variant

admin.site.register(Product)
admin.site.register(Category)
admin.site.register(Flavour)
admin.site.register(ProductImages)
admin.site.register(Variant)

