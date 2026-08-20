from django.db import models
from django.urls import reverse


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

	def get_absolute_url(self):
		return reverse('products:detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
	image = models.ImageField(upload_to='products/gallery/')
	alt_text = models.CharField(max_length=180)
	sort_order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ('sort_order',)
