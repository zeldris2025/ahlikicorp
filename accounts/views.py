from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm
from .models import UserProfile

def _resolve_login(identifier, password, request):
    """Authenticate against a username or an email address.

    Accounts are normally created with the email as the username, but the two
    can be edited apart. Matching on either avoids the trap where someone
    changes their username and can no longer sign in with it.
    """
    identifier = (identifier or '').strip()
    if not identifier or not password:
        return None

    # Username first: it is unique, so there is never any ambiguity.
    user = authenticate(request, username=identifier, password=password)
    if user is not None:
        return user

    # Django does not enforce unique emails, so more than one account can
    # share one. Try each rather than raising MultipleObjectsReturned.
    for candidate in User.objects.filter(email__iexact=identifier):
        user = authenticate(request, username=candidate.username, password=password)
        if user is not None:
            return user

    return None


def _safe_redirect_target(request, fallback='core:home'):
    """Return ``next`` only when it points back at this site.

    Redirecting to an unchecked ``next`` lets a crafted link bounce someone to
    another domain immediately after they sign in.

    If user is in Finance or Admin group, redirect to finance dashboard instead.
    """
    target = request.POST.get('next') or request.GET.get('next')
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target

    if request.user.groups.filter(name__in=['Finance', 'Admin']).exists():
        return 'quotes:finance_dashboard'

    return fallback


def login_view(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name__in=['Finance', 'Admin']).exists():
            return redirect('quotes:finance_dashboard')
        return redirect('core:home')

    if request.method == 'POST':
        user = _resolve_login(
            request.POST.get('email'),
            request.POST.get('password'),
            request,
        )

        if user is not None:
            login(request, user)
            return redirect(_safe_redirect_target(request))

        messages.error(request, 'Those details did not match an account. Check your email or username and try again.')

    return render(request, 'accounts/login.html', {'next': request.GET.get('next', '')})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('core:home')

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)
