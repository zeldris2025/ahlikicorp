from django.urls import path
from rest_framework.routers import DefaultRouter
from . import viewsets

router = DefaultRouter()
router.register(r'quotes', viewsets.QuoteViewSet, basename='quote')

app_name = 'api-quotes'
urlpatterns = router.urls
