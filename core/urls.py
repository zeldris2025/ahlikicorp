from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('companies/', views.CompaniesView.as_view(), name='companies'),
    path('companies/<slug:slug>/', views.CompanyDetailView.as_view(), name='company_detail'),
    # Former URL, kept so existing links keep working.
    path('brands/', RedirectView.as_view(pattern_name='core:companies', permanent=True)),
    path('locations/', views.LocationsView.as_view(), name='locations'),
    path('contact/', views.contact_view, name='contact'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
