from django.shortcuts import render, redirect
from django.urls import reverse
from .paypal import create_payment
from django.http import JsonResponse



def paypal_payment(request):
    if request.method == 'POST':
        total = request.POST.get('total')
        currency = 'INR'
        description = 'Cake Shop Payment'
        return_url = request.build_absolute_uri(reverse('paypal_success'))
        cancel_url = request.build_absolute_uri(reverse('paypal_cancel'))

        # Generate PayPal payment URL
        payment_url = create_payment(total, currency, description, return_url, cancel_url)
        if payment_url:
            return redirect(payment_url)
        else:
            return JsonResponse({"error": "Payment creation failed."})

    return render(request, 'user_side/payment/paypal_payment.html')


def paypal_success(request):
    return render(request, 'user_side/payment/payment_success.html')


def paypal_cancel(request):
    return render(request, 'user_side/payment/payment_cancel.html')
