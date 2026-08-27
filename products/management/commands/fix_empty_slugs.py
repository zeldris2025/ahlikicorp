"""Fix products with empty or invalid slugs.

This management command finds all products with empty or invalid slugs
and generates proper slugs for them based on their product name.
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Product


class Command(BaseCommand):
    help = 'Fix products with empty or invalid slugs'

    def handle(self, *args, **options):
        # Find products with empty or None slugs
        products_to_fix = Product.objects.filter(slug='') | Product.objects.filter(slug__isnull=True)

        if not products_to_fix.exists():
            self.stdout.write(self.style.SUCCESS('No products with empty slugs found.'))
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

            # Generate slug from product name
            base = slugify(product.name)[:45] or 'product'
            slug, n = base, 2

            # Ensure slug is unique
            existing = Product.objects.exclude(pk=product.pk)
            while existing.filter(slug=slug).exists():
                slug = f'{base}-{n}'
                n += 1

            product.slug = slug
            product.save(update_fields=['slug'])
            fixed_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Fixed product {product.id} ({product.name}): slug = {slug}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(f'\nFixed {fixed_count} product(s) with empty slugs.')
        )
