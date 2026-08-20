from django.contrib import admin
from .models import Location, ContactMessage, NewsletterSubscriber

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'island', 'phone', 'is_headquarters', 'sort_order')
    list_filter = ('island', 'is_headquarters')
    search_fields = ('name', 'address', 'phone', 'email')
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'island', 'is_headquarters', 'sort_order')}),
        ('Address', {'fields': ('address', 'latitude', 'longitude')}),
        ('Contact', {'fields': ('phone', 'email', 'opening_hours')}),
    )

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at', 'resolved_at')
    list_filter = ('created_at', 'resolved_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Message Info', {'fields': ('subject', 'created_at', 'resolved_at')}),
        ('Sender', {'fields': ('name', 'email', 'phone')}),
        ('Message', {'fields': ('message',)}),
    )

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)
    actions = ['mark_active', 'mark_inactive']

    def mark_active(self, request, queryset):
        queryset.update(is_active=True)
    mark_active.short_description = 'Mark selected as active'

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
    mark_inactive.short_description = 'Mark selected as inactive'
