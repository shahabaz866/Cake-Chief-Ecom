import datetime
from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Product, Variant
from django.contrib import messages  
from django.views.decorators.cache import never_cache
from cart_app.models import Cart, CartItem , Coupon
from order_app.models import Order, OrderItem
from user_app.models import Address, UserContact
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F
from decimal import Decimal
from django.db.models import Sum
from django.db import transaction
import razorpay
import json 
from django.conf import settings
from django.utils.timezone import now
from django.http import HttpResponse



def calculate_cart_total(cart):

    # Calculate the subtotal
    subtotal = CartItem.objects.filter(cart=cart).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or Decimal('0.00')

    # Define additional charges and tax rate
    tax_rate = Decimal('0.03')
    delivery_charge = Decimal('50.00')
    packaging_charge = Decimal('20.00')

    # Calculate the tax
    tax = subtotal * tax_rate

    # Apply discount
    discount = cart.coupon.discount if cart.coupon else Decimal('0.00')

    # Calculate the grand total
    total = subtotal - discount + tax + delivery_charge + packaging_charge

    # Save these values in the cart
    cart.subtotal = subtotal
    cart.discount = discount
    cart.tax = tax
    cart.delivery_charge = delivery_charge
    cart.packaging_charge = packaging_charge
    cart.total = total
    cart.save()
    


    return {
        'subtotal': float(subtotal),
        'discount': float(discount),
        'tax': float(tax),
        'delivery_charge': float(delivery_charge),
        'packaging_charge': float(packaging_charge),
        'grand_total': float(total),
    }


@never_cache
def add_to_cart(request, id):
    if request.user.is_authenticated and request.user.username == 'demo_user':
        messages.info(request, "Please log in to access the Add to Cart feature.")
        return redirect('login')

    if request.method == 'POST':
        product = get_object_or_404(Product, id=id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        variant_id = request.POST.get('variant')
        variant = get_object_or_404(Variant, id=variant_id)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant
        )

        if not created:
            # Check if the quantity is less than the stock or max limit
            if cart_item.quantity < min(variant.stock, 10):
                cart_item.quantity = F('quantity') + 1
            else:
                messages.warning(request, "You cannot add more than the available stock or the limit of 10.")
        else:
            cart_item.quantity = 1  # Initialize quantity for new items

        cart_item.price = variant.price
        cart_item.save()
        cart_item.refresh_from_db()

        # Recalculate and save the total, tax, delivery, and packaging charges
        totals = calculate_cart_total(cart)
        cart.total = totals['grand_total']
        cart.save()

        return redirect("cart_app:cart")


def quantity_plus(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    response_data = {}
    
    if item.quantity < 10:
        if item.quantity + 1 <= item.variant.stock:
            item.quantity = F('quantity') + 1
            item.save()
        else:
            response_data['error'] = 'Not enough stock available'
    else:
        response_data['error'] = 'Each customer is limited to a maximum purchase quantity of 10 units'

    item.refresh_from_db()
    
    # Calculate the updated cart totals
    cart_total_data = calculate_cart_total(item.cart)
    
    response_data['quantity'] = item.quantity
    response_data['item_subtotal'] = float(item.quantity * item.price)
    response_data['cart_subtotal'] = cart_total_data['subtotal']
    response_data['tax'] = cart_total_data['tax']
    response_data['delivery_charge'] = cart_total_data['delivery_charge']
    response_data['packaging_charge'] = cart_total_data['packaging_charge']
    response_data['grand_total'] = cart_total_data['grand_total']

    # Save the updated total in the cart
    item.cart.total = response_data['grand_total']
    item.cart.save()
    
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
    
    # Calculate the updated cart totals
    cart_total_data = calculate_cart_total(item.cart)
    
    response_data['quantity'] = item.quantity
    response_data['item_subtotal'] = float(item.quantity * item.price)
    response_data['cart_subtotal'] = cart_total_data['subtotal']
    response_data['tax'] = cart_total_data['tax']
    response_data['delivery_charge'] = cart_total_data['delivery_charge']
    response_data['packaging_charge'] = cart_total_data['packaging_charge']
    response_data['grand_total'] = cart_total_data['grand_total']

    # Save the updated total in the cart
    item.cart.total = response_data['grand_total']
    item.cart.save()

    return JsonResponse(response_data)
 

@never_cache
def cart_remove(request, id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=id)
        cart = cart_item.cart

        cart_item.delete()

        # Recalculate cart total after removing the item
        cart.total = sum(item.quantity * item.price for item in CartItem.objects.filter(cart=cart))
        cart.save()

    return redirect("cart_app:cart")

@never_cache
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')

    totals = calculate_cart_total(cart)
   

    context = {
        'cart_items': cart_items,
        'cart_subtotal': totals['subtotal'],
        'tax': totals['tax'],
        'discount': totals['discount'],
        'delivery_charge': totals['delivery_charge'],
        'packaging_charge': totals['packaging_charge'],
        'grand_total': totals['grand_total'],
        'coupon': cart.coupon,
    }
    return render(request, 'user_side/shop/cart.html', context)




@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    carts = Cart.objects.filter(user = request.user)
    
    
    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')


    if not cart_items:
        messages.warning(request, "Your cart is empty!")
        return redirect('cart_app:cart')

    # Calculate cart totals
    cart_subtotal = cart_items.aggregate(
        subtotal=Sum(F('quantity') * F('variant__price'))
    )['subtotal'] or 0

    discount = cart.coupon.discount if cart.coupon else 0
    delivery_charge = cart.delivery_charge
    packaging_charge = cart.packaging_charge
    tax = cart.tax
    grand_total = max(cart_subtotal - discount + delivery_charge + packaging_charge + tax, 0)
    cart.total = grand_total
    cart.save()




    user = request.user
    try:
        user_mobile = UserContact.objects.get(user=user, contact_type='PRIMARY').mobile_number
    except UserContact.DoesNotExist:
        user_mobile = ''

    addresses = Address.objects.filter(user=user, is_active=True).order_by('-is_default')
    default_address = addresses.filter(is_default=True).first()

    if not addresses or not default_address:
        messages.warning(request, "Please add a delivery address before proceeding!")
        return redirect('user_app:add_address')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                user_address=default_address,
                payment_method=payment_method,
                total_amount=cart.total,
                subtotal = cart_subtotal  
            )
            print("heee.",order.subtotal)

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variants=item.variant,
                    quantity=item.quantity,
                    price=item.variant.price,
                    
                )
                item.variant.stock = F('stock') - item.quantity
                item.variant.save()

            if payment_method == 'cod':
                cart_items.delete()
                cart.total = 0
                cart.save()
                messages.success(request, "Order placed successfully with Cash on Delivery!")
                return redirect('cart_app:order_confirmation', order_id=order.id)

            elif payment_method == 'razorpay':
                try:

                    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
                    razorpay_order = client.order.create({
                        'amount': int(grand_total * 100),  # Amount in paise (INR)
                        'currency': 'INR',
                        'receipt': str(order.id),
                        'payment_capture': 1  # Auto-capture after payment
                    })
                except razorpay.errors.RazorpayError as e:
                    messages.error(request, f"Error creating Razorpay order: {str(e)}")
                    return redirect('checkout')


                order.razorpay_order_id = razorpay_order['id']
                order.save()

               
                context = {
                    'order': order,
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'grand_total':  int(grand_total * 100),
                    'user': user,
                    'user_mobile': user_mobile,
                    'addresses': addresses,
                    'default_address': default_address,
                }
                return render(request, 'user_side/payment/payment.html', context)

            else:
                messages.error(request, "Invalid payment method selected.")
                return redirect('checkout')

    context = {
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'discount': discount,
        'tax': tax,
        'delivery_charge': delivery_charge,
        'packaging_charge': packaging_charge,
        'grand_total': grand_total,
        'user': user,
        'user_mobile': user_mobile,
        'addresses': addresses,
        'default_address': default_address,
    }

    return render(request, 'user_side/shop/checkout.html', context)



