from django.db import models


class Location(models.Model):
	name = models.CharField(max_length=120)
	company = models.ForeignKey(
		'products.Brand',
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='locations',
		help_text='Which group company operates from this site.',
	)
	address = models.CharField(max_length=255)
	island = models.CharField(max_length=40, default='Upolu')
	phone = models.CharField(max_length=40, blank=True)
	email = models.EmailField(blank=True)
	opening_hours = models.CharField(max_length=160, blank=True)
	latitude = models.DecimalField(
		max_digits=9, decimal_places=6, null=True, blank=True,
		help_text='Decimal degrees. Sites without coordinates are listed but not pinned on the map.',
	)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	is_headquarters = models.BooleanField(default=False)
	sort_order = models.PositiveSmallIntegerField(default=0)

	class Meta:
		ordering = ('sort_order', 'name')

	def __str__(self):
		return self.name


class NewsletterSubscriber(models.Model):
	email = models.EmailField(unique=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.email


class ContactMessage(models.Model):
	name = models.CharField(max_length=120)
	email = models.EmailField()
	phone = models.CharField(max_length=40, blank=True)
	subject = models.CharField(max_length=160)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	resolved_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ('-created_at',)
