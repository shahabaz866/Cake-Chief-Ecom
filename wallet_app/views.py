from django.http import JsonResponse
from .models import Wallet, Transaction
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages


def wallet_balance(request):
    if request.user.username == 'demo_user':
        return JsonResponse({'error': 'Access denied for demo user'}, status=403)
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    return JsonResponse({'balance': wallet.balance})


@login_required
def wallet_view(request):
    if request.user.username == 'demo_user':
        messages.error(request, 'Access denied for demo user.')
        return redirect('home') 

    # Fetch wallet and transactions
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = Transaction.objects.filter(wallet=wallet).order_by('-timestamp')

    return render(request, 'user_side/wallet/wallet.html', {
        'wallet': wallet,
        'transactions': transactions
    })
