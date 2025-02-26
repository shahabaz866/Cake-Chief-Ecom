
from django.urls import path,re_path
from . import views
from django.shortcuts import render
from django.views.decorators.cache import never_cache



@never_cache
def catch_all_view(request, path=None):
    return render(request, 'user_side/error/error_page.html',{'error_code': 404},status=404)

urlpatterns = [

    path('', views.dashboard, name='dashboard'), 
    path('user_management/', views.userManagement, name='user_management'),
    path('product_list/',views.product_list, name='product_list'),
    path('variant/<int:variant_id>/delete/', views.delete_variant, name='delete_variant'),
    path('add_product/',views.add_products, name='add_products'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('unblock-product/<int:product_id>/', views.unblock_product, name='unblock_product'),
    path('users/block/<int:user_id>/', views.block_user, name='block_user'),
    path('users/unblock/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('category_list/',views.category_list, name='category_list'),
    path('add_category/',views.add_category, name='add_category'),
    path('edit_category/<int:id>/', views.edit_category, name='edit_category'), 
    path('delete_category/<int:id>/', views.delete_category, name='delete_category'),
    path('unblock_category/<int:id>/', views.unblock_category, name='unblock_category'),

    path('flavour_list/',views.flavour_list, name='flavour_list'),
    path('add_flavour/',views.add_flavour, name='add_flavour'),
    path('edit_flavour/<int:id>/', views.edit_flavour, name='edit_flavour'), 
    path('delete_flavour/<int:id>/', views.delete_flavour, name='delete_flavour'),
    path('unblock_flavour/<int:id>/', views.unblock_flavour, name='unblock_flavour'),


    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/add/', views.coupon_add, name='coupon_add'),
    path('coupons/edit/<int:pk>/', views.coupon_edit, name='coupon_edit'),
    path('coupons/delete/<int:pk>/', views.coupon_delete, name='coupon_delete'),

path('admin/product/<int:product_id>/', views.admin_product_detail, name='admin_product_detail'),
path('admin/product/<int:product_id>/toggle/', views.toggle_product_status, name='toggle_product_status'),

    path('sales-report/', views.sales_report, name='sales_report'),

    re_path(r'^.*$', catch_all_view),

]