"""Live chat between a website visitor and the sales or staff team.

A visitor does not need an account: the assistant asks for a name, phone and
email before the chat starts, which is what any quote raised from the chat is
sent to. The conversation is tied to the visitor's session, so only the
browser that started it can read it.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    class Channel(models.TextChoices):
        SALES = 'sales', 'Sales team'
        STAFF = 'staff', 'Staff'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.SALES)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    # Who the visitor is, collected before the first message.
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    email = models.EmailField()
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='chat_conversations',
        help_text='Set when the visitor was signed in.',
    )

    # The agent looking after the chat. Claimed on their first reply.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_chats',
    )
    quote = models.ForeignKey(
        'quotes.Quote', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='chat_conversations',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    # Bumped on every message, so the inbox can sort by recent activity.
    last_message_at = models.DateTimeField(default=timezone.now, db_index=True)
    # When an agent last viewed the chat; customer messages after it are unread.
    agent_read_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-last_message_at',)

    def __str__(self):
        return f'#{self.pk} {self.customer_name} ({self.get_channel_display()})'

    @property
    def is_open(self):
        return self.status == self.Status.OPEN

    def unread_for_agents(self):
        qs = self.messages.filter(sender=Message.Sender.CUSTOMER)
        if self.agent_read_at:
            qs = qs.filter(created_at__gt=self.agent_read_at)
        return qs.count()


class Message(models.Model):
    class Sender(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        AGENT = 'agent', 'Agent'
        SYSTEM = 'system', 'System'

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=Sender.choices)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='chat_messages',
    )
    body = models.TextField(blank=True)
    # A product the agent shared; shown to the customer as a card.
    product = models.ForeignKey(
        'products.Product', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='chat_messages',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'pk')

    def __str__(self):
        return f'{self.get_sender_display()}: {self.body[:40]}'
