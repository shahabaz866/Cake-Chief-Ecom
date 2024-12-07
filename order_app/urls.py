from django.urls import path
from . import views

app_name = 'order_app'

urlpatterns = [
  
    # path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order/', views.order_list, name='order_list'),
    path('orders_view/<int:order_id>/', views.order_view, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('admin/orders/', views.admin_order_list, name='admin_order_list'),
    path('update-order-status/', views.update_order_status, name='update_order_status'),
    path('success/', views.success_view, name='success'),

    # path('status_page/<int:order_id>/',views.status_page,name='status_page'),


]