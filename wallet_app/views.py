from django.http import JsonResponse
from .models import Wallet, Transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from .models import Wallet, Transaction
from order_app.models import Order
from django.shortcuts import get_object_or_404
@never_cache
@login_required(login_url='login')
def wallet_balance(request):
    if request.user.username == 'demo_user':
        return JsonResponse({'error': 'Access denied for demo user'}, status=403)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return JsonResponse({'balance': wallet.balance})

@never_cache
@login_required(login_url='login')
def wallet_view(request):
    if request.user.username == 'demo_user':
        messages.error(request, 'Access denied for demo user.')
        return redirect('home') 

    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-timestamp')

    return render(request, 'user_side/wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })



@never_cache
@login_required(login_url='login')
def refund(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.order_status == 'CANCELLED' and order.payment_method in ['PayPal', 'Wallet']:
        if order.payment_status != 'Refunded':
            wallet, created = Wallet.objects.get_or_create(user=request.user)

            wallet.balance += order.total_amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=order.total_amount,
                transaction_type='Refund',
                description=f'Refund for Order #{order.id}'
            )

            order.payment_status = 'Refunded'
            order.save()

            return JsonResponse({'message': 'Refund successful', 'new_balance': wallet.balance})
        else:
            return JsonResponse({'error': 'Order already refunded'}, status=400)

    return JsonResponse({'error': 'Refund not applicable'}, status=400)

