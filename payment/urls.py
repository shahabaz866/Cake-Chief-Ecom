from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('create-payment/', views.create_payment, name='create_payment'),
    path('payment-success/', views.paypal_success, name='payment_success'),
    path('payment-cancel/', views.paypal_cancel, name='payment_cancel'),
    path('paypal-create/', views.paypal_payment, name='paypal_payment'),
]