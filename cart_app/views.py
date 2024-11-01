from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Product
from .models import CartItem, Cart
from django.contrib import messages  
from django.views.decorators.cache import never_cache



@never_cache
def cart_view(request):
    cart_id, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart_id).select_related('product')

    
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'user_side/shop/cart.html', context)

@never_cache
def add_to_cart(request, id):
    
    product_exi = get_object_or_404(Product, id=id)

    
    cart, created = Cart.objects.get_or_create(user=request.user)


    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product_exi)

  
    if not item_created:
        cart_item.quantity += 1
    else:
  
        cart_item.quantity = 1 

    if not item_created:
        if cart_item.quantity < 10:
            cart_item.quantity += 1
        else:
            messages.warning(request, "You can only add a maximum of 10 for each product.")  
    else:
       
        cart_item.quantity = 1


    cart_item.save()


    return redirect("cart")

@never_cache
def cart_remove(request, id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=id)
        print(f"Removing CartItem with ID: {cart_item.id}")  # Log the ID
        cart_item.delete()
    return redirect("cart")
