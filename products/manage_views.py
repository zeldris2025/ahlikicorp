"""Staff portal views for product maintenance.

A deliberately narrow alternative to Django Admin: Finance can maintain
products and categories and nothing else. Every view enforces the role check
server-side, so hiding a link is never what keeps someone out.
"""

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from accounts.permissions import StaffPortalMixin

from .forms import CategoryForm, ProductForm
from .models import Brand, Category, Product


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
        messages.success(self.request, f'“{self.object.name}” was created.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = 'Add product'
        context['submit_label'] = 'Create product'
        return context


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
