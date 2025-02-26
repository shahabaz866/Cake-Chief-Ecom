
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('home/', include(('home.urls', 'home'), namespace='home')),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('allauth.urls')),
    path('order_app/',include('order_app.urls')),
    path('cart_app/',include('cart_app.urls')),
    path('user_app/',include('user_app.urls')),
    path('wishlist/',include('wishlist_app.urls')),
    path('wallet/',include('wallet_app.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),

  

]

if settings.DEBUG:
            urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
