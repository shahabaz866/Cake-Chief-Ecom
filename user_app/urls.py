from django.urls import path
from . import views
app_name = 'user_profile'
urlpatterns = [
    path('profile/', views.userProfile, name='profile'),
    # path('user_address/', views.user_address, name='user_address'),
    # path('add_user_address/', views.add_user_address, name='add_user_address'),
    # path('add_user_mobile/', views.add_user_mobile, name='add_user_mobile'),
    # path('add_user_firstname/', views.add_user_firstname, name='add_user_firstname'),
    # path('add_user_lastname/', views.add_user_lastname, name='add_user_lastname'),
    # path('edit_user_mobile/', views.edit_user_mobile, name='edit_user_mobile'),
    # path('edit_user_firstname/', views.edit_user_firstname, name='edit_user_firstname'),
    # path('edit_user_lastname/', views.edit_user_lastname, name='edit_user_lastname'),
    # path('delete_user_address/<int:id>', views.delete_user_address, name='delete_user_address'),
    # path('replacement_order/<int:id>', views.replacement_order, name='replacement_order'),
    # path('add_address_checkout/', views.add_address_checkout, name='add_address_checkout'),

    ]