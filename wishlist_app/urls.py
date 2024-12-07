from django.urls import path
from . import views
app_name='wishlist_app'

urlpatterns = [
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/<str:variant_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/<int:variant_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]