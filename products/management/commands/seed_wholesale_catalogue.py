"""Seed a representative Ah Liki Wholesale trade catalogue.

The public catalogue is the wholesale list, so it needs enough depth to be
usable. Lines below are generic bulk food/non-food categories of the kind a
Samoan wholesale distributor carries; adjust or replace them in the admin with
the real trade list.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Brand, Category, Product

CATEGORIES = [
    ('Rice & Grains', 'rice-grains'),
    ('Canned & Preserved', 'canned-preserved'),
    ('Cooking Essentials', 'cooking-essentials'),
    ('Beverages', 'beverages'),
    ('Snacks & Confectionery', 'snacks-confectionery'),
    ('Household & Non-Food', 'household-non-food'),
    ('Paper & Disposables', 'paper-disposables'),
]

# (name, sku, category slug, cost price, exclusive, pack description)
PRODUCTS = [
    ('Long Grain White Rice 25kg Sack', 'AW-RICE-25', 'rice-grains', '68.00', False, '25kg sack'),
    ('Jasmine Rice 10kg Sack', 'AW-RICE-J10', 'rice-grains', '34.50', False, '10kg sack'),
    ('Rolled Oats 5kg', 'AW-OATS-05', 'rice-grains', '22.00', False, '5kg bag'),
    ('Plain Flour 20kg Sack', 'AW-FLOU-20', 'rice-grains', '46.00', False, '20kg sack'),

    ('Corned Beef 340g — Carton of 24', 'AW-CORN-24', 'canned-preserved', '96.00', True, 'Carton of 24'),
    ('Mackerel in Tomato 425g — Carton of 24', 'AW-MACK-24', 'canned-preserved', '78.00', False, 'Carton of 24'),
    ('Baked Beans 420g — Carton of 24', 'AW-BEAN-24', 'canned-preserved', '54.00', False, 'Carton of 24'),
    ('Tuna Chunks in Oil 185g — Carton of 48', 'AW-TUNA-48', 'canned-preserved', '112.00', False, 'Carton of 48'),

    ('Vegetable Cooking Oil 20L Drum', 'AW-OIL-20L', 'cooking-essentials', '78.00', False, '20L drum'),
    ('Refined Sugar 25kg Sack', 'AW-SUGR-25', 'cooking-essentials', '52.00', False, '25kg sack'),
    ('Iodised Salt 1kg — Carton of 24', 'AW-SALT-24', 'cooking-essentials', '26.00', False, 'Carton of 24'),
    ('Soy Sauce 5L — Case of 4', 'AW-SOYA-04', 'cooking-essentials', '38.00', False, 'Case of 4'),

    ('Bottled Water 1.5L — Case of 12', 'AW-WATR-12', 'beverages', '18.00', False, 'Case of 12'),
    ('Assorted Soft Drinks 330ml — Carton of 24', 'AW-SOFT-24', 'beverages', '32.00', False, 'Carton of 24'),
    ('Instant Coffee 200g — Case of 12', 'AW-COFF-12', 'beverages', '84.00', False, 'Case of 12'),
    ('Milk Powder 900g — Carton of 12', 'AW-MILK-12', 'beverages', '138.00', True, 'Carton of 12'),

    ('Cream Crackers 200g — Carton of 30', 'AW-CRAC-30', 'snacks-confectionery', '48.00', False, 'Carton of 30'),
    ('Assorted Biscuits 400g — Carton of 12', 'AW-BISC-12', 'snacks-confectionery', '42.00', False, 'Carton of 12'),
    ('Potato Crisps 150g — Carton of 24', 'AW-CRIS-24', 'snacks-confectionery', '58.00', False, 'Carton of 24'),

    ('Laundry Powder 5kg — Case of 4', 'AW-LAUN-04', 'household-non-food', '64.00', False, 'Case of 4'),
    ('Dishwashing Liquid 5L — Case of 4', 'AW-DISH-04', 'household-non-food', '46.00', False, 'Case of 4'),
    ('Bar Soap 100g — Carton of 72', 'AW-SOAP-72', 'household-non-food', '58.00', False, 'Carton of 72'),
    ('Bleach 2L — Case of 6', 'AW-BLCH-06', 'household-non-food', '30.00', False, 'Case of 6'),

    ('Toilet Tissue 2-Ply — Carton of 48', 'AW-TISS-48', 'paper-disposables', '52.00', False, 'Carton of 48'),
    ('Paper Towel — Carton of 24', 'AW-TOWL-24', 'paper-disposables', '44.00', False, 'Carton of 24'),
    ('Takeaway Containers — Carton of 500', 'AW-CONT-500', 'paper-disposables', '68.00', True, 'Carton of 500'),
]


class Command(BaseCommand):
    help = 'Seed the Ah Liki Wholesale trade catalogue.'

    def handle(self, *args, **options):
        try:
            brand = Brand.objects.get(slug='ahliki-wholesale')
        except Brand.DoesNotExist:
            self.stderr.write(self.style.ERROR('Ah Liki Samoa Wholesale not found — run seed_data first.'))
            return

        for name, slug in CATEGORIES:
            Category.objects.get_or_create(slug=slug, defaults={'name': name})

        created = updated = 0
        for name, sku, cat_slug, cost, exclusive, pack in PRODUCTS:
            category = Category.objects.get(slug=cat_slug)
            _, was_created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    'name': name,
                    'slug': slugify(name),
                    'brand': brand,
                    'category': category,
                    'description': (
                        f'{name}. Supplied by Ah Liki Samoa Wholesale for trade, '
                        f'hospitality and institutional customers. Sold as {pack.lower()}. '
                        f'Request a quote for current trade pricing.'
                    ),
                    'specifications': {'Pack size': pack, 'Category': category.name},
                    'cost_price': Decimal(cost),
                    'is_exclusive': exclusive,
                    'is_active': True,
                    'stock_quantity': 100,
                },
            )
            created += was_created
            updated += not was_created

        self.stdout.write(self.style.SUCCESS(f'Catalogue seeded — created {created}, updated {updated}'))
        self.stdout.write(f'Wholesale products now live: {Product.objects.filter(brand=brand, is_active=True).count()}')
