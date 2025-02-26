from django.urls import path,re_path
from . import views
from django.views.decorators.cache import never_cache
from django.shortcuts import render
@never_cache
def catch_all_view(request, path=None):
    return render(request, 'user_side/error/error_page.html')   
app_name='wishlist_app'

urlpatterns = [
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/<int:variant_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove/<int:wishlist_item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    re_path(r'^.*$', catch_all_view),
]