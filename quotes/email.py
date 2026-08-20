"""Transactional email for the quote workflow.

Each message is sent as multipart: a plain-text part built from the HTML, plus
the HTML alternative. That keeps them readable in clients that refuse HTML and
improves deliverability over an HTML-only body.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .pdf import generate_quote_pdf

logger = logging.getLogger('quotes')


def _send(subject, template, context, to, attachments=None):
    """Render and send one message, never letting email break the request.

    A failure here must not lose a submitted quote, so problems are logged
    rather than raised — including template errors, which `fail_silently` on
    the send call does not cover because rendering happens first.
    """
    recipients = [addr for addr in (to if isinstance(to, (list, tuple)) else [to]) if addr]
    if not recipients:
        return False

    try:
        html_body = render_to_string(template, context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html_body),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, 'text/html')

        for filename, content, mimetype in (attachments or []):
            message.attach(filename, content, mimetype)

        message.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Failed to send %s to %s', template, recipients)
        return False


def send_quote_confirmation_email(quote):
    """Acknowledge a submitted request. No pricing — none exists yet."""
    return _send(
        subject=f'Quote request received — {quote.reference}',
        template='quotes/email_confirmation.html',
        context={'quote': quote},
        to=quote.email,
    )


def send_quote_to_customer(quote):
    """Send the priced quote with its PDF attached."""
    attachments = []
    try:
        attachments.append((f'{quote.reference}.pdf', generate_quote_pdf(quote), 'application/pdf'))
    except Exception:
        # Still send the summary if the PDF cannot be produced.
        logger.exception('Could not generate PDF for %s; sending without attachment', quote.reference)

    return _send(
        subject=f'Your quote — {quote.reference}',
        template='quotes/email_quote.html',
        context={'quote': quote},
        to=quote.email,
        attachments=attachments,
    )


def notify_finance_team(quote):
    """Alert the internal team that a request is waiting to be priced."""
    return _send(
        subject=f'New quote request — {quote.reference}',
        template='quotes/email_finance_notification.html',
        context={'quote': quote},
        to=getattr(settings, 'QUOTE_NOTIFICATION_EMAIL', ''),
    )
