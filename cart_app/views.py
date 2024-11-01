from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Product
from .models import CartItem, Cart


def cart_view(request):
    cart_id, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart_id).select_related('product')
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'user_side/shop/cart.html', context)


def add_to_cart(request, id):
    # Get the product or return a 404 error if not found
    product_exi = get_object_or_404(Product, id=id)

    # Get or create a cart for the logged-in user
    cart, created = Cart.objects.get_or_create(user=request.user)

    # Get or create a cart item for the specific product in the cart
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product_exi)

    # Increment the quantity if the item already exists in the cart
    if not item_created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1  # Initialize to 1 if newly added

    # Save the cart item
    cart_item.save()

    # Redirect to the cart view instead of rendering it again here
    return redirect("cart")

def cart_remove(request, id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=id)
        print(f"Removing CartItem with ID: {cart_item.id}")  # Log the ID
        cart_item.delete()
    return redirect("cart")
