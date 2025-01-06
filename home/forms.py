from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '0.5'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your review here...'
            })
        }
