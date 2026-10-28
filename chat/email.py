"""Email alerts for the live chat.

Mirrors accounts.email: multipart messages, and a failure is logged rather
than raised so a visitor's chat is never lost to a mail server problem.
"""

import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from accounts.permissions import ADMIN_GROUP, FINANCE_GROUP, SALES_GROUP

from .models import Conversation

logger = logging.getLogger('chat')


def agent_emails(channel):
    """Everyone who should hear about a new chat on this channel.

    Sales chats go to every sales girl; staff chats to Finance and Admin. If
    nobody in the group has an email address, the shared sales inbox gets it
    so the visitor is never left waiting unseen.
    """
    groups = [SALES_GROUP] if channel == Conversation.Channel.SALES else [FINANCE_GROUP, ADMIN_GROUP]
    emails = sorted(set(
        User.objects.filter(is_active=True, groups__name__in=groups)
        .exclude(email='')
        .values_list('email', flat=True)
    ))
    return emails or [getattr(settings, 'QUOTE_NOTIFICATION_EMAIL', '')]


def notify_agents_of_new_chat(conversation, first_message=''):
    recipients = [e for e in agent_emails(conversation.channel) if e]
    if not recipients:
        return False

    context = {
        'conversation': conversation,
        'first_message': first_message,
        'site_url': settings.SITE_BASE_URL,
    }
    try:
        html_body = render_to_string('chat/email_new_chat.html', context)
        # Bcc, so one sales girl's address is not handed to all the others.
        message = EmailMultiAlternatives(
            subject=f'{conversation.customer_name} wants help with their order',
            body=strip_tags(html_body),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.DEFAULT_FROM_EMAIL],
            bcc=recipients,
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Failed to send new chat alert for conversation %s', conversation.pk)
        return False
