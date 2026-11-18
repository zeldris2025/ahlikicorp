# Copyright (c) 2026 Charlie Wilson Ah Kuoi. All rights reserved.
# Proprietary and confidential. Use, copying or distribution requires the
# prior written permission of Charlie Wilson Ah Kuoi. See LICENSE.

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
