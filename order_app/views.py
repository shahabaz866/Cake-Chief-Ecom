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




def get_primary_mobile_number(user):
        primary_contact = UserContact.objects.filter(user=user, contact_type='PRIMARY', is_active=True).first()
        return primary_contact.mobile_number if primary_contact else None



@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    pending_orders_count = orders.filter(order_status='PENDING').count()
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

@login_required
def order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    order_items = OrderItem.objects.filter(order=order)
 
    default_address = Address.objects.filter(user=request.user, is_default=True).first()   

    primary_mobile_number = get_primary_mobile_number(request.user)
 

    context = {
        'order': order,
        'default_address': default_address,
        'primary_mobile_number': primary_mobile_number,
        'order_items': order_items,
    }

    return render(request, 'user_side/order/order_view.html', context)




@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        if order.order_status in ['PROCESSING', 'SHIPPED']:
           
            order.order_status = 'CANCELLED'

           
            for order_item in order.orderitem_set.all():
                product = order_item.product
                product.stock += order_item.quantity  
                product.save() 

            order.save() 
            messages.success(request, f'Order #{order_id} has been cancelled and stock has been restored.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
        return redirect('order_app:order_list')

    context = {
        'order_id': order_id,
        'order': order  
    }

    return render(request, 'user_side/order/cancel_confirmation.html', context)

    
@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_order_status = request.POST.get('new_order_status')
        new_payment_status = request.POST.get('new_payment_status')

        order = get_object_or_404(Order, id=order_id)

        if new_order_status and new_order_status != order.order_status:
            order.order_status = new_order_status
            messages.success(request, f"Order status updated to {new_order_status}")

        # Update payment status
        if new_payment_status and new_payment_status != order.payment_status:
            order.payment_status = new_payment_status
            messages.success(request, f"Payment status updated to {new_payment_status}")

        # Save changes
        order.save()

    return redirect('order_app:order_management')

def update_payment_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_payment_status = request.POST.get('new_payment_status')
        order = get_object_or_404(Order, id=order_id)
        order.payment_status = new_payment_status
        order.save()
        messages.success(request, f"Order #{order_id} payment status updated to {new_payment_status}.")
    return redirect('order_app:admin_order_list')

@login_required
def admin_order_list(request):
    order_list = Order.objects.all().order_by('-id')

    order_status_choices = Order.ORDER_STATUS_CHOICES
    payment_status_choices = PaymentStatus.CHOICES

    search_query = request.GET.get('search', '')
    if search_query:
        order_list = order_list.filter(
            Q(id__icontains=search_query) |  
            Q(user__email__icontains=search_query) | 
            Q(user__username__icontains=search_query) | 
            Q(order_status__icontains=search_query)
        )
    

    status_filter = request.GET.get('order_status', '')
    if status_filter:
        order_list = order_list.filter(order_status=status_filter)


    payment_status_filter = request.GET.get('payment_status', '')
    if payment_status_filter:
        order_list = order_list.filter(payment_status=payment_status_filter)

    page = request.GET.get('page', 1)
    paginator = Paginator(order_list, 20)
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    context = {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
        'payment_status_filter': payment_status_filter,
        'status_choices': order_status_choices,
        'payment_status_choices': payment_status_choices,
    }
    
    return render(request, 'admin/order_management/order_list.html', context)



def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_order_status')

        if not new_status:  # Check for empty values
            messages.error(request, "Order status cannot be empty.")
            return redirect('order_app:admin_order_list')

        order = get_object_or_404(Order, id=order_id)
        order.order_status = new_status
        order.save()
        messages.success(request, "Order status updated successfully.")

    return redirect('order_app:admin_order_list')

@login_required
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    messages.success(request, f"Order #{order_id} has been deleted.")
    return redirect('order_app:admin_order_list')

def success_view(request):
    return render(request, 'user_side/order/order_view.html')
