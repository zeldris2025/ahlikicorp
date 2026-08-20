"""Cache invalidation for company and product data.

The home page and footer cache their querysets for an hour. Without these
receivers an edit in the admin would not appear on the site until that hour
elapsed — and because LocMemCache is per-process, clearing it from a shell
would not affect the running server.
"""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Brand, Product

# Keys populated by core.views.HomeView and core.context_processors.
COMPANY_CACHE_KEYS = ('group_companies', 'footer_brands', 'brands')
PRODUCT_CACHE_KEYS = ('featured_products',)


@receiver(post_save, sender=Brand)
@receiver(post_delete, sender=Brand)
def clear_company_caches(sender, **kwargs):
    cache.delete_many(list(COMPANY_CACHE_KEYS))


@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def clear_product_caches(sender, **kwargs):
    cache.delete_many(list(PRODUCT_CACHE_KEYS))