def get_primary_mobile_number(user):
        primary_contact = UserContact.objects.filter(user=user, contact_type='PRIMARY', is_active=True).first()
        return primary_contact.mobile_number if primary_contact else None
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    cart = Cart.objects.filter(user=request.user)
    order_items = order.orderitem_set.all().select_related('product')


   
    
     

    default_address = Address.objects.filter(user=request.user, is_default=True).first()
    if not default_address:
        default_address = Address.objects.filter(user=request.user).first()

    primary_mobile_number = get_primary_mobile_number(request.user)

    

    context = {
        'order': order,
        'order_items': order_items,
        'payment_status': 'Paid' if order.is_paid else 'Pending',
        'default_address': default_address,
        'primary_mobile_number': primary_mobile_number,
        # 'grand_total':cart_total,
    }

    return render(request, 'user_side/order/order_confirm.html', context)

# @login_required
# def verify_payment(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         razorpay_payment_id = data.get('razorpay_payment_id')
#         razorpay_order_id = data.get('razorpay_order_id')
#         razorpay_signature = data.get('razorpay_signature')

#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#         try:
#             client.utility.verify_payment_signature({
#                 'razorpay_order_id': razorpay_order_id,
#                 'razorpay_payment_id': razorpay_payment_id,
#                 'razorpay_signature': razorpay_signature,
#             })

#             # Update order status to 'PAID'
#             order = Order.objects.get(razorpay_order_id=razorpay_order_id)
#             order.order_status = 'PAID'
#             order.save()

#             return JsonResponse({'success': True})
#         except razorpay.errors.SignatureVerificationError:
#             return JsonResponse({'success': False})


@login_required
def verify_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
       
        razorpay_order_id = data.get('razorpay_order_id')
        print(razorpay_order_id)
        razorpay_signature = data.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # Verify the Razorpay payment signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Update the order status to 'PAID' in the database
            order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)
            order.order_status = 'PAID'
            order.is_paid = True
            order.save()

            # Clear the cart after payment
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart).delete()
            cart.total = 0
            cart.save()

            messages.success(request, "Payment verified and order placed successfully.")
            return JsonResponse({'success': True})
        except razorpay.errors.SignatureVerificationError as e:
            messages.error(request, "Payment verification failed.")
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



@never_cache
def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip()
        cart = get_object_or_404(Cart, user=request.user)
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True, valid_to__gte=datetime.date.today())
            cart.coupon = coupon
            cart.save()
            print(cart.coupon.discount)
            messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon.")
    return redirect('cart_app:cart')

def remove_coupon(request):
    cart = Cart.objects.get(user=request.user)
    cart.coupon = None
    cart.save()
    return redirect('cart_app:cart')  