"""Fix products with empty or invalid SKUs.

This management command finds all products with empty or invalid SKUs
and generates proper SKUs for them based on their product name.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Product


class Command(BaseCommand):
    help = 'Fix products with empty or invalid SKUs'

    def handle(self, *args, **options):
        # Find products with empty or None SKUs
        products_to_fix = Product.objects.filter(sku='') | Product.objects.filter(sku__isnull=True)

        if not products_to_fix.exists():
            self.stdout.write(self.style.SUCCESS('No products with empty SKUs found.'))
            return

        fixed_count = 0

        for product in products_to_fix:
            if not product.name or not product.name.strip():
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipping product {product.id}: No product name'
                    )
                )
                continue

            # Generate SKU from product name
            base = slugify(product.name).upper()[:20]
            if not base:
                base = 'PRODUCT'

            sku, n = base, 2

            # Ensure SKU is unique
            existing = Product.objects.exclude(pk=product.pk)
            while existing.filter(sku__iexact=sku).exists():
                sku = f'{base}-{n}'
                n += 1

            product.sku = sku
            product.save(update_fields=['sku'])
            fixed_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Fixed product {product.id} ({product.name}): SKU = {sku}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nFixed {fixed_count} product(s) with empty SKUs.')
        )
