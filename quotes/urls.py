from django.urls import path
from . import views

app_name = 'quotes'

urlpatterns = [
    path('create/', views.QuoteCreateView.as_view(), name='create'),
    path('<int:pk>/confirmation/', views.QuoteConfirmationView.as_view(), name='confirmation'),
    path('', views.QuoteListView.as_view(), name='finance_dashboard'),
    path('<int:pk>/', views.QuoteDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.QuoteUpdateView.as_view(), name='edit'),
    path('<int:pk>/pdf/', views.quote_pdf_view, name='pdf'),
    path('<int:pk>/add-items/', views.quote_add_items, name='add_items'),
]
