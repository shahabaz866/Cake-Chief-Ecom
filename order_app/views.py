from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Order,OrderItem
from cart_app.models import Cart, CartItem
from  user_app.models import Address,UserContact
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from user_app.models import Address, UserContact


def get_primary_mobile_number(user):
        primary_contact = UserContact.objects.filter(user=user, contact_type='PRIMARY', is_active=True).first()
        return primary_contact.mobile_number if primary_contact else None



@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
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

    
    # Get the default address
    default_address = Address.objects.filter(user=request.user, is_default=True).first()

    # Get the primary mobile number
    primary_mobile_number = get_primary_mobile_number(request.user)
    print(primary_mobile_number ,"fds")
    print(default_address,"ggf")

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
                product.stock += order_item.quantity  # Restore the stock by adding the order quantity
                product.save()  # Save the updated product

            order.save()  # Save the canceled order
            messages.success(request, f'Order #{order_id} has been cancelled and stock has been restored.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
        return redirect('order_app:order_list')

    context = {
        'order_id': order_id,
        'order': order  
    }

    return render(request, 'user_side/order/cancel_confirmation.html', context)

    

@login_required
def admin_order_list(request):
    # Get all orders ordered by creation date
    order_list = Order.objects.all().order_by('id')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        order_list = order_list.filter(
            Q(order_number__icontains=search_query) |
            Q(customer__email__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(order_status__icontains=search_query)
        )
    
    # Handle status filter
    status_filter = request.GET.get('order_status', '')
    if status_filter:
        order_list = order_list.filter(order_status=status_filter)
    
    # Pagination
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
        'status_choices': Order.ORDER_STATUS_CHOICES,
    }
    
    return render(request, 'admin/order_management/order_list.html', context)




def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')

        try:
            order = Order.objects.get(id=order_id)
            order.order_status = new_status  # Update status to "processing"
            order.save()

            messages.success(request, f"Order #{order_id} status updated to {new_status}.")

            return redirect('order_app:admin_order_list')

        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('admin_order_list') 

    # If it's not a POST request, return an error message
    messages.error(request, "Invalid request.")
    return redirect('admin_order_list')  # Redirect to a fallback page

def success_view(request):
    return render(request, 'user_side/order/order_view.html')

# @login_required
# def status_page(request,order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)

#     order_items = order.orderitem_set.all().select_related('product')

#     default_address = Address.objects.filter(user=request.user, is_default=True).first()

#     primary_mobile_number = get_primary_mobile_number(request.user)

#     total_amount = sum(item.quantity * item.price for item in order_items)
    
  
#     order.total_amount = total_amount
#     order.save()

#     if not default_address:
#         default_address = Address.objects.filter(user=request.user).first()
        
#     context = {
#         'order': order,
#         'order_items': order_items,
        
#         'payment_status': 'Paid' if order.is_paid else 'Pending',
#         'default_address': default_address,
#         'primary_mobile_number': primary_mobile_number,

#     }

#     return render(request,'user_side/order/status_page.html',context)