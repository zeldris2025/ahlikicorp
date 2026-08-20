from django.contrib import admin
from .models import Brand, Category, Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'sort_order')

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Group operating companies (surfaced to visitors as "companies")."""

    list_display = ('name', 'sector', 'slug', 'sort_order')
    list_filter = ('sector',)
    search_fields = ('name', 'sector', 'tagline')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'sector', 'tagline')}),
        ('Branding', {'fields': ('accent_color', 'logo')}),
        ('Details', {
            'fields': ('description', 'highlights', 'sort_order'),
            'description': 'Highlights must be a JSON list of short strings, e.g. ["Eggs", "Fresh produce"].',
        }),
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'brand', 'category', 'cost_price', 'is_exclusive', 'is_active', 'stock_quantity')
    list_filter = ('brand', 'category', 'is_exclusive', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'sku', 'brand', 'category')}),
        ('Description', {'fields': ('description', 'specifications')}),
        ('Images', {'fields': ('image',)}),
        ('Pricing & Stock', {'fields': ('cost_price', 'stock_quantity')}),
        ('Status', {'fields': ('is_exclusive', 'is_active')}),
        ('Metadata', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'sort_order')
    list_filter = ('product', 'sort_order')
    ordering = ('product', 'sort_order')
