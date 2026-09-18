from django.db import models
from django.urls import reverse
from django.utils import timezone

from .image_utils import generate_thumbnail, optimize_image


def _optimize_field(instance, field_name, keep_transparency=False):
	"""Compress a freshly uploaded file in place, before it reaches storage.

	Django marks a field ``_committed = False`` only while it holds a new file
	that has not been written yet, which is exactly when — and only when — we
	want to re-encode. Without that guard every ordinary edit would recompress
	the stored image again and slowly degrade it.
	"""
	field = getattr(instance, field_name, None)
	if not field or field._committed:
		return False

	optimized = optimize_image(field, keep_transparency=keep_transparency)
	if optimized:
		setattr(instance, field_name, optimized)
	return True


class Brand(models.Model):
	"""An operating company within the Ah Liki Investment Corporation group.

	Named ``Brand`` for historical reasons; presented to visitors as a
	"company" throughout the site.
	"""

	name = models.CharField(max_length=120)
	slug = models.SlugField(unique=True)
	tagline = models.CharField(max_length=180)
	description = models.TextField()
	sector = models.CharField(
		max_length=80,
		blank=True,
		help_text='Short sector label shown above the company name, e.g. "Wholesale Distribution".',
	)
	highlights = models.JSONField(
		default=list,
		blank=True,
		help_text='List of short capability statements shown as chips on the company section.',
	)
	accent_color = models.CharField(max_length=7, default='#0A6B4E')
	logo = models.ImageField(upload_to='brands/', blank=True)
	sort_order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ('sort_order', 'name')

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		# Company logos are usually transparent PNGs, so they must not be
		# flattened onto a white rectangle.
		_optimize_field(self, 'logo', keep_transparency=True)
		super().save(*args, **kwargs)

	def get_absolute_url(self):
		return reverse('core:company_detail', kwargs={'slug': self.slug})


class Category(models.Model):
	name = models.CharField(max_length=100)
	slug = models.SlugField(unique=True)

	class Meta:
		ordering = ('name',)
		verbose_name_plural = 'categories'

	def __str__(self):
		return self.name


class Product(models.Model):
	name = models.CharField(max_length=160)
	slug = models.SlugField(unique=True)
	sku = models.CharField(max_length=60, unique=True)
	brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
	description = models.TextField()
	specifications = models.JSONField(default=dict, blank=True)
	image = models.ImageField(upload_to='products/', blank=True)
	thumbnail = models.ImageField(
		upload_to='products/thumbs/',
		blank=True,
		editable=False,
		help_text='Generated automatically from the image; used on listing pages.',
	)
	is_exclusive = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	stock_quantity = models.PositiveIntegerField(default=0)
	cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('name',)
		indexes = [models.Index(fields=('is_active', 'is_exclusive'))]

	def __str__(self):
		return f'{self.name} ({self.sku})'

	def save(self, *args, **kwargs):
		# Ensure slug is always generated before saving
		if not self.slug or not self.slug.strip():
			from django.utils.text import slugify
			base = slugify(self.name)[:45] or 'product'
			slug, n = base, 2
			existing = Product.objects.exclude(pk=self.pk) if self.pk else Product.objects.all()
			while existing.filter(slug=slug).exists():
				slug = f'{base}-{n}'
				n += 1
			self.slug = slug

		# Ensure SKU is always generated before saving
		if not self.sku or not self.sku.strip():
			from django.utils.text import slugify
			base = slugify(self.name).upper()[:20] or 'PRODUCT'
			sku, n = base, 2
			existing = Product.objects.exclude(pk=self.pk) if self.pk else Product.objects.all()
			while existing.filter(sku__iexact=sku).exists():
				sku = f'{base}-{n}'
				n += 1
			self.sku = sku

		# Compress the upload and derive the small listing image from it, so
		# the catalogue grid never has to download full-size photos.
		if _optimize_field(self, 'image'):
			self.thumbnail = generate_thumbnail(self.image)
		elif not self.image:
			self.thumbnail = ''

		super().save(*args, **kwargs)

	@property
	def list_image(self):
		"""The image to use anywhere the product appears as a small card.

		Falls back to the full image for records saved before thumbnails
		existed, so nothing disappears from the catalogue mid-backfill.
		"""
		return self.thumbnail or self.image

	def get_absolute_url(self):
		return reverse('products:detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
	image = models.ImageField(upload_to='products/gallery/')
	alt_text = models.CharField(max_length=180)
	sort_order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ('sort_order',)

	def save(self, *args, **kwargs):
		_optimize_field(self, 'image')
		super().save(*args, **kwargs)


class ExclusiveBrand(models.Model):
	"""A supplier brand the group is the sole authorised distributor for.

	These are the labels we carry on exclusive terms, not group companies.
	They appear as a scrolling logo marquee on the home page, below the
	group company sections.
	"""

	name = models.CharField(max_length=120)
	logo = models.ImageField(upload_to='exclusive/')
	website = models.URLField(blank=True, help_text='Optional. Turns the logo into a link.')
	note = models.CharField(
		max_length=120,
		blank=True,
		help_text='Optional short label shown under the logo, e.g. "Beverages".',
	)
	sort_order = models.PositiveSmallIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ('sort_order', 'name')
		verbose_name = 'exclusive brand'
		verbose_name_plural = 'exclusive brands'

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		# Supplier logos ride in a marquee on the home page; keep their
		# transparency so they sit on the page background, not on white.
		_optimize_field(self, 'logo', keep_transparency=True)
		super().save(*args, **kwargs)


class PromotionQuerySet(models.QuerySet):
	def live(self):
		"""Promotions that are switched on and inside their date window.

		A blank start or end means "no bound on that side", so a promotion
		with neither date runs until someone withdraws it.
		"""
		now = timezone.now()
		return self.filter(
			models.Q(is_active=True)
			& (models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now))
			& (models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now))
		)


class Promotion(models.Model):
	"""A promotion slide on the home page hero.

	The hero is a slideshow rather than a grid of cards: a promotion is sold
	by its photography, and one full-width stage per offer carries an image
	far better than four thumbnails competing for the same row.
	"""

	kicker = models.CharField(
		max_length=28,
		blank=True,
		help_text='Small label above the headline, e.g. "This week" or "New in".',
	)
	headline = models.CharField(
		max_length=60,
		help_text='Keep it to a few words — it is set very large on the slide.',
	)
	subtext = models.CharField(
		max_length=100,
		blank=True,
		help_text='Optional single supporting line. Leave empty if the headline says it.',
	)
	image = models.ImageField(
		upload_to='promotions/',
		help_text='Landscape photo, at least 1600px wide. It fills the whole slide.',
	)
	cta_label = models.CharField(max_length=24, default='See the deal')
	cta_url = models.CharField(
		max_length=300,
		blank=True,
		help_text='Where the button goes, e.g. /products/?category=3. Blank hides the button.',
	)
	accent_color = models.CharField(max_length=7, default='#8BC53F')
	starts_at = models.DateTimeField(null=True, blank=True, help_text='Optional. Blank means live now.')
	ends_at = models.DateTimeField(null=True, blank=True, help_text='Optional. Blank means no end date.')
	is_active = models.BooleanField(default=True)
	sort_order = models.PositiveSmallIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	objects = PromotionQuerySet.as_manager()

	class Meta:
		ordering = ('sort_order', '-created_at')

	def __str__(self):
		return self.headline

	def save(self, *args, **kwargs):
		# Promotion photos are full-bleed JPEGs; flattening them is fine and
		# keeps the hero's largest asset small.
		_optimize_field(self, 'image')
		super().save(*args, **kwargs)
