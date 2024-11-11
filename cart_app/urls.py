from django.urls import path
from . import views
app_name = 'cart_app'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    
    path('add_to_cart/<int:id>/',views.add_to_cart,name='add_cart'),

    path('quantity_plus/<int:item_id>/', views.quantity_plus, name='quantity_plus'),

    path('quantity_minus/<int:item_id>/', views.quantity_minus, name='quantity_minus'),


    path("remove_from_cart/<int:id>/", views.cart_remove, name="remove_from_cart"),

    path('checkout/', views.checkout_view, name='checkout'),
    
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    
    


]
