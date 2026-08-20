from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('brands/', views.BrandsView.as_view(), name='brands'),
    path('locations/', views.LocationsView.as_view(), name='locations'),
    path('contact/', views.contact_view, name='contact'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
