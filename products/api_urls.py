from django.urls import path
from rest_framework.routers import DefaultRouter
from . import viewsets

router = DefaultRouter()
router.register(r'products', viewsets.ProductViewSet, basename='product')
router.register(r'brands', viewsets.BrandViewSet, basename='brand')
router.register(r'categories', viewsets.CategoryViewSet, basename='category')

app_name = 'api-products'
urlpatterns = router.urls
