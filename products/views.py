from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Brand, Category
from .forms import ProductSearchForm

class ProductListView(ListView):
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 24

    # The public catalogue is the wholesale trade list. The other group
    # companies are retail/hospitality operations and do not sell from here.
    CATALOGUE_BRAND_SLUG = 'ahliki-wholesale'

    def get_queryset(self):
        queryset = (
            Product.objects
            .filter(is_active=True, brand__slug=self.CATALOGUE_BRAND_SLUG)
            .select_related('brand', 'category')
        )

        form = ProductSearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            category = form.cleaned_data.get('category')
            is_exclusive = form.cleaned_data.get('is_exclusive')

            if query:
                queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
            if category:
                queryset = queryset.filter(category=category)
            if is_exclusive:
                queryset = queryset.filter(is_exclusive=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProductSearchForm(self.request.GET)
        context['categories'] = Category.objects.all()
        context['catalogue_brand'] = Brand.objects.filter(slug=self.CATALOGUE_BRAND_SLUG).first()
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True, brand__slug=ProductListView.CATALOGUE_BRAND_SLUG)
            .select_related('brand', 'category')
            .prefetch_related('gallery')
        )
