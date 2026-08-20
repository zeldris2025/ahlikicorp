"""Cache invalidation for generated quote PDFs.

The rendered PDF is cached for a day against the quote id. Any edit to the
quote or its line items has to drop that entry, otherwise Finance would keep
serving and emailing a stale document after correcting prices.
"""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Quote, QuoteItem


def quote_pdf_cache_key(quote_id):
    return f'quote_pdf_{quote_id}'


@receiver(post_save, sender=Quote)
@receiver(post_delete, sender=Quote)
def clear_quote_pdf(sender, instance, **kwargs):
    cache.delete(quote_pdf_cache_key(instance.pk))


@receiver(post_save, sender=QuoteItem)
@receiver(post_delete, sender=QuoteItem)
def clear_quote_pdf_for_item(sender, instance, **kwargs):
    # A line-item change alters the totals, so the parent quote's PDF is stale.
    cache.delete(quote_pdf_cache_key(instance.quote_id))
