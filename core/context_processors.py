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
    """Item count for the quote basket indicator in the header."""
    if not hasattr(request, 'session'):
        return {'quote_basket_count': 0}
    from quotes.basket import QuoteBasket
    return {'quote_basket_count': len(QuoteBasket(request))}


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
