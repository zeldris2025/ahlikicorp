from django.urls import path

from . import manage_views

app_name = 'manage'

urlpatterns = [
    path('', manage_views.DashboardView.as_view(), name='dashboard'),

    path('products/', manage_views.ProductListView.as_view(), name='product_list'),
    path('products/new/', manage_views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', manage_views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', manage_views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<int:pk>/toggle/', manage_views.toggle_active, name='product_toggle'),

    path('categories/', manage_views.CategoryListView.as_view(), name='category_list'),
]
