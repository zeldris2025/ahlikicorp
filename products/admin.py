import json

from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .csv_import import CSV_COLUMNS, CsvImportError, import_products, template_response
from .forms import ProductBulkUploadForm
from core.models import Location

from .models import Brand, Category, ExclusiveBrand, Product, ProductImage, Promotion

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'sort_order')

class LocationInline(admin.TabularInline):
    """A company's sites, with a link through to the full form and its map."""

    model = Location
    extra = 0
    fields = ('name', 'address', 'island', 'latitude', 'longitude', 'is_headquarters')
    show_change_link = True

class HighlightsField(forms.CharField):
    """Edits the highlights JSON list as plain text, one chip per line."""

    widget = forms.Textarea(attrs={'rows': 4, 'placeholder': 'Fresh eggs\nIsland-wide delivery'})

    def prepare_value(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return value
        if isinstance(value, list):
            return '\n'.join(str(item) for item in value)
        return value or ''

    def to_python(self, value):
        lines = (line.strip() for line in (value or '').splitlines())
        return [line for line in lines if line]


class CompanyAdminForm(forms.ModelForm):
    highlights = HighlightsField(
        required=False,
        help_text='One per line. Each line becomes a chip on the company section, e.g. "Fresh eggs".',
    )

    class Meta:
        model = Brand
        fields = '__all__'
        widgets = {
            'accent_color': forms.TextInput(attrs={'type': 'color', 'style': 'width:4rem;height:2.2rem;padding:0'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
        help_texts = {
            'slug': 'Web address of the company page, e.g. /companies/farmer-joe/. Filled in from the name.',
            'tagline': 'One line under the company name.',
            'accent_color': 'Brand colour used for the company section, buttons and map pins.',
            'logo': 'Transparent PNG or SVG-style logo works best.',
            'sort_order': 'Lower numbers appear first on the home page, menu and footer.',
        }


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Operating companies under Ah Liki Investment Corporation.

    Every company added here appears on the home page, the Companies page,
    the header menu and the footer, and gets its own page at /companies/<slug>/.
    """

    form = CompanyAdminForm
    list_display = ('logo_preview', 'name', 'sector', 'sites', 'sort_order', 'view_page')
    list_display_links = ('logo_preview', 'name')
    list_editable = ('sort_order',)
    list_filter = ('sector',)
    search_fields = ('name', 'sector', 'tagline')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Company', {'fields': ('name', 'slug', 'sector', 'tagline')}),
        ('Branding', {'fields': ('accent_color', 'logo', 'hero_image')}),
        ('About the company', {'fields': ('description', 'highlights', 'sort_order')}),
    )
    inlines = [LocationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_sites=Count('locations'))

    @admin.display(description='Logo')
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" alt="" style="height:32px;max-width:80px;object-fit:contain">', obj.logo.url)
        return format_html(
            '<span style="display:inline-block;width:14px;height:14px;border-radius:50%;background:{}"></span>',
            obj.accent_color,
        )

    @admin.display(description='Sites', ordering='_sites')
    def sites(self, obj):
        return obj._sites

    @admin.display(description='Page')
    def view_page(self, obj):
        return format_html('<a href="{}" target="_blank" rel="noopener">View ↗</a>', obj.get_absolute_url())

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

    # Bulk import lives here as well as in the staff portal, so whoever is
    # already in Admin does not have to change screens to load a price list.
    change_list_template = 'admin/products/product/change_list.html'

    def get_urls(self):
        custom = [
            path(
                'import-csv/',
                self.admin_site.admin_view(self.import_csv_view),
                name='products_product_import_csv',
            ),
            path(
                'import-csv/template/',
                self.admin_site.admin_view(self.csv_template_view),
                name='products_product_csv_template',
            ),
        ]
        return custom + super().get_urls()

    def csv_template_view(self, request):
        return template_response()

    def import_csv_view(self, request):
        form = ProductBulkUploadForm()

        if request.method == 'POST':
            form = ProductBulkUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    result = import_products(form.cleaned_data['csv_file'])
                except CsvImportError as exc:
                    self.message_user(request, str(exc), level=messages.ERROR)
                else:
                    if result.created:
                        self.message_user(request, result.success_summary(), level=messages.SUCCESS)
                    if result.has_skipped:
                        self.message_user(request, result.skipped_summary(), level=messages.INFO)
                    if result.has_errors:
                        self.message_user(request, result.error_summary(), level=messages.WARNING)
                    if not result.created and not result.has_errors and not result.has_skipped:
                        self.message_user(request, 'No rows found in the CSV file.', level=messages.WARNING)
                    if result.created:
                        return redirect(reverse('admin:products_product_changelist'))

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Import products from CSV',
            'form': form,
            'columns': CSV_COLUMNS,
            'template_url': reverse('admin:products_product_csv_template'),
        }
        return render(request, 'admin/products/product/import_csv.html', context)

@admin.register(ExclusiveBrand)
class ExclusiveBrandAdmin(admin.ModelAdmin):
    """Supplier labels we distribute exclusively — the home page logo marquee."""

    list_display = ('name', 'note', 'sort_order', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('sort_order', 'is_active')
    search_fields = ('name', 'note')
    fields = ('name', 'logo', 'website', 'note', 'sort_order', 'is_active')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'sort_order')
    list_filter = ('product', 'sort_order')
    ordering = ('product', 'sort_order')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """Slides in the home page hero slideshow."""

    list_display = ('headline', 'kicker', 'is_active', 'starts_at', 'ends_at', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('headline', 'kicker', 'subtext')
    fieldsets = (
        ('Slide', {'fields': ('kicker', 'headline', 'subtext', 'image')}),
        ('Button', {'fields': ('cta_label', 'cta_url')}),
        ('Scheduling', {
            'fields': ('is_active', 'starts_at', 'ends_at', 'sort_order'),
            'description': 'Leave both dates blank to run the slide until it is switched off.',
        }),
        ('Styling', {'fields': ('accent_color',)}),
    )
