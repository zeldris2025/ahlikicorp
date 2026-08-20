from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from core.models import Location
from products.models import Product


class Quote(models.Model):
	class Status(models.TextChoices):
		PENDING = 'PENDING', 'Pending'
		QUOTED = 'QUOTED', 'Quoted'
		ACCEPTED = 'ACCEPTED', 'Accepted'
		REJECTED = 'REJECTED', 'Rejected'

	reference = models.CharField(max_length=24, unique=True, editable=False)
	customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='quotes')
	customer_name = models.CharField(max_length=120)
	company = models.CharField(max_length=160, blank=True)
	email = models.EmailField()
	phone = models.CharField(max_length=40)
	delivery_location = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL, related_name='quotes')
	delivery_address = models.CharField(max_length=255, blank=True)
	notes = models.TextField(blank=True)
	internal_notes = models.TextField(blank=True)
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
	tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
	valid_until = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('-created_at',)
		permissions = [('manage_quotes', 'Can price and manage quotes')]

	def save(self, *args, **kwargs):
		if not self.reference:
			from django.utils.crypto import get_random_string
			self.reference = f'AL-{get_random_string(8).upper()}'
		super().save(*args, **kwargs)

	@property
	def subtotal(self):
		return sum(item.line_total for item in self.items.all())

	@property
	def tax_total(self):
		return self.subtotal * self.tax_rate / 100

	@property
	def total(self):
		return self.subtotal + self.tax_total

	def __str__(self):
		return f'{self.reference} - {self.customer_name}'


class QuoteItem(models.Model):
	quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
	product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='quote_items')
	quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

	class Meta:
		constraints = [models.UniqueConstraint(fields=('quote', 'product'), name='unique_quote_product')]

	@property
	def line_total(self):
		return (self.unit_price or 0) * self.quantity

	@property
	def margin(self):
		if self.unit_price is None:
			return None
		return (self.unit_price - self.product.cost_price) * self.quantity

	def __str__(self):
		return f'{self.quantity} x {self.product.name}'
