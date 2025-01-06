from django import forms
from .models import Review_prdct

class ReviewForms(forms.ModelForm):
    class Meta:
        model = Review_prdct
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write your review here...'
            })
        }