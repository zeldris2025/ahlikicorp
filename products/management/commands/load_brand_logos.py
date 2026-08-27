from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from products.models import Brand

# Maps a brand slug to the logo filename shipped in static/images/.
LOGO_MAP = {
    'ahliki-wholesale': 'ahliki_logo.png',
    'burger-bills': 'burgerbills_logo.png',
    'taula-beverage': 'taula_logo.png',
    'farmer-joe': 'farmerjoe_logo.png',
    'tanumapua-farm': 'tanumapua_logo.png',
}


class Command(BaseCommand):
    help = 'Attach the brand logo images in static/images/ to their Brand records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Replace logos on brands that already have one.',
        )

    def handle(self, *args, **options):
        source_dir = Path(settings.BASE_DIR) / 'static' / 'images'
        attached = skipped = missing = 0

        for slug, filename in LOGO_MAP.items():
            try:
                brand = Brand.objects.get(slug=slug)
            except Brand.DoesNotExist:
                self.stderr.write(self.style.WARNING(f'No brand with slug "{slug}" — skipping.'))
                missing += 1
                continue

            source = source_dir / filename
            if not source.exists():
                self.stderr.write(self.style.WARNING(f'{filename} not found in {source_dir} — skipping.'))
                missing += 1
                continue

            if brand.logo and not options['force']:
                self.stdout.write(f'{brand.name} already has a logo — use --force to replace.')
                skipped += 1
                continue

            with source.open('rb') as fh:
                brand.logo.save(filename, File(fh), save=True)

            self.stdout.write(self.style.SUCCESS(f'Attached {filename} to {brand.name}'))
            attached += 1

        self.stdout.write('')
        self.stdout.write(f'Attached: {attached}   Skipped: {skipped}   Missing: {missing}')

        without = Brand.objects.filter(logo='').order_by('sort_order', 'name')
        if without.exists():
            self.stdout.write('')
            self.stdout.write('Brands still without a logo (they fall back to an icon):')
            for brand in without:
                self.stdout.write(f'  - {brand.name}')
