import datetime
from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Product, Variant
from django.contrib import messages  
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from cart_app.models import Cart, CartItem , Coupon
from order_app.models import Order, OrderItem
from user_app.models import Address, UserContact
from wallet_app.models import Wallet
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import F
from decimal import Decimal
from django.db.models import Sum
from django.db import transaction 
from django.conf import settings
from django.utils import timezone
import paypalrestsdk 
from wallet_app.models import Wallet, Transaction
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
import uuid
from django.urls import reverse


def calculate_cart_total(cart):

    subtotal = CartItem.objects.filter(cart=cart).aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or Decimal('0.00')

    tax_rate = Decimal('0.03')
    delivery_charge = Decimal('50.00')
    packaging_charge = Decimal('20.00')

    tax = subtotal * tax_rate

    discount = cart.coupon.discount if cart.coupon else Decimal('0.00')

    total = subtotal - discount + tax + delivery_charge + packaging_charge

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
        
        if not variant_id:
            variant = Variant.objects.filter(product=product).first()
            if not variant:
                messages.error(request, "No variant available for this product")
                return redirect('wishlist_app:wishlist')
        else:
            try:
                variant = get_object_or_404(Variant, id=variant_id)
            except:
                messages.error(request, "Invalid variant selected")
                return redirect('wishlist_app:wishlist')

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, variant=variant
        )

        if not created:
            if cart_item.quantity < min(variant.stock, 10):
                cart_item.quantity = F('quantity') + 1
            else:
                messages.warning(request, "You cannot add more than the available stock or the limit of 10.")
        else:
            cart_item.quantity = 1

        cart_item.price = variant.price
        cart_item.save()
        cart_item.refresh_from_db()

        totals = calculate_cart_total(cart)
        cart.total = totals['grand_total']
        cart.save()

        return redirect("cart_app:cart")

@never_cache
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
    
    cart_total_data = calculate_cart_total(item.cart)
    
    response_data['quantity'] = item.quantity
    response_data['item_subtotal'] = float(item.quantity * item.price)
    response_data['cart_subtotal'] = cart_total_data['subtotal']
    response_data['tax'] = cart_total_data['tax']
    response_data['delivery_charge'] = cart_total_data['delivery_charge']
    response_data['packaging_charge'] = cart_total_data['packaging_charge']
    response_data['grand_total'] = cart_total_data['grand_total']

    item.cart.total = response_data['grand_total']
    item.cart.save()
    
    return JsonResponse(response_data)
@never_cache
def quantity_minus(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    response_data = {}

    if item.quantity > 1:
        item.quantity = F('quantity') - 1
        item.save()
    else:
        response_data['error'] = 'Product quantity must be at least 1'

    item.refresh_from_db()
    
    cart_total_data = calculate_cart_total(item.cart)
    
    response_data['quantity'] = item.quantity
    response_data['item_subtotal'] = float(item.quantity * item.price)
    response_data['cart_subtotal'] = cart_total_data['subtotal']
    response_data['tax'] = cart_total_data['tax']
    response_data['delivery_charge'] = cart_total_data['delivery_charge']
    response_data['packaging_charge'] = cart_total_data['packaging_charge']
    response_data['grand_total'] = cart_total_data['grand_total']

    item.cart.total = response_data['grand_total']
    item.cart.save()

    return JsonResponse(response_data)
 

@never_cache
def cart_remove(request, id):
    if request.method == "POST":
        cart_item = get_object_or_404(CartItem, id=id)
        cart = cart_item.cart

        cart_item.delete()

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
        'available_coupons': Coupon.objects.filter(
            valid_to__gte=timezone.now(),
            active=True
        ).order_by('valid_to')
    }
    return render(request, 'user_side/shop/cart.html', context)



@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    host = request.get_host()
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
    print(grand_total)
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
        print(payment_method)

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    user_address=default_address,
                    payment_method=payment_method,
                    total_amount=cart.total,
                    subtotal=cart_subtotal
                )

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
                    # order.payment_status = 'Completed'
                    order.order_status = 'Processing'
                    order.save()
                    messages.success(request, "Order placed successfully with Cash on Delivery!")
                    return redirect('cart_app:order_confirmation', order_id=order.id)

                elif payment_method == 'paypal':
                        print("ghdh")
                        paypal_checkout = {
                            'business': settings.PAYPAL_RECEIVER_EMAIL,
                            'amount': grand_total,
                            'item_name': f'Order-{uuid.uuid4()}',
                            'invoice': uuid.uuid4(),
                            'currency_code': 'INR',
                            'notify_url': f"http://{host}{reverse('paypal-ipn')}",
                            'return_url': f"http://{host}{reverse('payment-success')}?order_id={order.id}",
                            'cancel_url': f"http://{host}{reverse('payment-failed')}",
                        }

                        paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)

                        context.update({'paypal': paypal_payment})

                        return render(request, 'user_side/payment/payment.html', context)
                       
                elif payment_method == 'wallet':
                    if wallet.balance >= grand_total:
                        wallet.balance -= grand_total
                        wallet.save()

                        Transaction.objects.create(
                            wallet=wallet,
                            amount=-grand_total,  
                            balance_after_transaction=wallet.balance,
                            transaction_type="Debit",
                            description=f"Order #{order.id} payment"
                        )

                        # Process the order
                        cart_items.delete()
                        cart.total = 0
                        cart.save()
                        order.payment_status = 'Completed'
                        order.order_status = 'Processing'
                        order.save()
                        
                        messages.success(request, "Order placed successfully using your wallet!")
                        return redirect('cart_app:order_confirmation', order_id=order.id)
                elif wallet.balance < grand_total:
                    messages.error(request, "there is no balance in wallet please choose another payment.")
                    return redirect('cart_app:checkout')

                else:
                    messages.error(request, "there is no ballence in wallet please choose another payment.")
                    return redirect('cart_app:checkout')

        except Exception as e:
            messages.error(request, f"Error processing order: {str(e)}")
            return redirect('cart_app:checkout')

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


@login_required
def payment_success(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.payment_status = 'Completed'
    order.order_status = 'Processing'
    order.save()

    messages.success(request, "Payment successful! Your order is being processed.")
    return redirect('cart_app:order_confirmation', order_id=order.id)



@login_required
def payment_failed(request):
    messages.error(request, "Payment failed. Please try again.")
    return redirect('cart_app:checkout')






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

@login_required
def paypal_return(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        # Payment successful, mark the order as paid
        order = Order.objects.get(id=request.session.get('order_id'))
        order.status = 'Paid'
        order.save()
        messages.success(request, "Payment successful via PayPal!")
        return redirect('cart_app:order_confirmation', order_id=order.id)
    else:
        messages.error(request, "Payment failed.")
        return redirect('cart_app:checkout')

@login_required
def paypal_cancel(request):
    messages.warning(request, "Payment was cancelled.")
    return redirect('cart_app:checkout')
