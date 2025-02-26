from django.urls import path,re_path
from . import views
from django.views.decorators.cache import never_cache
from django.shortcuts import render

@never_cache
def catch_all_view(request, path=None):
    return render(request, 'user_side/error/error_page.html')


app_name = 'order_app'

urlpatterns = [
  
    path('order/', views.order_list, name='order_list'),
    path('orders_view/<int:order_id>/', views.order_view, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
    path('orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('update-payment-status/', views.update_payment_status, name='update_payment_status'),
    path('success/', views.success_view, name='success'),
    path('update-order-status/', views.update_order_status, name='update_order_status'),
    path('delete-order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('order/<int:order_id>/invoice/', views.generate_invoice, name='generate_invoice'),
    # path('cancel_order/', views.cancel_view, name='cancel_order'),
    path('track_order/', views.track_order, name='track_order'),
    re_path(r'^.*$', catch_all_view),



]

