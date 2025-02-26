from django.urls import path,re_path
from . import views
from django.views.decorators.cache import never_cache
from django.shortcuts import render
# @never_cache
# def catch_all_view(request, path=None):
#     return render(request, 'user_side/error/error_page.html')

app_name= 'wallet_app'


urlpatterns = [
    path('wallet/', views.wallet_view, name='wallet_view'),
    
    # path('wallet/add/', views.add_funds, name='add_funds'),
    # path('wallet/deduct/', views.deduct_funds, name='deduct_funds'),
    # re_path(r'^.*$', catch_all_view),
]