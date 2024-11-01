from django.shortcuts import render

# Create your views here.

def order_view(request):
    return render(request,'user_side/shop/shop.html')