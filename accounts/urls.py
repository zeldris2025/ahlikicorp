from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('register/submitted/', views.register_submitted_view, name='register_submitted'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Approved accounts are issued a generated password, so changing it has to
    # be possible from the site rather than only through Django Admin.
    path(
        'password/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url=reverse_lazy('accounts:password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'password/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html',
        ),
        name='password_change_done',
    ),
]
