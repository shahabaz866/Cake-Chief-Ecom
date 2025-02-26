from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Order,OrderItem
from cart_app.models import Cart, CartItem
from  user_app.models import Address,UserContact
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from user_app.models import Address, UserContact
from django.views.decorators.csrf import csrf_exempt
from .constants import PaymentStatus
from wallet_app.models import Wallet, Transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import tempfile






def get_primary_mobile_number(user):
        primary_contact = UserContact.objects.filter(user=user, contact_type='PRIMARY', is_active=True).first()
        return primary_contact.mobile_number if primary_contact else None


@never_cache
@login_required(login_url='login')
def order_list(request):
    try: 
            
            orders = Order.objects.filter(user=request.user).order_by('-created_at')
            pending_orders_count = orders.filter(order_status='PROCESSING').count()
            delivery_orders_count = orders.filter(order_status='DELIVERED').count()


            orders_with_items = []
            for order in orders:
                items = OrderItem.objects.filter(order=order)
                
                
                orders_with_items.append({
                    'order': order,
                    'items': items,
                })
            
            context = {
                'orders_with_items': orders_with_items,
                'pending_orders_count': pending_orders_count,
                'delivery_orders_count': delivery_orders_count,

                
            }
            return render(request, 'user_side/order/order_list.html', context)
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
    

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseServerError

@never_cache
@login_required(login_url='login')
def order_view(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        cart = get_object_or_404(Cart, user=request.user)
        order_items = OrderItem.objects.filter(order=order)
        default_address = Address.objects.filter(user=request.user, is_default=True).first()
        primary_mobile_number = get_primary_mobile_number(request.user)

        context = {
            'cart': cart,
            'order': order,
            'default_address': default_address,
            'primary_mobile_number': primary_mobile_number,
            'order_items': order_items,
        }
        return render(request, 'user_side/order/order_view.html', context)

    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

        


@login_required(login_url='login')
@never_cache
def generate_invoice(request, order_id):
    try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            order_items = OrderItem.objects.filter(order=order)
            default_address = Address.objects.filter(user=request.user, is_default=True).first()
            cart = Cart.objects.get(user=request.user)
            order.discount

            context = {
                'cart': cart,
                'order': order,
                'order_items': order_items,
                'default_address': default_address,
            }

            invoice_html = render_to_string('user_side/order/invoice.html', context)

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="CakeChief_{order.id}.pdf"'

            HTML(string=invoice_html).write_pdf(response)

            return response
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


@never_cache
@login_required(login_url='login')
def cancel_order(request, order_id):
    try:
        order = get_object_or_404(Order.objects.select_related('user'), id=order_id, user=request.user)

        if request.method == 'POST':
            cancellation_reason = request.POST.get('cancellation_reason', '').strip()

            if order.order_status not in ['PROCESSING', 'SHIPPED']:
                messages.error(request, 'This order cannot be cancelled.')
                return redirect('order_app:order_detail', order_id=order.id)

            with transaction.atomic():
                order.cancellation_reason = cancellation_reason

                # Restore stock for each item in the order
                for order_item in order.items.select_related('variants').all():
                    variant = order_item.variants
                    variant.stock += order_item.quantity
                    variant.save()

                # Refund logic for Wallet and PayPal
                if order.payment_method in ['wallet', 'paypal']:
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += order.total_amount
                    wallet.save()

                    # Record the transaction
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=order.total_amount,
                        balance_after_transaction=wallet.balance,
                        transaction_type='CREDIT',
                        description=f"Order #{order.id} payment refund"
                    )

                    order.payment_status = 'Refunded'

                order.order_status = 'CANCELLED'
                order.save()

            messages.success(request, f'Order #{order.id} has been cancelled. Stock restored and amount refunded (if applicable).')
            return redirect('order_app:order_detail', order_id=order.id)

    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@csrf_exempt
def update_order_status(request):
    try:
        if request.method == 'POST':
            order_id = request.POST.get('order_id')
            new_order_status = request.POST.get('new_order_status')
            new_payment_status = request.POST.get('new_payment_status')

            order = get_object_or_404(Order, id=order_id)

            with transaction.atomic():
                if new_order_status == 'CANCELLED' and order.payment_method in ['paypal', 'wallet']:
                    # Refund logic for Wallet and PayPal
                    wallet, created = Wallet.objects.get_or_create(user=order.user)
                    wallet.balance += order.total_amount
                    wallet.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        amount=order.total_amount,
                        balance_after_transaction=wallet.balance,
                        transaction_type='CREDIT',
                        description=f"Order #{order.id} payment refund"
                    )

                    order.payment_status = 'Refunded'

                if new_order_status and new_order_status != order.order_status:
                    order.order_status = new_order_status
                    messages.success(request, f"Order status updated to {new_order_status}")

                if new_payment_status and new_payment_status != order.payment_status:
                    order.payment_status = new_payment_status
                    messages.success(request, f"Payment status updated to {new_payment_status}")

                order.save()

            return redirect('order_app:admin_order_list')

    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
