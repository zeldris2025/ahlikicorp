from django.test import TestCase
from django.urls import reverse


class PublicPageTests(TestCase):
	def test_public_pages_render_with_shared_stylesheet(self):
		pages = (
			'core:home',
			'core:about',
			'core:brands',
			'core:locations',
			'core:contact',
			'products:list',
			'quotes:create',
			'accounts:login',
			'accounts:register',
		)

		for page in pages:
			with self.subTest(page=page):
				response = self.client.get(reverse(page))
				self.assertEqual(response.status_code, 200)
				self.assertContains(response, '/static/css/style.css')

# Create your tests here.
