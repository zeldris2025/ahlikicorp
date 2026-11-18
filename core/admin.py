from django.conf import settings
from django.contrib import admin
from .models import Location, ContactMessage, NewsletterSubscriber

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'island', 'phone', 'on_map', 'is_headquarters', 'sort_order')
    list_filter = ('company', 'island', 'is_headquarters')
    search_fields = ('name', 'address', 'phone', 'email')
    list_select_related = ('company',)
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'company', 'island', 'is_headquarters', 'sort_order')}),
        ('Address', {
            'fields': ('address', 'latitude', 'longitude'),
            'description': (
                'Use the map below to place the pin, or type the coordinates in. '
                'Sites without coordinates are listed on the website but not pinned.'
            ),
        }),
        ('Contact', {'fields': ('phone', 'email', 'opening_hours')}),
    )

    @admin.display(boolean=True, description='On map')
    def on_map(self, obj):
        return obj.latitude is not None and obj.longitude is not None

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # The pin picker shows the group's other sites for reference.
        others = Location.objects.filter(latitude__isnull=False, longitude__isnull=False)
        if object_id:
            others = others.exclude(pk=object_id)
        extra_context = {
            **(extra_context or {}),
            'map_points': [
                {'name': l.name, 'lat': float(l.latitude), 'lng': float(l.longitude)}
                for l in others
            ],
            'map_tile_url': settings.MAP_TILE_URL,
            'map_tile_attribution': settings.MAP_TILE_ATTRIBUTION,
        }
        return super().changeform_view(request, object_id, form_url, extra_context)

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
