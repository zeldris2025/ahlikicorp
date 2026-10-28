from django.urls import path

from . import agent_views, views

app_name = 'chat'

urlpatterns = [
    # Visitor, from the assistant widget. Always the session's own chat.
    path('chat/current/', views.current, name='current'),
    path('chat/start/', views.start, name='start'),
    path('chat/poll/', views.poll, name='poll'),
    path('chat/send/', views.send, name='send'),
    path('chat/end/', views.end, name='end'),

    # Agent inbox, inside the staff portal.
    path('manage/chats/', agent_views.InboxView.as_view(), name='inbox'),
    path('manage/chats/api/list/', agent_views.conversation_list, name='api_list'),
    path('manage/chats/api/products/', agent_views.product_search, name='api_products'),
    path('manage/chats/api/<int:pk>/', agent_views.conversation_detail, name='api_detail'),
    path('manage/chats/api/<int:pk>/send/', agent_views.send, name='api_send'),
    path('manage/chats/api/<int:pk>/take/', agent_views.take, name='api_take'),
    path('manage/chats/api/<int:pk>/status/', agent_views.set_status, name='api_status'),
    path('manage/chats/api/<int:pk>/quote/', agent_views.create_quote, name='api_quote'),
]
