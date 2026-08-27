from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .csv_import import CSV_COLUMNS, CsvImportError, import_products, template_response
from .forms import ProductBulkUploadForm
from .models import Brand, Category, ExclusiveBrand, Product, ProductImage

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
