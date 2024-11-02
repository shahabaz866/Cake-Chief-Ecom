from django.urls import path
from . import views

urlpatterns =[
            
    path('',views.HomePage,name='home'),
    path('shop/flavor/<int:flavor_id>/', views.shoplist, name='flavor_filter'),
    path('shop/category/<int:category_id>/', views.shoplist, name='shop_by_category'),
    path('size/<int:size_id>/', views.size_filter, name='size_filter'), 
    path('shop/', views.shoplist, name='shop'), 
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('contact/',views.contact,name='contact'),
    path('about/',views.about,name='about'),
    path('verify_otp/', views.verify_otp, name='verify_otp'), 
    path('login/',views.LogingPage,name='login'),
    path('logout/',views.LogoutPage,name='logout'),
    path('signup/', views.SignupPage, name='SignupPage'),
   
     
]