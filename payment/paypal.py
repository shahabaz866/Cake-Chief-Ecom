import paypalrestsdk
from django.conf import settings


paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,  
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})


def create_payment(total, currency, description, return_url, cancel_url):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
        "transactions": [{
            "amount": {
                "total": str(total),
                "currency": currency
            },
            "description": description
        }]
    })

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return link.href  
    else:
        return None  
