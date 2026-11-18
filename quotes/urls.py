from django.urls import path

from . import basket_views, quick_request, views

app_name = 'quotes'

urlpatterns = [
    # Basket flow: browse -> add -> review -> checkout
    path('basket/', basket_views.basket_detail, name='basket'),
    path('basket/add/<int:pk>/', basket_views.basket_add, name='basket_add'),
    path('basket/update/<int:pk>/', basket_views.basket_update, name='basket_update'),
    path('basket/remove/<int:pk>/', basket_views.basket_remove, name='basket_remove'),
    path('basket/clear/', basket_views.basket_clear, name='basket_clear'),
    path('checkout/', basket_views.checkout, name='checkout'),

    # The floating "Request a quote" widget, open to any visitor.
    path('request/', quick_request.quick_request, name='quick_request'),
    path('create/', views.QuoteCreateView.as_view(), name='create'),
    path('<int:pk>/confirmation/', views.QuoteConfirmationView.as_view(), name='confirmation'),
    path('', views.QuoteListView.as_view(), name='finance_dashboard'),
    path('<int:pk>/', views.QuoteDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.QuoteUpdateView.as_view(), name='edit'),
    path('<int:pk>/pdf/', views.quote_pdf_view, name='pdf'),
    path('<int:pk>/add-items/', views.quote_add_items, name='add_items'),
]
