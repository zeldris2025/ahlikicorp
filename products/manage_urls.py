from django.urls import path

from . import manage_views

app_name = 'manage'

urlpatterns = [
    path('', manage_views.DashboardView.as_view(), name='dashboard'),

    path('products/', manage_views.ProductListView.as_view(), name='product_list'),
    path('products/new/', manage_views.ProductCreateView.as_view(), name='product_create'),
    path('products/bulk-upload/', manage_views.ProductBulkUploadView.as_view(), name='product_bulk_upload'),
    path('products/csv-template/', manage_views.product_csv_template, name='product_csv_template'),
    path('products/<int:pk>/edit/', manage_views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', manage_views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<int:pk>/toggle/', manage_views.toggle_active, name='product_toggle'),

    path('categories/', manage_views.CategoryListView.as_view(), name='category_list'),

    path('export/', manage_views.ExportView.as_view(), name='export'),
    path('export/all.zip', manage_views.export_all, name='export_all'),
    path('export/<str:key>.csv', manage_views.export_dataset, name='export_dataset'),

    path('promotions/', manage_views.PromotionListView.as_view(), name='promotion_list'),
    path('promotions/<int:pk>/edit/', manage_views.PromotionUpdateView.as_view(), name='promotion_edit'),
    path('promotions/<int:pk>/delete/', manage_views.PromotionDeleteView.as_view(), name='promotion_delete'),

    path('exclusive-logos/', manage_views.ExclusiveLogoListView.as_view(), name='exclusive_list'),
    path('exclusive-logos/<int:pk>/edit/', manage_views.ExclusiveLogoUpdateView.as_view(), name='exclusive_edit'),
    path('exclusive-logos/<int:pk>/delete/', manage_views.ExclusiveLogoDeleteView.as_view(), name='exclusive_delete'),
]
