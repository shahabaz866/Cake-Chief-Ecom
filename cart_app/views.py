from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Product
from django.contrib import messages  
from django.views.decorators.cache import never_cache
from cart_app.models import Cart,CartItem,Order,OrderItem
from django.contrib.auth.decorators import login_required
from django.db.models import F
from decimal import Decimal


@never_cache
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    # cart_items.total_price = sum(item.quantity * item.product.price for item in cart_items)
   
    # cart_items.save()






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
    
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')

    cart_item.save()
    cart.total = sum(item.quantity * item.product.price for item in cart_items)
    cart.save()
   
    


    return redirect("cart")

@never_cache
def cart_remove(request, id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=id)
        print(f"Removing CartItem with ID: {cart_item.id}")  # Log the ID
        cart_item.delete()
    return redirect("cart")


@login_required
def checkout_view(request):
    # Retrieve the cart for the logged-in user
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')

    # Check if cart is empty
    if not cart_items:
        messages.warning(request, "Your cart is empty!")
        return redirect('cart')

    cart_total = request.session.get('cart_total', 0)  # Retrieve from session

    if request.method == 'POST':
        # Gather form data
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        address2 = request.POST.get('address2', '')  # Optional
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        order_notes = request.POST.get('orderNotes', '')
        payment_method = request.POST.get('payment')
        
        try:
            # Create the order
            order = Order.objects.create(
                user=request.user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                address2=address2,
                city=city,
                state=state,
                pincode=pincode,
                order_notes=order_notes,
                payment_method=payment_method,
                total_amount=cart_total  # Use the session cart total here
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price,
                    size=item.size
                )
            
            # Clear the cart after checkout
            cart_items.delete()
            
            # Redirect based on payment method
            if payment_method == 'upi':
                return redirect('payment_gateway', order_id=order.id)
            else:
                messages.success(request, 'Order placed successfully!')
                return redirect('order_confirmation', order_id=order.id)
                
        except Exception as e:
            messages.error(request, 'There was an error processing your order. Please try again.')
            return redirect('checkout')
    
    context = {
        'cart_items': cart_items,
        'total': cart_total,
          'cart':cart,  
    }
    
    return render(request, 'user_side/shop/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        context = {
            'order': order,
            'order_items': order.orderitem_set.all()
        }
        return render(request, 'order_confirmation.html', context)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found!')
        return redirect('home')
