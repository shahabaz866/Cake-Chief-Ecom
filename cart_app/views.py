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
from django.dispatch import receiver
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.ipn.signals import valid_ipn_received  
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.http import JsonResponse
from django.utils import timezone 





def calculate_cart_total(cart):
    cart_items = CartItem.objects.filter(cart=cart).select_related('variant')
    cart=  Cart.objects.get(user=cart.user)

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
    try:       
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
                messages.success(request, "Item added to cart.")
                cart_count = CartItem.objects.filter(cart=cart).count()
                request.session['cart_count'] = cart_count 

                return redirect("cart_app:cart")
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
def quantity_plus(request, item_id):
    try:        
            item = get_object_or_404(CartItem, pk=item_id)
            cart = Cart.objects.get(user=request.user)  
            response_data = {}
            
            if item.quantity < 10:
                if item.quantity + 1 <= item.variant.stock:
                    item.quantity = F('quantity') + 1
                    item.save()
                    item.refresh_from_db() 
                
                else:
                    response_data['error'] = 'Not enough stock available'
                    return JsonResponse(response_data)
            else:
                response_data['error'] = 'Each customer is limited to a maximum purchase quantity of 10 units'
                return JsonResponse(response_data)
            
            cart_total_data = calculate_cart_total(item.cart)
            
            response_data.update({
                'quantity': item.quantity,
                'item_subtotal': float(item.quantity * item.price),
                'cart_subtotal': cart_total_data['subtotal'],
                'tax': cart_total_data['tax'],
                'delivery_charge': cart_total_data['delivery_charge'],
                'packaging_charge': cart_total_data['packaging_charge'],
                'grand_total': cart_total_data['grand_total']
            })

            item.cart.total = response_data['grand_total']
            item.cart.save()
            
            return JsonResponse(response_data)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
def quantity_minus(request, item_id):
    try:        
        item = get_object_or_404(CartItem, pk=item_id)
        cart = Cart.objects.get(user=request.user)
        response_data = {}

        if item.quantity > 1:
            item.quantity = F('quantity') - 1
            item.save()
        else:
            response_data['error'] = 'Product quantity must be at least 1'

        item.refresh_from_db()

        # Check if coupon discount is greater than the cart total
        refresh_page = False
        if cart.coupon and cart.total < cart.coupon.discount:
            cart.coupon = None
            cart.save()
            refresh_page = True  # Flag to refresh the page

        cart_total_data = calculate_cart_total(item.cart)

        response_data['quantity'] = item.quantity
        response_data['item_subtotal'] = float(item.quantity * item.price)
        response_data['cart_subtotal'] = cart_total_data['subtotal']
        response_data['tax'] = cart_total_data['tax']
        response_data['delivery_charge'] = cart_total_data['delivery_charge']
        response_data['packaging_charge'] = cart_total_data['packaging_charge']
        response_data['grand_total'] = cart_total_data['grand_total']
        response_data['coupon_applied'] = bool(item.cart.coupon)
        response_data['discount'] = cart_total_data['discount'] if item.cart.coupon else 0
        response_data['refresh_page'] = refresh_page  # Send flag to the frontend

        item.cart.total = response_data['grand_total']
        item.cart.save()

        return JsonResponse(response_data)

    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


@never_cache
def cart_remove(request, id):
    try:
                if request.method == "POST":
                    cart_item = get_object_or_404(CartItem, id=id)
                    cart = cart_item.cart

                    cart_item.delete()

                    cart.total = sum(item.quantity * item.price for item in CartItem.objects.filter(cart=cart))

                if cart.coupon:
                    if cart.total < cart.coupon.discount:
                        cart.coupon = None

                    cart.save()
                cart_count = CartItem.objects.filter(cart=cart).count()
                if cart_count == 0:
                    request.session.pop('cart_count', None)
                else:
                    request.session['cart_count'] = cart_count
                return JsonResponse({
                "success": True,
                "cart_total_items": cart_count,
                "cart_subtotal": cart.total,
                "grand_total": cart.total ,  
            })
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    except Exception as e:
        
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@never_cache
def refresh_coupon(request):
    cart = Cart.objects.get(user=request.user)  
    


    discount = cart.get_discount_amount()  
    grand_total = cart.get_total_with_discount()  
    return JsonResponse({
        'coupon_applied': bool(cart.coupon),
        'discount': discount,
        'grand_total': grand_total
    })

