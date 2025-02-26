from django.urls import path, re_path
from . import views
from django.views.decorators.cache import never_cache
from django.shortcuts import render
# @never_cache
# def catch_all_view(request, path=None):
#     return render(request, 'user_side/error/error_page.html')

app_name = 'user_app'

urlpatterns = [
    path('profile/', views.user_show_view, name='user_show'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('addresses/', views.address_list_view, name='address_list'),
    path('address/add/', views.add_address_view, name='add_address'),  # For adding an address
    path('address/edit/<int:address_id>/', views.edit_address_view, name='edit_address'),  # For editing an address
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    # re_path(r'^.*$', catch_all_view),
]
