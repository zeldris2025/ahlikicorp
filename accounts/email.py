"""Transactional email for the customer application workflow.

Mirrors quotes.email: multipart messages, and a failure is logged rather than
raised so a submitted application is never lost to a mail server problem.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger('accounts')


def _send(subject, template, context, to):
    recipients = [addr for addr in (to if isinstance(to, (list, tuple)) else [to]) if addr]
    if not recipients:
        return False

    context.setdefault('site_url', settings.SITE_BASE_URL)
    try:
        html_body = render_to_string(template, context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html_body),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html_body, 'text/html')
        message.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Failed to send %s to %s', template, recipients)
        return False


def send_application_received(application):
    """Tell the applicant their details are with us and under review."""
    return _send(
        subject='We have your trade account application',
        template='accounts/email_application_received.html',
        context={'application': application},
        to=application.email,
    )


def notify_staff_of_application(application):
    """Alert whoever reviews applications that one is waiting."""
    return _send(
        subject=f'New trade account application — {application.organisation}',
        template='accounts/email_application_staff.html',
        context={'application': application},
        to=settings.APPLICATION_NOTIFICATION_EMAIL,
    )


def send_application_approved(application, username, password):
    """Send the sign-in details for a newly created account.

    The password is passed in rather than read back: it only exists in memory
    between being generated and being sent, and is stored hashed.
    """
    return _send(
        subject='Your Ah Liki trade account is ready',
        template='accounts/email_application_approved.html',
        context={'application': application, 'username': username, 'password': password},
        to=application.email,
    )


def send_application_rejected(application, include_notes=False):
    """Tell an applicant the account was not opened."""
    return _send(
        subject='About your Ah Liki trade account application',
        template='accounts/email_application_rejected.html',
        context={'application': application, 'include_notes': include_notes},
        to=application.email,
    )
