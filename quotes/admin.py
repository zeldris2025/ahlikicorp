from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Quote, QuoteItem

class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'line_total')
    readonly_fields = ('line_total',)

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('reference', 'customer_name', 'status_badge', 'total', 'created_at', 'actions_column')
    list_filter = ('status', 'created_at', 'delivery_location')
    search_fields = ('reference', 'customer_name', 'company', 'email')
    inlines = [QuoteItemInline]
    readonly_fields = ('reference', 'customer', 'created_at', 'updated_at', 'subtotal', 'tax_total', 'total')

    fieldsets = (
        ('Reference', {'fields': ('reference', 'status', 'created_at', 'updated_at')}),
        ('Customer Info', {'fields': ('customer', 'customer_name', 'company', 'email', 'phone')}),
        ('Delivery', {'fields': ('delivery_location', 'delivery_address')}),
        ('Pricing', {'fields': ('tax_rate', 'valid_until', 'subtotal', 'tax_total', 'total')}),
        ('Notes', {'fields': ('notes', 'internal_notes')}),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'QUOTED': 'blue',
            'ACCEPTED': 'green',
            'REJECTED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def actions_column(self, obj):
        url = reverse('admin:quotes_quote_change', args=[obj.pk])
        return format_html('<a class="button" href="{}">Edit</a>', url)
    actions_column.short_description = 'Actions'

@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ('quote', 'product', 'quantity', 'unit_price', 'line_total')
    list_filter = ('quote__status',)
    search_fields = ('quote__reference', 'product__name')
    readonly_fields = ('line_total', 'margin')
