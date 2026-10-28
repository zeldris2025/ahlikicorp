from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ('created_at', 'sender', 'agent', 'body', 'product')
    readonly_fields = fields
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'email', 'phone', 'channel', 'status', 'assigned_to', 'last_message_at')
    list_filter = ('channel', 'status')
    search_fields = ('customer_name', 'email', 'phone')
    raw_id_fields = ('customer', 'assigned_to', 'quote')
    inlines = [MessageInline]
