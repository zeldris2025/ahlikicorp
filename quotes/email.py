from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .pdf import generate_quote_pdf

def send_quote_confirmation_email(quote):
    """Send quote submission confirmation to customer."""
    subject = f'Quote Request Received - {quote.reference}'
    html_message = render_to_string('quotes/email_confirmation.html', {'quote': quote})

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[quote.email],
        content_subtype='html',
    )
    email.send(fail_silently=True)

def send_quote_to_customer(quote):
    """Send generated quote PDF to customer."""
    subject = f'Your Quote - {quote.reference}'
    html_message = render_to_string('quotes/email_quote.html', {'quote': quote})
    pdf_content = generate_quote_pdf(quote)

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[quote.email],
        content_subtype='html',
    )
    email.attach(f'{quote.reference}.pdf', pdf_content, 'application/pdf')
    email.send(fail_silently=True)

def notify_finance_team(quote):
    """Notify finance team of new quote submission."""
    if not hasattr(settings, 'QUOTE_NOTIFICATION_EMAIL'):
        return

    subject = f'New Quote Submitted - {quote.reference}'
    html_message = render_to_string('quotes/email_finance_notification.html', {'quote': quote})

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.QUOTE_NOTIFICATION_EMAIL],
        content_subtype='html',
    )
    email.send(fail_silently=True)
