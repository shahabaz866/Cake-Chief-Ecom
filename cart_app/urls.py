from django.urls import path,include,re_path
from . import views
from django.shortcuts import render
from django.views.decorators.cache import never_cache


app_name = 'cart_app'
@never_cache
def catch_all_view(request, path=None):
    return render(request, 'user_side/error/error_page.html',{'error_code': 404},status=404)

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    
    path('add_to_cart/<int:id>/',views.add_to_cart,name='add_cart'),

    path('quantity_plus/<int:item_id>/', views.quantity_plus, name='quantity_plus'),

    path('quantity_minus/<int:item_id>/', views.quantity_minus, name='quantity_minus'),


    path("remove_from_cart/<int:id>/", views.cart_remove, name="remove_from_cart"),

    path('checkout/', views.checkout_view, name='checkout'),
    
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    path('refresh-coupon/', views.refresh_coupon, name='refresh_coupon'),

    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
   
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    re_path(r'^.*$', catch_all_view),

]

