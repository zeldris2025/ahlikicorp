from django.core.management.base import BaseCommand

from products.models import Brand

# Sector labels, capability statements and accent colours for each company.
# Accent colours are sampled from each company's logo where one exists, then
# darkened until they meet WCAG AA (4.5:1) against white, since they are used
# as heading and tagline text on light backgrounds.
# Sourced from the company overview supplied for the project — adjust in the
# Django admin (Products → Brands) rather than editing this file for one-offs.
PROFILES = {
    'ahliki-wholesale': {
        'sector': 'Wholesale Distribution',
        'accent_color': '#2278ac',
        'tagline': 'Bulk food and non-food distribution across Samoa',
        'description': (
            'The distribution backbone of the group, supplying bulk food, foodstuff and '
            'non-food lines to retailers, hospitality and institutional customers. Our '
            'supply-chain network reaches the entire Samoan market and supports Samoan '
            'communities abroad.'
        ),
        'highlights': [
            'Bulk food & foodstuff',
            'Non-food distribution',
            'Nationwide supply chain',
            'Trade & wholesale pricing',
        ],
    },
    'farmer-joe': {
        'sector': 'Supermarket Retail',
        'accent_color': '#0b818b',
        'tagline': 'Samoa’s trusted supermarket chain',
        'description': (
            'A supermarket chain serving families across Upolu with everyday groceries, '
            'fresh produce and household essentials. Stores at Fugalei, Vaitele, Ululoloa '
            'and Saleimoa put quality within reach of the communities we serve.'
        ),
        'highlights': [
            'Fugalei',
            'Vaitele',
            'Ululoloa',
            'Saleimoa',
        ],
    },
    'taula-beverage': {
        'sector': 'Brewing & Beverages',
        'accent_color': '#007830',
        'tagline': '100% Samoan-owned brewery',
        'description': (
            'A wholly Samoan-owned brewery and beverage producer. Taula produces beers, '
            'soft drinks and bottled water to consistent standards, brewed locally for '
            'the Samoan market and for Samoans overseas.'
        ),
        'highlights': [
            'Beers',
            'Soft drinks',
            'Bottled water',
            '100% Samoan-owned',
        ],
    },
    'burger-bills': {
        'sector': 'Restaurants & Quick Service',
        'accent_color': '#d80000',
        'tagline': 'Quick-service dining done properly',
        'description': (
            'The group’s restaurant and fast-food venture, serving freshly prepared meals '
            'with the same standard of quality and consistency that runs through every '
            'company in the Ah Liki group.'
        ),
        'highlights': [
            'Dine in & takeaway',
            'Freshly prepared',
            'Consistent quality',
        ],
    },
    'tanumapua-farm': {
        'sector': 'Sustainable Agriculture',
        'accent_color': '#5c7b20',
        'tagline': 'Locally grown, sustainably farmed',
        'description': (
            'Our agricultural operation, producing eggs, fresh produce and local chicken '
            'through sustainable farming practices — shortening the supply chain and '
            'keeping value within Samoa.'
        ),
        'highlights': [
            'Eggs',
            'Fresh produce',
            'Local chicken',
            'Sustainable practices',
        ],
    },
}


class Command(BaseCommand):
    help = 'Populate sector, tagline, description and highlights for each group company.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-copy',
            action='store_true',
            help='Only fill in sector and highlights; leave existing tagline/description alone.',
        )

    def handle(self, *args, **options):
        updated = missing = 0

        for slug, profile in PROFILES.items():
            try:
                brand = Brand.objects.get(slug=slug)
            except Brand.DoesNotExist:
                self.stderr.write(self.style.WARNING(f'No company with slug "{slug}" — skipping.'))
                missing += 1
                continue

            brand.sector = profile['sector']
            brand.highlights = profile['highlights']
            brand.accent_color = profile['accent_color']
            if not options['keep_copy']:
                brand.tagline = profile['tagline']
                brand.description = profile['description']

            brand.save()
            self.stdout.write(self.style.SUCCESS(f'Updated {brand.name}'))
            updated += 1

        self.stdout.write('')
        self.stdout.write(f'Updated: {updated}   Missing: {missing}')
