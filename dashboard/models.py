from django.db import models
from django.contrib.auth.models import User
from PIL import Image
import os
import PIL

# from django.conf import settings

class Category(models.Model):

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=250)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Flavour(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=250)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    

class Size(models.Model):
    name = models.CharField(max_length=50) 
   
    is_active = models.BooleanField(default=True) 
    def __str__(self):
        return self.name


class Product(models.Model):

    id = models.AutoField(primary_key=True) 
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, null=True)
    flavour = models.ForeignKey(Flavour, related_name='products', on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=50)
    stock = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='admin_assets/img/product/', blank=True, null=True)
    cropped_image = models.ImageField(upload_to='products/cropped_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    priority = models.IntegerField(default=0)
    is_bestseller = models.BooleanField(default=False)  
    is_new = models.BooleanField(default=False) 
    dietary_info = models.CharField(max_length=100, blank=True, null=True)  
    sizes = models.ManyToManyField(Size, related_name='products')
    added_on = models.DateTimeField(auto_now_add=True ,null=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image:
            # Open the image
            img = Image.open(self.image.path)
            
            # Define the desired size (400x400)
            desired_size = (400, 400)
            
            # Resize the image while maintaining aspect ratio
            img.thumbnail(desired_size, Image.Resampling.LANCZOS)
            
            # Create a new blank image with the desired size (400x400)
            new_img = Image.new("RGB", desired_size, (255, 255, 255))
            
            # Calculate the position to paste the thumbnail on the new image
            x = (desired_size[0] - img.width) // 2
            y = (desired_size[1] - img.height) // 2
            
            # Paste the thumbnail onto the new image
            new_img.paste(img, (x, y))
            
            # Save the new image back to the same path
            new_img.save(self.image.path)


class ProductImages(models.Model):
    product= models.ForeignKey(Product, on_delete=models.CASCADE ,related_name='images')
    image =models.ImageField(upload_to='admin_assets/img/product_multi_img/')
    
    def __str__(self):
        return f'Image for {self.product.title}'
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Open the image
        img = Image.open(self.image.path)
        
        # Define the desired size
        desired_size = (400, 400)
        
        # Calculate the new size to maintain aspect ratio
        img.thumbnail(desired_size, Image.Resampling.LANCZOS)
        
        # Create a new blank image with the desired size
        new_img = Image.new("RGB", desired_size, (255, 255, 255))
        
        # Calculate the position to paste the thumbnail on the new image
        x = (desired_size[0] - img.width) // 2
        y = (desired_size[1] - img.height) // 2
        
        # Paste the thumbnail onto the new image
        new_img.paste(img, (x, y))
        
        # Save the new image back to the same path
        new_img.save(self.image.path)


class Variant(models.Model):
    WEIGHT_CHOICES=[
         ('0.5kg', '0.5 kg'),
        ('1kg', '1 kg'),
        ('1.5kg', '1.5 kg'),
        ('2kg', '2 kg'),
    ]

    product =models.ForeignKey(Product,on_delete=models.CASCADE, related_name='variants')
    weight = models.CharField(max_length=10, choices=WEIGHT_CHOICES)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.weight} - ${self.price}"



