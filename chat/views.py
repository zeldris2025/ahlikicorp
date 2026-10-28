"""Visitor side of the live chat, called from the assistant widget.

A visitor can only ever reach the conversation stored in their own session,
so there is no conversation id in these URLs to guess.
"""

import json

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .email import notify_agents_of_new_chat
from .models import Conversation, Message
from .serializers import conversation_dict, message_dict

SESSION_KEY = 'chat_conversation_id'
CONTACT_KEY = 'chat_contact'
MAX_MESSAGE = 2000
# Each new chat emails every sales girl, so cap how often one address can
# start them.
STARTS_PER_HOUR = 5


def read_json(request):
    try:
        return json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return {}


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')


def _session_conversation(request):
    pk = request.session.get(SESSION_KEY)
    if not pk:
        return None
    return (
        Conversation.objects.select_related('assigned_to')
        .filter(pk=pk).first()
    )


def _messages_after(conversation, after):
    qs = conversation.messages.select_related('agent', 'product__brand', 'product__category')
    if after:
        qs = qs.filter(pk__gt=after)
    return [message_dict(m) for m in qs]


def _prefill(request):
    """Contact details to pre-fill the form: last used, else the account's."""
    saved = request.session.get(CONTACT_KEY)
    if saved:
        return saved
    user = request.user
    if not user.is_authenticated:
        return {'name': '', 'phone': '', 'email': ''}
    profile = getattr(user, 'profile', None)
    return {
        'name': user.get_full_name() or '',
        'phone': getattr(profile, 'phone', '') or '',
        'email': user.email or '',
    }


@require_GET
def current(request):
    """Restore the visitor's chat after a page change or reload."""
    conversation = _session_conversation(request)
    if conversation is None:
        return JsonResponse({'conversation': None, 'contact': _prefill(request)})
    return JsonResponse({
        'conversation': conversation_dict(conversation),
        'messages': _messages_after(conversation, 0),
        'contact': _prefill(request),
    })


@require_POST
def start(request):
    data = read_json(request)
    errors = {}

    channel = data.get('channel')
    if channel not in Conversation.Channel.values:
        errors['channel'] = 'Choose who you would like to talk to.'

    name = (data.get('name') or '').strip()[:120]
    if len(name) < 2:
        errors['name'] = 'Please tell us your name.'

    phone = (data.get('phone') or '').strip()[:40]
    if sum(c.isdigit() for c in phone) < 5:
        errors['phone'] = 'Please enter a phone number we can reach you on.'

    email = (data.get('email') or '').strip()[:254]
    try:
        validate_email(email)
    except ValidationError:
        errors['email'] = 'Please enter a valid email address.'

    first = (data.get('message') or '').strip()[:MAX_MESSAGE]

    if errors:
        return JsonResponse({'ok': False, 'errors': errors}, status=400)

    # One open chat per visitor: starting again returns the one in progress.
    existing = _session_conversation(request)
    if existing and existing.is_open:
        return JsonResponse({
            'ok': True,
            'conversation': conversation_dict(existing),
            'messages': _messages_after(existing, 0),
        })

    rate_key = f'chat-starts:{_client_ip(request)}'
    starts = cache.get(rate_key, 0)
    if starts >= STARTS_PER_HOUR:
        return JsonResponse({
            'ok': False,
            'errors': {'form': 'You have started several chats already. Please wait a little and try again, or call us.'},
        }, status=429)
    cache.set(rate_key, starts + 1, 3600)

    with transaction.atomic():
        conversation = Conversation.objects.create(
            channel=channel,
            customer_name=name,
            phone=phone,
            email=email,
            customer=request.user if request.user.is_authenticated else None,
        )
        who = 'one of our sales team' if channel == Conversation.Channel.SALES else 'a member of our staff'
        Message.objects.create(
            conversation=conversation,
            sender=Message.Sender.SYSTEM,
            body=(
                f'Thanks {name.split()[0]}! We have let {who} know and someone will be with you shortly. '
                f'If you have to leave, we will follow up at {email}.'
            ),
        )
        if first:
            Message.objects.create(conversation=conversation, sender=Message.Sender.CUSTOMER, body=first)

    request.session[SESSION_KEY] = conversation.pk
    request.session[CONTACT_KEY] = {'name': name, 'phone': phone, 'email': email}

    transaction.on_commit(lambda: notify_agents_of_new_chat(conversation, first))

    return JsonResponse({
        'ok': True,
        'conversation': conversation_dict(conversation),
        'messages': _messages_after(conversation, 0),
    })


@require_GET
def poll(request):
    conversation = _session_conversation(request)
    if conversation is None:
        return JsonResponse({'conversation': None, 'messages': []})
    try:
        after = int(request.GET.get('after', 0))
    except ValueError:
        after = 0
    return JsonResponse({
        'conversation': conversation_dict(conversation),
        'messages': _messages_after(conversation, after),
    })


@require_POST
def send(request):
    conversation = _session_conversation(request)
    if conversation is None or not conversation.is_open:
        return JsonResponse({'ok': False, 'error': 'This chat has ended.'}, status=400)

    body = (read_json(request).get('body') or '').strip()[:MAX_MESSAGE]
    if not body:
        return JsonResponse({'ok': False, 'error': 'Type a message first.'}, status=400)

    message = Message.objects.create(conversation=conversation, sender=Message.Sender.CUSTOMER, body=body)
    Conversation.objects.filter(pk=conversation.pk).update(last_message_at=message.created_at)
    return JsonResponse({'ok': True, 'message': message_dict(message)})


@require_POST
def end(request):
    conversation = _session_conversation(request)
    if conversation and conversation.is_open:
        now = timezone.now()
        Message.objects.create(
            conversation=conversation, sender=Message.Sender.SYSTEM,
            body=f'{conversation.customer_name} ended the chat.',
        )
        Conversation.objects.filter(pk=conversation.pk).update(
            status=Conversation.Status.CLOSED, closed_at=now, last_message_at=now,
        )
    # Forget it, so the assistant offers a fresh start next time.
    request.session.pop(SESSION_KEY, None)
    return JsonResponse({'ok': True})
