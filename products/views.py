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

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('brand', 'category')

        form = ProductSearchForm(self.request.GET)
        if form.is_valid():
            query = form.cleaned_data.get('query')
            brand = form.cleaned_data.get('brand')
            category = form.cleaned_data.get('category')
            is_exclusive = form.cleaned_data.get('is_exclusive')

            if query:
                queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
            if brand:
                queryset = queryset.filter(brand=brand)
            if category:
                queryset = queryset.filter(category=category)
            if is_exclusive:
                queryset = queryset.filter(is_exclusive=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProductSearchForm(self.request.GET)
        context['brands'] = Brand.objects.all()
        context['categories'] = Category.objects.all()
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    slug_field = 'slug'

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('brand', 'category').prefetch_related('gallery')
