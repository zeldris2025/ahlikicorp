from django.core.cache import cache


def site_brands(request):
    """Brand list for the site-wide footer strip and brand links."""
    brands = cache.get('footer_brands')
    if brands is None:
        from products.models import Brand
        brands = list(Brand.objects.all().order_by('sort_order', 'name'))
        cache.set('footer_brands', brands, 3600)
    return {'footer_brands': brands}


def user_roles(request):
    """Expose role flags to every template.

    Templates cannot test group membership directly (``'Finance' in
    user.groups`` compares a string against Group instances), so the checks
    are resolved here once per request.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'is_finance': False, 'is_admin': False, 'can_manage_quotes': False}

    groups = set(user.groups.values_list('name', flat=True))
    is_finance = 'Finance' in groups
    is_admin = 'Admin' in groups or user.is_superuser

    return {
        'is_finance': is_finance,
        'is_admin': is_admin,
        'can_manage_quotes': is_finance or is_admin,
    }
