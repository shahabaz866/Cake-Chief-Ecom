from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class HeroBanner(models.Model):
    image = models.ImageField(upload_to='hero_banners/')
    title = models.CharField(max_length=200, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    helpful_votes = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.user.username} - {self.rating} stars"
    

class HelpfulVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    review = models.ForeignKey(Review, on_delete=models.CASCADE) 
    voted_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        unique_together = ('user', 'review')  

    def __str__(self):
        return f"{self.user.username} voted for review {self.review.id}"