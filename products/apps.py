from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    # Group companies live here too, so the admin heading names both.
    verbose_name = 'Companies & products'

    def ready(self):
        from . import signals  # noqa: F401  (registers cache invalidation)
