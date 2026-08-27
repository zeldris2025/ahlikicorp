"""Ingest exclusive-distribution logos dropped into a folder.

Anyone can add a logo to the home page marquee by copying an image into
``static/images/exclusive/`` and running this command — no admin login and no
code change. The brand name is derived from the filename, so
``coca_cola.png`` becomes "Coca Cola".
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from products.models import ExclusiveBrand

EXTENSIONS = ('*.png', '*.jpg', '*.jpeg', '*.webp', '*.svg')


class Command(BaseCommand):
    help = 'Create ExclusiveBrand records from the images in static/images/exclusive/.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            default='static/images/exclusive',
            help='Folder to read logos from, relative to the project root.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Replace the logo on brands that already have one.',
        )

    def handle(self, *args, **options):
        source_dir = Path(settings.BASE_DIR) / options['folder']
        if not source_dir.is_dir():
            self.stderr.write(self.style.ERROR(f'{source_dir} does not exist.'))
            return

        files = sorted(
            path
            for pattern in EXTENSIONS
            for path in source_dir.glob(pattern)
        )
        if not files:
            self.stdout.write(f'No images found in {source_dir}.')
            return

        created = updated = skipped = 0

        for order, source in enumerate(files, start=1):
            name = source.stem.replace('_', ' ').replace('-', ' ').strip().title()
            brand, was_created = ExclusiveBrand.objects.get_or_create(
                name=name,
                defaults={'sort_order': order},
            )

            if brand.logo and not options['force']:
                self.stdout.write(f'{name} already has a logo — use --force to replace.')
                skipped += 1
                continue

            with source.open('rb') as fh:
                brand.logo.save(source.name, File(fh), save=True)

            if was_created:
                self.stdout.write(self.style.SUCCESS(f'Added {name}'))
                created += 1
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated logo for {name}'))
                updated += 1

        self.stdout.write('')
        self.stdout.write(f'Created: {created}   Updated: {updated}   Skipped: {skipped}')
