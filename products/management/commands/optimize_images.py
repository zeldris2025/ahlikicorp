"""Compress images that were stored before optimization was in place.

New uploads are handled automatically in the model layer. This command is for
the back catalogue: it re-encodes anything oversized and fills in the missing
listing thumbnails.
"""

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from products.image_utils import generate_thumbnail, optimize_image
from products.models import Brand, ExclusiveBrand, Product, ProductImage


def _kb(n):
	return f'{n / 1024:.0f}KB'


class Command(BaseCommand):
	help = 'Re-compress stored images and generate any missing thumbnails.'

	def add_arguments(self, parser):
		parser.add_argument(
			'--dry-run',
			action='store_true',
			help='Report what would change without writing anything.',
		)

	def handle(self, *args, **options):
		dry = options['dry_run']
		saved = 0

		saved += self._process(
			Product.objects.exclude(image='').only('id', 'image', 'thumbnail'),
			'image', dry, thumbnail=True, label='product images',
		)
		saved += self._process(
			ProductImage.objects.exclude(image='').only('id', 'image'),
			'image', dry, label='gallery images',
		)
		saved += self._process(
			Brand.objects.exclude(logo='').only('id', 'logo'),
			'logo', dry, transparent=True, label='company logos',
		)
		saved += self._process(
			ExclusiveBrand.objects.exclude(logo='').only('id', 'logo'),
			'logo', dry, transparent=True, label='exclusive brand logos',
		)

		verb = 'would be saved' if dry else 'saved'
		self.stdout.write(self.style.SUCCESS(f'\nTotal {verb}: {_kb(saved)}'))

	def _process(self, queryset, field_name, dry, thumbnail=False, transparent=False, label=''):
		self.stdout.write(self.style.MIGRATE_HEADING(f'\n{label}:'))
		saved = 0
		touched = 0

		for obj in queryset.iterator():
			field = getattr(obj, field_name)
			try:
				before = field.size
				field.open('rb')
				optimized = optimize_image(field, keep_transparency=transparent)
				thumb = generate_thumbnail(field, keep_transparency=transparent) if thumbnail else None
			except (FileNotFoundError, OSError) as exc:
				self.stdout.write(self.style.WARNING(f'  skipped {obj.pk}: {exc}'))
				continue
			finally:
				field.close()

			after = optimized.size
			needs_thumb = thumbnail and not obj.thumbnail
			# Only rewrite when it is actually a win, so repeated runs are a no-op.
			if after >= before * 0.95 and not needs_thumb:
				continue

			touched += 1
			# Re-encoding an already-small JPEG can make it bigger; in that
			# case leave the stored file alone and just add the thumbnail.
			shrinks = after < before
			if shrinks:
				saved += before - after
				change = f'{_kb(before)} -> {_kb(after)}'
			else:
				change = f'{_kb(before)} kept (re-encode would grow it), thumbnail only'

			if dry:
				self.stdout.write(f'  {obj.pk}: {change}')
				continue

			if shrinks:
				# save=False so the row is written once, by the save() below.
				field.save(optimized.name, ContentFile(optimized.read()), save=False)
			if thumb is not None:
				obj.thumbnail = thumb
			obj.save()
			self.stdout.write(f'  {obj.pk}: {change}')

		self.stdout.write(f'  {touched} updated')
		return saved