@login_required(login_url='login')
@never_cache
def cart_view(request):
    try:        
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')

            totals = calculate_cart_total(cart)

           

            context = {}

            if cart_items:
                first_item_category = cart_items[0].product.category
                related_products = Product.objects.filter(
                    category=first_item_category,
                    is_active=True
                ).exclude(
                    id__in=[item.product.id for item in cart_items]
                )[:20]  
            else:
                related_products = Product.objects.filter(
                    is_active=True
                ).order_by('-created_at')[:4]
            
            context['related_products'] = related_products

            valid_coupon = Coupon.objects.filter(
                valid_to__gte=timezone.now(),
                active=True
            ).exclude(discount__gt=totals['subtotal']).order_by('valid_to')

            context.update({
                'cart_items': cart_items,
                'cart_subtotal': totals['subtotal'],
                'tax': totals['tax'],
                'discount': totals['discount'],
                'delivery_charge': totals['delivery_charge'],
                'packaging_charge': totals['packaging_charge'],
                'grand_total': totals['grand_total'],
                'coupon': cart.coupon,
                'available_coupons': valid_coupon,
            })

            return render(request, 'user_side/shop/cart.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
            
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
import requests

def get_usd_exchange_rate():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/INR")  
        data = response.json()
        return data['rates']['USD']  
    except Exception as e:
        return 0.012 



@never_cache
@login_required(login_url='login')
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)

    try:        

                if request.user.username == "demo_user":
                    messages.warning(request, "Demo users cannot place orders. Please log in with a real account.")
                    return redirect('cart_app:cart')

                cart = get_object_or_404(Cart, user=request.user)
                cart_items = CartItem.objects.filter(cart=cart).select_related('product', 'variant')
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                host = request.get_host()

                if not cart_items or cart.total <= 0:
                    messages.warning(request, "Your cart is empty!")
                    return redirect('cart_app:cart')

                for item in cart_items:
                    if item.variant.stock < item.quantity:
                        messages.error(request, f"Insufficient stock for {item.product.title}. Reduce quantity or remove the item.")
                        return redirect('cart_app:cart')

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

                    
                    if payment_method in ['cod', 'paypal', 'wallet']:

                        if payment_method == 'cod' and cart.total > 1000:
                            messages.error(request, "Cash on Delivery (COD) is not available for orders above 1000. Please choose another payment method.")
                            return redirect('cart_app:checkout')
                        
                        order = Order.objects.create(
                            user=user,
                            user_address=default_address,
                            payment_method=payment_method,
                            total_amount=grand_total,
                            subtotal=cart_subtotal,
                            tax=cart.tax,  
                            delivery_charge=cart.delivery_charge, 
                            packaging_charge=cart.packaging_charge, 
                            discount=discount,  
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
                            if cart.total < 1000:
                                cart_items.delete()
                                cart.total = 0
                                cart.save()
                                order.payment_status = 'Pending'
                                order.order_status = 'PROCESSING'
                                order.save()

                                messages.success(request, "Order placed successfully with Cash on Delivery!")
                                return redirect('cart_app:order_confirmation', order_id=order.id)

                            messages.error(request, "Cash on Delivery (COD) is not available for orders above 1000. Please choose another payment method.")
                            return redirect('cart_app:checkout')

                        elif payment_method == 'paypal':
                            usd_rate = Decimal(str(get_usd_exchange_rate()))  
                            total_in_usd = (grand_total * usd_rate).quantize(Decimal('0.01'))
                            if total_in_usd <= 0:
                                messages.error(request, "Conversion failed. Please try again.")
                                return redirect('cart_app:checkout')

                            paypal_checkout = {
                                'business': settings.PAYPAL_RECEIVER_EMAIL,
                                'amount': total_in_usd,  
                                'invoice': uuid.uuid4(),
                                'item_name': 'Order Payment',
                                'currency_code': 'USD',  
                                'notify_url': f"http://{host}{reverse('paypal-ipn')}",
                                'return_url': f"http://{host}{reverse('cart_app:payment_success')}?order_id={order.id}",
                            }
                            paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)

                            context = {
                                'paypal': paypal_payment,
                                'cart_items': cart_items,
                                'cart_subtotal': cart_subtotal,
                                'total': total_in_usd,  
                                'paypal_checkout': paypal_checkout,
                                'order': order,
                            }
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

                                cart_items.delete()
                                cart.total = 0
                                cart.save()
                                order.payment_status = 'Completed'
                                order.order_status = 'PROCESSING'
                                order.save()

                                messages.success(request, "Order placed successfully using your wallet!")
                                return redirect('cart_app:order_confirmation', order_id=order.id)
                            else:
                                messages.error(request, f"Insufficient balance in your wallet! Your current balance is ₹{wallet.balance:.2f}. Please add funds or choose another payment method.")
                                return redirect('cart_app:checkout')

                    else:
                        messages.error(request, "Please select a valid payment method!")
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
                    'wallel_balance': wallet.balance,
                }

                return render(request, 'user_side/shop/checkout.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    
    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



@login_required(login_url='login')
def payment_success(request):
    order_id = request.GET.get('order_id')
    try:
        order = Order.objects.get(id=order_id)
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items.delete()
        cart.total = 0
        cart.save()
        
        order.payment_status = 'Completed'
        order.order_status = 'PROCESSING'
        order.save()

        messages.success(request, "Payment successful! Your order has been confirmed.")
        return redirect('cart_app:order_confirmation', order_id=order.id)
    except Order.DoesNotExist:
        messages.error(request, "Order not found!")
        return redirect('cart_app:cart')
@login_required(login_url='login')
def payment_failed(request):
    messages.error(request, "Payment failed! Please try again.")
    return redirect('cart_app:checkout')

@receiver(valid_ipn_received)
def paypal_payment_received(sender, **kwargs):
    ipn_obj = sender
    
    if ipn_obj.payment_status == ST_PP_COMPLETED:
       
        try:
            order = Order.objects.get(id=ipn_obj.invoice)
            
           
            if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
                
                return
                
            if ipn_obj.mc_gross == order.total_amount and ipn_obj.mc_currency == 'INR':
              
                order.payment_status = 'Completed'
                order.order_status = 'PROCESSING'
                order.save()
        except Order.DoesNotExist:
            pass




def get_primary_mobile_number(user):
        primary_contact = UserContact.objects.filter(user=user, contact_type='PRIMARY', is_active=True).first()
        return primary_contact.mobile_number if primary_contact else None


@login_required(login_url='login')
@never_cache
def order_confirmation(request, order_id):
    try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            order_items = order.items.all().select_related('product', 'variants') 
            cart = Cart.objects.get(user=request.user)

            
            default_address = Address.objects.filter(user=request.user, is_default=True).first()
            if not default_address:
                default_address = Address.objects.filter(user=request.user).first()

        
            primary_mobile_number = get_primary_mobile_number(request.user)
            cart_count = CartItem.objects.filter(cart=cart).count()
            if cart_count >0:
                request.session.pop('cart_count', 0)
            else:
                request.session['cart_count'] = cart_count


            context = {
                'order': order,
                'order_items': order_items,
                'payment_status': order.get_payment_status_display(),
                'default_address': default_address,
                'primary_mobile_number': primary_mobile_number,
            }

            return render(request, 'user_side/order/order_confirm.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
def apply_coupon(request):
    try:        
        if request.method == 'POST':
            coupon_code = request.POST.get('coupon_code', '').strip()
            cart = get_object_or_404(Cart, user=request.user)
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True, valid_to__gte=timezone.now())
                cart.coupon = coupon
                cart.save()
                messages.success(request, format_html("Coupon '{}' applied successfully!", coupon.code))
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid or expired coupon.")
        return redirect('cart_app:cart')
    
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

def remove_coupon(request):
    try:        
        cart = Cart.objects.get(user=request.user)
        cart.coupon = None
        cart.save()
        return redirect('cart_app:cart')  
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@login_required(login_url='login')
def paypal_return(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        order = Order.objects.get(id=request.session.get('order_id'))
        order.status = 'Paid'
        order.save()
        messages.success(request, "Payment successful via PayPal!")
        return redirect('cart_app:order_confirmation', order_id=order.id)
    else:
        messages.error(request, "Payment failed.")
        return redirect('cart_app:checkout')

@login_required(login_url='login')
def paypal_cancel(request):
    messages.warning(request, "Payment was cancelled.")
    return redirect('cart_app:checkout')
