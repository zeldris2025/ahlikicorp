import json

from django.contrib.auth.models import Group, User
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import Brand, Category, Product
from quotes.models import Quote

from .models import Conversation, Message


def post(client, name, data=None, args=None):
    return client.post(
        reverse(name, args=args), json.dumps(data or {}), content_type='application/json',
    )


# Plain static storage, so rendering pages does not depend on collectstatic.
@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class ChatFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.sales_group = Group.objects.get(name='Sales Girls')  # created by migration
        self.finance_group, _ = Group.objects.get_or_create(name='Finance')

        self.mele = User.objects.create_user('mele', 'mele@ahliki.com', 'pw', first_name='Mele')
        self.sina = User.objects.create_user('sina', 'sina@ahliki.com', 'pw', first_name='Sina')
        for u in (self.mele, self.sina):
            u.groups.add(self.sales_group)
        self.finance = User.objects.create_user('fin', 'fin@ahliki.com', 'pw')
        self.finance.groups.add(self.finance_group)

        brand = Brand.objects.create(name='Taula', slug='taula', tagline='t', description='d')
        category = Category.objects.create(name='Drinks', slug='drinks')
        self.product = Product.objects.create(
            name='Taula Lager 330ml', slug='taula-lager', sku='TL-330',
            brand=brand, category=category, description='Beer',
        )

    def start(self, channel='sales', **extra):
        data = {'channel': channel, 'name': 'Ioane Tavita', 'phone': '+685 7712345',
                'email': 'ioane@example.com', 'message': 'I need 20 cartons'}
        data.update(extra)
        return post(self.client, 'chat:start', data)

    def test_contact_details_are_required(self):
        res = self.start(name='', phone='12', email='nope')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(set(res.json()['errors']), {'name', 'phone', 'email'})
        self.assertFalse(Conversation.objects.exists())

    def test_start_emails_every_sales_girl(self):
        with self.captureOnCommitCallbacks(execute=True):
            res = self.start()
        self.assertEqual(res.status_code, 200)

        conversation = Conversation.objects.get()
        self.assertEqual(conversation.email, 'ioane@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(set(mail.outbox[0].bcc), {'mele@ahliki.com', 'sina@ahliki.com'})
        self.assertIn('Ioane Tavita', mail.outbox[0].subject)

    def test_staff_chat_goes_to_finance_not_sales(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.start(channel='staff')
        self.assertEqual(mail.outbox[0].bcc, ['fin@ahliki.com'])

        # And sales girls cannot open it.
        self.client.force_login(self.mele)
        conversation = Conversation.objects.get()
        res = self.client.get(reverse('chat:api_detail', args=[conversation.pk]))
        self.assertEqual(res.status_code, 404)

    def test_visitor_only_reaches_their_own_chat(self):
        self.start()
        other = self.client_class()
        res = other.get(reverse('chat:poll'))
        self.assertIsNone(res.json()['conversation'])

    def test_full_conversation_and_quote(self):
        self.start()
        conversation = Conversation.objects.get()

        agent = self.client_class()
        agent.force_login(self.mele)
        self.assertEqual(agent.get(reverse('chat:inbox')).status_code, 200)

        listing = agent.get(reverse('chat:api_list') + '?tab=waiting').json()
        self.assertEqual(listing['counts']['waiting'], 1)
        self.assertEqual(listing['items'][0]['unread'], 1)

        # First reply claims the chat.
        post(agent, 'chat:api_send', {'body': 'Talofa!'}, [conversation.pk])
        conversation.refresh_from_db()
        self.assertEqual(conversation.assigned_to, self.mele)

        # Sharing a product shows up on the visitor side as a card.
        post(agent, 'chat:api_send', {'product_id': self.product.pk}, [conversation.pk])
        visitor_view = self.client.get(reverse('chat:poll')).json()
        self.assertEqual(visitor_view['conversation']['agent'], 'Mele')
        self.assertEqual(visitor_view['messages'][-1]['product']['sku'], 'TL-330')

        post(self.client, 'chat:send', {'body': 'Yes please, 20 cartons'})

        with self.captureOnCommitCallbacks(execute=True):
            res = post(agent, 'chat:api_quote', {
                'items': [{'product_id': self.product.pk, 'quantity': 20}],
                'notes': 'Deliver to Vaitele',
            }, [conversation.pk])
        self.assertEqual(res.status_code, 200)

        quote = Quote.objects.get()
        self.assertEqual((quote.customer_name, quote.email, quote.phone),
                         ('Ioane Tavita', 'ioane@example.com', '+685 7712345'))
        self.assertEqual(quote.items.get().quantity, 20)
        conversation.refresh_from_db()
        self.assertEqual(conversation.quote, quote)
        self.assertTrue(Message.objects.filter(body__contains=quote.reference).exists())

        post(agent, 'chat:api_status', {'action': 'close'}, [conversation.pk])
        res = post(self.client, 'chat:send', {'body': 'hello?'})
        self.assertEqual(res.status_code, 400)

    def test_inbox_is_closed_to_customers(self):
        customer = User.objects.create_user('c', 'c@example.com', 'pw')
        self.client.force_login(customer)
        self.assertEqual(self.client.get(reverse('chat:inbox')).status_code, 403)
        self.assertEqual(self.client.get(reverse('chat:api_list')).status_code, 403)

    def test_sales_girl_signs_in_to_the_inbox(self):
        res = self.client.post(reverse('accounts:login'), {'email': 'mele', 'password': 'pw'})
        self.assertRedirects(res, reverse('chat:inbox'))

    def test_start_is_rate_limited(self):
        for i in range(5):
            self.start()
            post(self.client, 'chat:end')
        self.assertEqual(self.start().status_code, 429)