def update_payment_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_payment_status = request.POST.get('new_payment_status')
        order = get_object_or_404(Order, id=order_id)
        order.payment_status = new_payment_status
        order.save()
        messages.success(request, f"Order #{order_id} payment status updated to {new_payment_status}.")
    return redirect('order_app:admin_order_list')



@never_cache
@staff_member_required(login_url='admin:login')
def admin_order_list(request):
    try:
            order_list = Order.objects.all().order_by('-id')
            order_status_choices = Order.ORDER_STATUS_CHOICES
            payment_status_choices = PaymentStatus.CHOICES

            total_count = order_list.count()
            pending_count = order_list.filter(order_status='PENDING').count()
            delivered_count = order_list.filter(order_status='DELIVERED').count()
            cancelled_count = order_list.filter(order_status='CANCELLED').count()

            search_query = request.GET.get('search', '')
            if search_query:
                order_list = order_list.filter(
                    Q(id__icontains=search_query) |  
                    Q(user__email__icontains=search_query) | 
                    Q(user__username__icontains=search_query) | 
                    Q(order_status__icontains=search_query)
                )

            order_status_filter = request.GET.get('order_status', '')
            if order_status_filter:
                order_list = order_list.filter(order_status=order_status_filter)

            payment_status_filter = request.GET.get('payment_status', '')
            if payment_status_filter:
                order_list = order_list.filter(payment_status=payment_status_filter)

            items_per_page = 15 
            paginator = Paginator(order_list, items_per_page)

            page = request.GET.get('page')
            try:
                orders = paginator.page(page)
            except PageNotAnInteger:
                orders = paginator.page(1)
            except EmptyPage:
                orders = paginator.page(paginator.num_pages)

            context = {
                'orders': orders,  
                'search_query': search_query,
                'order_status_filter': order_status_filter,
                'payment_status_filter': payment_status_filter,
                'status_choices': order_status_choices,
                'payment_status_choices': payment_status_choices,
                'total_count': total_count,
                'pending_count': pending_count,
                'delivered_count': delivered_count,
                'cancelled_count': cancelled_count,
            }

            return render(request, 'admin/order_management/order_list.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
@staff_member_required(login_url='admin:login')
def admin_order_detail(request, order_id):
    try:
       
        order = Order.objects.get(id=order_id)
        order_items = order.items.all()
      
        order_status_choices = Order.ORDER_STATUS_CHOICES
        payment_status_choices = PaymentStatus.CHOICES
        
        
        context = {
            'order': order,
            'order_items': order_items,
            'status_choices': order_status_choices,
            'payment_status_choices': payment_status_choices,
        }
        
        return render(request, 'admin/order_management/order_detail.html', context)
        
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



# def update_order_status(request):
#     if request.method == 'POST':
#         order_id = request.POST.get('order_id')
#         new_status = request.POST.get('new_order_status')

#         if not new_status: 
#             messages.error(request, "Order status cannot be empty.")
#             return redirect('order_app:admin_order_list')

#         order = get_object_or_404(Order, id=order_id)
#         order.order_status = new_status

#         if new_status == 'CANCELLED' and order.payment_method in ['PayPal', 'Wallet']:
#             order.payment_status = 'Refunded'

#         order.save()
#         messages.success(request, "Order status updated successfully.")

#     return redirect('order_app:admin_order_list')


@login_required(login_url='login')
def delete_order(request, order_id):
    try:        
            order = get_object_or_404(Order, id=order_id)
            order.delete()
            messages.success(request, f"Order #{order_id} has been deleted.")
            return redirect('order_app:admin_order_list')
    except Http404:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
def success_view(request):
    return render(request, 'user_side/order/order_view.html')

@login_required(login_url='login')
@never_cache
def track_order(request):
    try:        
            order = None
            order_id = request.GET.get('order_id')
            
            if order_id and order_id.isdigit():  # ✅ Check if order_id is numeric
                order_id = int(order_id) 
                try:
                    if request.user.is_authenticated:
                        order = Order.objects.get(id=order_id, user=request.user)
                    else:
                        order = Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    messages.error(request, 'Order not found')
            
            return render(request, 'user_side/order/Order_tracking.html', {
                'order': order
            })
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            print(e)
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
    
    
