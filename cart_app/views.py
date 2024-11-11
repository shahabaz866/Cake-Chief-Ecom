from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Product
from django.contrib import messages  
from django.views.decorators.cache import never_cache
from cart_app.models import Cart, CartItem
from order_app.models import  Order, OrderItem
from user_app.models import Address, UserContact
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F
from decimal import Decimal

@never_cache
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    
    # Calculate total cart price
    cart_total = float(sum(item.quantity * item.product.price for item in cart_items))

    request.session['cart_total'] = cart_total
      
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }
    return render(request, 'user_side/shop/cart.html', context)

@never_cache
def add_to_cart(request, id):
    if request.user.is_authenticated and request.user.username == 'demo_user':
        messages.info(request, "Please log in to access the Add to Cart feature.")
        return redirect('login')
    else:
        product = get_object_or_404(Product, id=id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        remaining_stock = product.stock


        # Update the quantity, but limit it to a maximum of 10
        if not created:
                if cart_item.quantity < remaining_stock and cart_item.quantity < 10:
                    cart_item.quantity = F('quantity') + 1
                    cart_item.save()
                    cart_item.refresh_from_db()
                else:
                    messages.warning(request, f"You can only add up to {min(remaining_stock, 10)} of this product.")

        else:
            cart_item.quantity = 1
            cart_item.save()

        # Calculate and save total price for the cart item
        cart_item.total_price = cart_item.quantity * cart_item.product.price
        cart_item.save()

        # Calculate and save the cart total
        cart.total = sum(item.quantity * item.product.price for item in cart.cartitem_set.all())
        cart.save()
        
        return redirect("cart_app:cart")

def quantity_plus(request, item_id):

    item = get_object_or_404(CartItem, pk=item_id)
    response_data = {}

    if item.quantity < 10:
        item.quantity = F('quantity') + 1
        item.save()
        
    else:
        response_data['error'] = 'Each customer is limited to a maximum purchase quantity of 10 units'

    item.refresh_from_db()
    response_data['quantity'] = item.quantity
    response_data['item_subtotal'] = float(item.quantity * item.product.price)
    response_data['total_price'] = float(sum(i.quantity * i.product.price for i in CartItem.objects.filter(cart=item.cart)))

    return JsonResponse(response_data)

def quantity_minus(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    response_data = {}

    if item.quantity > 1:
        item.quantity = F('quantity') - 1
        item.save()
    else:
        response_data['error'] = 'Product quantity must be at least 1'

    item.refresh_from_db()
    response_data['quantity'] = item.quantity
    response_data['total_price'] = float(sum(i.quantity * i.product.price for i in CartItem.objects.filter(cart=item.cart)))

    return JsonResponse(response_data)


@never_cache
def cart_remove(request, id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=id)
        cart = cart_item.cart
        cart_item.delete()
        
        # Recalculate cart total after removing the item
        cart.total = sum(item.quantity * item.product.price for item in CartItem.objects.filter(cart=cart))
        cart.save()
    return redirect("cart_app:cart")





@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')

    if not cart_items:
        messages.warning(request, "Your cart is empty!")
        return redirect('cart_app:cart')
    
    cart_total = request.session.get('cart_total', 0)
   
    user = request.user
    try:
        user_mobile = UserContact.objects.get(
            user=user, 
            contact_type='PRIMARY'
        ).mobile_number
    except UserContact.DoesNotExist:
        user_mobile = ''

    addresses = Address.objects.filter(
        user=user,
        is_active=True
    ).order_by('-is_default')
    
    default_address = addresses.filter(is_default=True).first()




    

    if request.method == 'POST':
        try:
            # Retrieve form data
            order_data = {
                'user': request.user,
                'payment_method': request.POST.get('payment'),
                'total_amount': cart_total,
            }
            order = Order.objects.create(**order_data)

            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                    # size=item.
                )
            
            # Clear cart
            cart_items.delete()
            return redirect('order_app:order_confirmation', order_id=order.id)
                
        except Exception:
            messages.error(request, 'There was an error processing your order. Please try again.')
            return render(request,'user_side/shop/checkout.html')
    
    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart': cart,  
        'user': user,
        'user_mobile': user_mobile,
        'addresses': addresses,
        'default_address': default_address,
    }
    
    return render(request, 'user_side/shop/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
        'order_items': order.orderitem_set.all()
    }
    return render(request, 'order_confirmation.html', context)


def sample(request):
    return render(request,'user_side/shop/sample.html')
