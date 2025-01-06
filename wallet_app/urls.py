from django.urls import path
from . import views

app_name= 'wallet_app'

urlpatterns = [
    path('wallet/', views.wallet_view, name='wallet_view'),
    # path('wallet/add/', views.add_funds, name='add_funds'),
    # path('wallet/deduct/', views.deduct_funds, name='deduct_funds'),
]