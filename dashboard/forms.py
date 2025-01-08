from django import forms
from dashboard.models import Review_prdct

class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.RadioSelect(
            choices=[(i, '★' * i) for i in range(1, 6)],
            attrs={'class': 'rating-input'}
        )
    )
    
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control review-textarea',
                'placeholder': 'Share your experience with this product...',
                'rows': 4
            }
        )
    )
    
    images = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={'class': 'form-control-file'}
        )
    )

    class Meta:
        model = Review_prdct
        fields = ['rating', 'comment', 'images']
