from django.urls import path
from . import views

urlpatterns = [
    # Example path
    path('', views.order_view, name='order_view'),  # Replace with your actual view
]