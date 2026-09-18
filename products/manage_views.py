"""Staff portal views for product maintenance.

A deliberately narrow alternative to Django Admin: Finance can maintain
products and categories and nothing else. Every view enforces the role check
server-side, so hiding a link is never what keeps someone out.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from accounts.permissions import StaffPortalMixin

from .csv_export import DATASETS, archive_response, dataset_counts, dataset_response
from .csv_import import CsvImportError, import_products, template_response
from .forms import CategoryForm, ExclusiveBrandForm, ProductForm, ProductBulkUploadForm, PromotionForm
from .models import Brand, Category, ExclusiveBrand, Product, Promotion


class DashboardView(StaffPortalMixin, TemplateView):
    template_name = 'manage/dashboard.html'

    def get_context_data(self, **kwargs):
        from quotes.models import Quote

        context = super().get_context_data(**kwargs)
        context['product_total'] = Product.objects.count()
        context['product_active'] = Product.objects.filter(is_active=True).count()
        context['product_exclusive'] = Product.objects.filter(is_exclusive=True, is_active=True).count()
        context['out_of_stock'] = Product.objects.filter(is_active=True, stock_quantity=0).count()
        context['category_total'] = Category.objects.count()

        context['quotes_pending'] = Quote.objects.filter(status=Quote.Status.PENDING).count()
        context['quotes_total'] = Quote.objects.count()

        context['recent_products'] = (
            Product.objects.select_related('brand', 'category').order_by('-updated_at')[:6]
        )
        return context


class ProductListView(StaffPortalMixin, ListView):
    model = Product
    template_name = 'manage/product_list.html'
    context_object_name = 'products'
    paginate_by = 25

    def get_queryset(self):
        qs = Product.objects.select_related('brand', 'category').order_by('-updated_at')

        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))

        brand = self.request.GET.get('brand')
        if brand:
            qs = qs.filter(brand_id=brand)

        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'exclusive':
            qs = qs.filter(is_exclusive=True)
        elif status == 'nostock':
            qs = qs.filter(stock_quantity=0)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.order_by('sort_order', 'name')
        context['search'] = self.request.GET.get('q', '')
        context['brand_filter'] = self.request.GET.get('brand', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class ProductCreateView(StaffPortalMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'manage/product_form.html'
    success_url = reverse_lazy('manage:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'”{self.object.name}” was created.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = 'Add product'
        context['submit_label'] = 'Create product'
        return context


class ProductBulkUploadView(StaffPortalMixin, TemplateView):
    template_name = 'manage/product_bulk_upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', ProductBulkUploadForm())
        return context

    def post(self, request, *args, **kwargs):
        form = ProductBulkUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, self.get_context_data(form=form))

        try:
            result = import_products(form.cleaned_data['csv_file'])
        except CsvImportError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, self.get_context_data(form=form))

        if result.created:
            messages.success(request, result.success_summary())
        if result.has_skipped:
            messages.info(request, result.skipped_summary())
        if result.has_errors:
            messages.warning(request, result.error_summary())
        if not result.created and not result.has_errors and not result.has_skipped:
            messages.warning(request, 'No rows found in the CSV file.')

        return redirect('manage:product_list')


def product_csv_template(request):
    """Download a starter CSV with the expected header row."""
    from accounts.permissions import is_finance
    from django.core.exceptions import PermissionDenied

    if not request.user.is_authenticated or not is_finance(request.user):
        raise PermissionDenied('This area is restricted to authorised staff.')

    return template_response()


class ProductUpdateView(StaffPortalMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'manage/product_form.html'
    success_url = reverse_lazy('manage:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'“{self.object.name}” was updated.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = 'Edit product'
        context['submit_label'] = 'Save changes'
        return context


class ProductDeleteView(StaffPortalMixin, DeleteView):
    model = Product
    template_name = 'manage/product_confirm_delete.html'
    success_url = reverse_lazy('manage:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Deleting a product that has been quoted would break the quote's
        # history, so surface that before they commit to it.
        context['quote_uses'] = self.object.quote_items.count()
        return context

    def form_valid(self, form):
        name = self.object.name
        if self.object.quote_items.exists():
            # PROTECT on the FK would raise; withdraw it instead of deleting.
            self.object.is_active = False
            self.object.save(update_fields=['is_active'])
            messages.warning(
                self.request,
                f'“{name}” appears on existing quotes, so it was withdrawn from the '
                f'catalogue instead of deleted. Quote history is preserved.',
            )
            return redirect(self.success_url)

        messages.success(self.request, f'“{name}” was deleted.')
        return super().form_valid(form)


class CategoryListView(StaffPortalMixin, ListView):
    model = Category
    template_name = 'manage/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count('products')).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category “{category.name}” was added.')
            return redirect('manage:category_list')

        self.object_list = self.get_queryset()
        context = self.get_context_data()
        context['form'] = form
        return render(request, self.template_name, context)


class ExclusiveLogoListView(StaffPortalMixin, ListView):
    """Logos of the brands we distribute exclusively, shown in the home marquee.

    Add and list on one page, in the same shape as the category screen: adding
    a logo is a two-field job and does not warrant its own step.
    """

    model = ExclusiveBrand
    template_name = 'manage/exclusive_list.html'
    context_object_name = 'logos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', ExclusiveBrandForm())
        return context

    def post(self, request, *args, **kwargs):
        form = ExclusiveBrandForm(request.POST, request.FILES)
        if form.is_valid():
            logo = form.save()
            messages.success(request, f'“{logo.name}” was added to the home page marquee.')
            return redirect('manage:exclusive_list')

        self.object_list = self.get_queryset()
        return render(request, self.template_name, self.get_context_data(form=form))


class ExclusiveLogoUpdateView(StaffPortalMixin, UpdateView):
    model = ExclusiveBrand
    form_class = ExclusiveBrandForm
    template_name = 'manage/exclusive_form.html'
    success_url = reverse_lazy('manage:exclusive_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'“{self.object.name}” was updated.')
        return response


class ExclusiveLogoDeleteView(StaffPortalMixin, DeleteView):
    model = ExclusiveBrand
    template_name = 'manage/exclusive_confirm_delete.html'
    success_url = reverse_lazy('manage:exclusive_list')

    def form_valid(self, form):
        messages.success(self.request, f'“{self.object.name}” was removed from the marquee.')
        return super().form_valid(form)


class PromotionListView(StaffPortalMixin, ListView):
    """Slides in the home page hero slideshow.

    Adding one needs a photo and a short headline, so the create form sits
    beside the list rather than on a screen of its own.
    """

    model = Promotion
    template_name = 'manage/promotion_list.html'
    context_object_name = 'promotions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', PromotionForm())
        return context

    def post(self, request, *args, **kwargs):
        form = PromotionForm(request.POST, request.FILES)
        if form.is_valid():
            promotion = form.save()
            messages.success(request, f'“{promotion.headline}” was added to the home page slideshow.')
            return redirect('manage:promotion_list')

        self.object_list = self.get_queryset()
        return render(request, self.template_name, self.get_context_data(form=form))


class PromotionUpdateView(StaffPortalMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = 'manage/promotion_form.html'
    success_url = reverse_lazy('manage:promotion_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'“{self.object.headline}” was updated.')
        return response


class PromotionDeleteView(StaffPortalMixin, DeleteView):
    model = Promotion
    template_name = 'manage/promotion_confirm_delete.html'
    success_url = reverse_lazy('manage:promotion_list')

    def form_valid(self, form):
        messages.success(self.request, f'“{self.object.headline}” was removed from the slideshow.')
        return super().form_valid(form)


class ExportView(StaffPortalMixin, TemplateView):
    """One screen listing everything that can be pulled out of the site."""

    template_name = 'manage/export.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        counts = dataset_counts()
        context['datasets'] = [
            {'key': key, 'count': counts.get(key, 0), **dataset}
            for key, dataset in DATASETS.items()
        ]
        context['row_total'] = sum(counts.values())
        return context


def export_dataset(request, key):
    """Download a single dataset as CSV."""
    _require_staff(request)
    if key not in DATASETS:
        raise Http404('There is no export by that name.')
    return dataset_response(key)


def export_all(request):
    """Download every dataset at once as a ZIP of CSV files."""
    _require_staff(request)
    return archive_response()


def _require_staff(request):
    """Same server-side gate the class-based portal views apply.

    The plain function views cannot use StaffPortalMixin, and an export is
    exactly the kind of URL that must not rely on a hidden link for safety.
    """
    from accounts.permissions import is_finance

    if not request.user.is_authenticated or not is_finance(request.user):
        raise PermissionDenied('This area is restricted to authorised staff.')


def toggle_active(request, pk):
    """Quick active/withdrawn switch from the product list."""
    from accounts.permissions import is_finance

    if not request.user.is_authenticated or not is_finance(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied('This area is restricted to authorised staff.')

    if request.method != 'POST':
        return redirect('manage:product_list')

    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    messages.success(
        request,
        f'“{product.name}” is now {"live in the catalogue" if product.is_active else "withdrawn"}.',
    )
    return redirect(request.META.get('HTTP_REFERER') or 'manage:product_list')
