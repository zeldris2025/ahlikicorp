"""ahlikicorp URL Configuration"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('products/', include('products.urls', namespace='products')),
    path('quotes/', include('quotes.urls', namespace='quotes')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    # Live chat: the visitor endpoints and the agent inbox at /manage/chats/.
    path('', include('chat.urls', namespace='chat')),
    # Staff portal — a narrow alternative to Django Admin for Finance.
    path('manage/', include('products.manage_urls', namespace='manage')),
    path('api/products/', include('products.api_urls', namespace='api-products')),
    path('api/quotes/', include('quotes.api_urls', namespace='api-quotes')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
elif settings.SERVE_MEDIA:
    # Production (Azure): serve uploaded files from the persistent MEDIA_ROOT.
    # static() is a no-op when DEBUG is off, so the route is added directly.
    urlpatterns += [
        re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), serve,
                {'document_root': settings.MEDIA_ROOT}),
    ]
