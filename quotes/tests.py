from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Quote


class QuoteRequestTests(TestCase):
	@patch('quotes.views.notify_finance_team')
	@patch('quotes.views.send_quote_confirmation_email')
	def test_authenticated_request_keeps_customer(self, confirmation_email, finance_email):
		user = User.objects.create_user('customer@example.com', 'customer@example.com', 'password')
		self.client.force_login(user)

		response = self.client.post(reverse('quotes:create'), {
			'customer_name': 'Test Customer',
			'email': 'customer@example.com',
			'phone': '123456',
		})

		quote = Quote.objects.get()
		self.assertRedirects(response, reverse('quotes:confirmation', args=[quote.pk]))
		self.assertEqual(quote.customer, user)
		confirmation_email.assert_called_once_with(quote)
		finance_email.assert_called_once_with(quote)

# Create your tests here.
