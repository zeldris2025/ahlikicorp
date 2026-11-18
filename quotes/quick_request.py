"""Quote requests from the floating "Request a quote" widget.

Open to any visitor, unlike the basket checkout, and the items are typed in
freely rather than picked from the catalogue. They are written into the
quote's notes, since a QuoteItem must point at a Product; Finance turns them
into priced lines with the existing Add items page.
"""

import json

from django import forms
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.captcha import verify_recaptcha

from .email import notify_finance_team, send_quote_confirmation_email
from .models import Quote

MAX_ITEMS = 30
# Requests allowed from one address per hour, to keep scripted spam out of
# the Finance inbox.
HOURLY_LIMIT = 5


class QuickQuoteForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=40)
    email = forms.EmailField()
    company = forms.CharField(max_length=160, required=False)
    # Hidden from people; anything typed here came from a bot.
    website = forms.CharField(required=False)


def _clean_items(raw):
    """Return [(description, quantity)], skipping blank rows."""
    items = []
    for row in raw if isinstance(raw, list) else []:
        if not isinstance(row, dict):
            continue
        description = str(row.get('item', '')).strip()[:200]
        if not description:
            continue
        try:
            quantity = int(row.get('qty') or 1)
        except (TypeError, ValueError):
            quantity = 1
        items.append((description, min(max(quantity, 1), 100000)))
    return items[:MAX_ITEMS]


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')


@require_POST
def quick_request(request):
    try:
        payload = json.loads(request.body or b'{}')
    except ValueError:
        return JsonResponse({'errors': {'form': 'Something went wrong. Please try again.'}}, status=400)

    form = QuickQuoteForm(payload)
    items = _clean_items(payload.get('items'))
    errors = {}
    if not form.is_valid():
        errors.update({field: messages[0] for field, messages in form.errors.items()})
    if not items:
        errors['items'] = 'Add at least one item you would like a price for.'
    if errors:
        return JsonResponse({'errors': errors}, status=400)

    data = form.cleaned_data
    if data['website']:
        # Look successful so the bot moves on, but save nothing.
        return JsonResponse({'reference': 'AL-RECEIVED'})

    if not verify_recaptcha(payload.get('captcha'), _client_ip(request)):
        return JsonResponse(
            {'errors': {'captcha': 'Please tick "I\'m not a robot" before sending.'}},
            status=400,
        )

    throttle_key = f'quick_quote_{_client_ip(request)}'
    count = cache.get(throttle_key, 0)
    if count >= HOURLY_LIMIT:
        return JsonResponse(
            {'errors': {'form': 'You have sent several requests already. Please try again later or call us.'}},
            status=429,
        )
    cache.set(throttle_key, count + 1, 3600)

    lines = '\n'.join(f'- {qty} x {description}' for description, qty in items)
    notes = f'Items requested:\n{lines}'

    quote = Quote.objects.create(
        customer=request.user if request.user.is_authenticated else None,
        customer_name=data['name'],
        company=data['company'],
        email=data['email'],
        phone=data['phone'],
        notes=notes,
    )
    send_quote_confirmation_email(quote)
    notify_finance_team(quote)
    return JsonResponse({'reference': quote.reference})
