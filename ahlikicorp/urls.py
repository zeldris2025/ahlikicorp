"""ahlikicorp URL Configuration"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('products/', include('products.urls', namespace='products')),
    path('quotes/', include('quotes.urls', namespace='quotes')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('api/products/', include('products.api_urls', namespace='api-products')),
    path('api/quotes/', include('quotes.api_urls', namespace='api-quotes')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
