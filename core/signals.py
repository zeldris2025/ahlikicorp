"""Cache invalidation for location data used on the home page."""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Location


@receiver(post_save, sender=Location)
@receiver(post_delete, sender=Location)
def clear_location_caches(sender, **kwargs):
    cache.delete('locations_count')
