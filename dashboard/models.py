from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg

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
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='admin_assets/img/product/', blank=True, null=True)
    cropped_image = models.ImageField(upload_to='products/cropped_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    is_bestseller = models.BooleanField(default=False)  
    is_new = models.BooleanField(default=False) 
    dietary_info = models.CharField(max_length=100, blank=True, null=True)  
    added_on = models.DateTimeField(auto_now_add=True ,null=True)
    

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image:
            
            img = Image.open(self.image.path)

            desired_size = (400, 400)

            img.thumbnail(desired_size, Image.Resampling.LANCZOS)

            new_img = Image.new("RGB", desired_size, (255, 255, 255))

            x = (desired_size[0] - img.width) // 2
            y = (desired_size[1] - img.height) // 2

            new_img.paste(img, (x, y))

            new_img.save(self.image.path)
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return 0

    def total_reviews(self):
        return self.reviews.count()
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    def total_reviews(self):
        return self.reviews.count()

    def rating_distribution(self):
        distribution = {i: self.reviews.filter(rating=i).count() for i in range(1, 6)}
        return distribution


class ProductImages(models.Model):
    product= models.ForeignKey(Product, on_delete=models.CASCADE ,related_name='images')
    image =models.ImageField(upload_to='admin_assets/img/product_multi_img/')
    
    def __str__(self):
        return f'Image for {self.product.title}'
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)
        desired_size = (400, 400)
        img.thumbnail(desired_size, Image.Resampling.LANCZOS)
        new_img = Image.new("RGB", desired_size, (255, 255, 255))
        
        x = (desired_size[0] - img.width) // 2
        y = (desired_size[1] - img.height) // 2

        new_img.paste(img, (x, y))
 
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
    stock = models.IntegerField(default=0)  
    sku = models.CharField(max_length=20, blank=True, null=True)  
    def __str__(self):
        return f"{self.product.title} - {self.weight} - ${self.price}"
    

class Review_prdct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    helpful_votes = models.IntegerField(default=0)
    images = models.ImageField(upload_to='review_images/', blank=True, null=True)
    
    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username}'s review for {self.product.title}"

class ReviewHelpful(models.Model):
    review = models.ForeignKey(Review_prdct, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')