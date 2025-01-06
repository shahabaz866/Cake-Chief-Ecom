from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet
from decimal import Decimal

@login_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        amount =  Decimal(request.POST.get('amount')) 
        if amount  <= 0:
            messages.error(request, f"{amount} negative index is not possible.")
            
        else:
             
            try:
                if action == 'add':
                    wallet.add_funds(amount)
                    messages.success(request, f"{amount} added to your wallet.")
                elif action == 'deduct':
                    wallet.deduct_funds(amount)
                    messages.success(request, f"{amount} deducted from your wallet.")
                else:
                    messages.error(request, "Invalid action.")
            except ValueError as e:
                 messages.error(request, str(e))
        return redirect('wallet_app:wallet_view')
        


    return render(request, 'user_side/wallet/wallet.html', {'wallet': wallet})
