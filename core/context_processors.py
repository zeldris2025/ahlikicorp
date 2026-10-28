from django.core.cache import cache


def site_brands(request):
    """Company list for the footer strip and the header mega menu.

    Both are on every page, so the list and the site count are cached rather
    than queried per request.
    """
    brands = cache.get('footer_brands')
    if brands is None:
        from products.models import Brand
        brands = list(Brand.objects.all().order_by('sort_order', 'name'))
        cache.set('footer_brands', brands, 3600)

    locations_count = cache.get('locations_count')
    if locations_count is None:
        from .models import Location
        locations_count = Location.objects.count()
        cache.set('locations_count', locations_count, 3600)

    return {
        'footer_brands': brands,
        'nav_companies': brands,
        'nav_locations_count': locations_count,
    }


def site_contact(request):
    """Address, phone, email and shop link for the header.

    The address comes from whichever Location is flagged as headquarters, so
    it stays correct when the head office moves, and falls back to the
    SITE_ADDRESS setting when no site is flagged. The result is cached: it is
    read on every page and changes about once a decade.
    """
    from django.conf import settings

    address = cache.get('site_contact_address')
    if address is None:
        from .models import Location
        hq = Location.objects.filter(is_headquarters=True).first()
        address = (hq.address if hq else '') or getattr(settings, 'SITE_ADDRESS', '')
        cache.set('site_contact_address', address, 3600)

    phone = getattr(settings, 'SITE_PHONE', '')
    return {
        'site_address': address,
        'site_phone': phone,
        # tel: links must not contain spaces or punctuation.
        'site_phone_href': ''.join(c for c in phone if c.isdigit() or c == '+'),
        'site_email': getattr(settings, 'SITE_EMAIL', ''),
        # Hidden until the storefront launches; see SHOW_SHOP_ONLINE.
        'shop_online_url': getattr(settings, 'SHOP_ONLINE_URL', ''),
        'show_shop_online': getattr(settings, 'SHOW_SHOP_ONLINE', False),
    }


def user_roles(request):
    """Expose role flags to every template.

    Templates cannot test group membership directly (``'Finance' in
    user.groups`` compares a string against Group instances), so the checks
    are resolved here once per request.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {
            'is_finance': False,
            'is_admin': False,
            'can_manage_quotes': False,
            'can_request_quote': False,
            'is_sales': False,
            'can_answer_chats': False,
        }

    groups = set(user.groups.values_list('name', flat=True))
    is_finance = 'Finance' in groups
    is_admin = 'Admin' in groups or user.is_superuser
    # Approved trade accounts are the only ones that may raise a quote.
    is_customer = 'Customers' in groups
    is_sales = 'Sales Girls' in groups

    return {
        'is_finance': is_finance,
        'is_admin': is_admin,
        'can_manage_quotes': is_finance or is_admin,
        'can_request_quote': is_customer or is_finance or is_admin,
        'is_sales': is_sales,
        'can_answer_chats': is_sales or is_finance or is_admin,
    }


# Order in which social icons appear in the header and footer.
_SOCIAL_ORDER = (
    ('facebook', 'Facebook'),
    ('instagram', 'Instagram'),
    ('tiktok', 'TikTok'),
    ('linkedin', 'LinkedIn'),
    ('youtube', 'YouTube'),
)


def social_links(request):
    """Social profile links for the header and footer.

    Any profile without a configured URL still renders (so the header looks
    complete) but points at '#'. Set SOCIAL_FACEBOOK / SOCIAL_INSTAGRAM /
    SOCIAL_TIKTOK / SOCIAL_LINKEDIN in the environment to activate them.
    """
    from django.conf import settings

    configured = getattr(settings, 'SOCIAL_LINKS', {})
    return {
        'social_links': [
            {
                'key': key,
                'label': label,
                'url': configured.get(key) or '#',
                'configured': bool(configured.get(key)),
            }
            for key, label in _SOCIAL_ORDER
        ]
    }


def quote_basket(request):
    """Basket state for the header indicator and the catalogue buttons.

    ``quote_basket_ids`` lets a product already in the basket render in its
    added state on first paint, rather than flashing 'Add to quote' and then
    correcting itself.
    """
    if not hasattr(request, 'session'):
        return {'quote_basket_count': 0, 'quote_basket_ids': []}

    from quotes.basket import QuoteBasket
    basket = QuoteBasket(request)
    return {
        'quote_basket_count': len(basket),
        'quote_basket_ids': [int(pk) for pk in basket.basket.keys()],
    }


def site_assistant(request):
    """FAQ content for the floating assistant widget."""
    from django.urls import reverse

    from .faq import FAQ_TOPICS, STARTER_IDS

    topics = []
    for topic in FAQ_TOPICS:
        links = []
        for link in topic.get('links', []):
            try:
                links.append({'label': link['label'], 'url': reverse(link['url'])})
            except Exception:
                # A renamed route should not take the whole widget down.
                continue
        topics.append({
            'id': topic['id'],
            'q': topic['q'],
            'a': topic['a'],
            'keywords': topic['keywords'],
            'links': links,
        })

    return {'assistant_topics': topics, 'assistant_starters': STARTER_IDS}


def current_view(request):
    """Resolved route name, so navigation can mark the active page."""
    match = getattr(request, 'resolver_match', None)
    if match is None:
        return {'view_name': '', 'view_namespace': ''}
    return {'view_name': match.view_name or '', 'view_namespace': match.namespace or ''}
