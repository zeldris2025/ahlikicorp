"""Image optimization utilities.

Every image that enters the site is compressed on the way in, so a staff
member uploading a 6MB phone photo does not turn into a 6MB download for
every visitor. The work happens in the model layer (see ``models.py``) so
that it applies no matter which door the upload came through — staff portal,
Django Admin, or a management command.

Sizes and quality come from ``settings.IMAGE_OPTIMIZATION`` so they can be
tuned without touching code.
"""

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

DEFAULTS = {
	'MAX_WIDTH': 1200,
	'MAX_HEIGHT': 1200,
	'QUALITY': 85,
	'THUMBNAIL_SIZE': (300, 300),
	'THUMBNAIL_QUALITY': 75,
}


def _config(key):
	return getattr(settings, 'IMAGE_OPTIMIZATION', {}).get(key, DEFAULTS[key])


def _prepare(image_file, keep_transparency):
	"""Open an upload as a Pillow image, upright and in a saveable mode."""
	image_file.seek(0)
	img = Image.open(image_file)

	# Phone cameras record orientation in EXIF rather than in the pixels.
	img = ImageOps.exif_transpose(img)

	if keep_transparency and img.mode in ('RGBA', 'LA', 'P'):
		return img.convert('RGBA'), 'PNG'

	if img.mode in ('RGBA', 'LA', 'P'):
		# Flatten onto white; JPEG has no alpha channel.
		img = img.convert('RGBA')
		background = Image.new('RGB', img.size, (255, 255, 255))
		background.paste(img, mask=img.split()[-1])
		img = background
	elif img.mode != 'RGB':
		img = img.convert('RGB')

	return img, 'JPEG'


def _encode(img, fmt, quality):
	buffer = BytesIO()
	if fmt == 'PNG':
		img.save(buffer, format='PNG', optimize=True)
	else:
		img.save(buffer, format='JPEG', quality=quality, optimize=True, progressive=True)
	return buffer.getvalue()


def _rename(name, fmt, suffix=''):
	"""Give the file the extension it actually holds.

	The old behaviour kept the uploaded name, so a ``.png`` upload was stored
	as ``.png`` while containing JPEG bytes.
	"""
	stem = Path(name or 'image').stem or 'image'
	return f'{stem}{suffix}.{"png" if fmt == "PNG" else "jpg"}'


def optimize_image(image_file, max_width=None, max_height=None, quality=None,
                   keep_transparency=False):
	"""Compress an uploaded image, returning a ``ContentFile`` ready to store.

	Set ``keep_transparency`` for logos, which are usually PNGs that must not
	be flattened onto a white box.
	"""
	if not image_file:
		return None

	max_width = max_width or _config('MAX_WIDTH')
	max_height = max_height or _config('MAX_HEIGHT')
	quality = quality or _config('QUALITY')

	img, fmt = _prepare(image_file, keep_transparency)
	img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

	return ContentFile(_encode(img, fmt, quality),
	                   name=_rename(getattr(image_file, 'name', ''), fmt))


def generate_thumbnail(image_file, size=None, quality=None, keep_transparency=False):
	"""Build the small image used by catalogue cards and baskets.

	Listing pages show images at roughly 300px wide; serving the full 1200px
	file there is the single biggest avoidable cost on the catalogue page,
	where 24 of them load at once.
	"""
	if not image_file:
		return None

	size = tuple(size or _config('THUMBNAIL_SIZE'))
	quality = quality or _config('THUMBNAIL_QUALITY')

	img, fmt = _prepare(image_file, keep_transparency)
	img.thumbnail(size, Image.Resampling.LANCZOS)

	return ContentFile(_encode(img, fmt, quality),
	                   name=_rename(getattr(image_file, 'name', ''), fmt, suffix='_thumb'))
