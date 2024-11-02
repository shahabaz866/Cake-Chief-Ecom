from django.urls import path
from . import views


app_name = 'user_app'
urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/show/', views.user_show_view, name='user_show'),
    
 

    # path('delete_user_address/<int:id>', views.delete_user_address, name='delete_user_address'),
    # path('replacement_order/<int:id>', views.replacement_order, name='replacement_order'),
    # path('add_address_checkout/', views.add_address_checkout, name='add_address_checkout'),

    ]

