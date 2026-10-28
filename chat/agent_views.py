"""Agent side of the live chat: the three-panel inbox and its JSON endpoints.

Sales girls see the sales channel; Finance and Admin see every chat. Every
endpoint checks this server-side, not just the page that links to it.
"""

import functools

from django.db import transaction
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from accounts.permissions import (
    ADMIN_GROUP, FINANCE_GROUP, ChatAgentMixin, can_answer_chats, in_groups,
)
from products.models import Product
from quotes.email import notify_finance_team, send_quote_confirmation_email
from quotes.models import Quote, QuoteItem

from .models import Conversation, Message
from .serializers import conversation_dict, message_dict, product_card
from .views import MAX_MESSAGE, read_json

TABS = ('waiting', 'mine', 'open', 'closed')


def agent_required(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if not can_answer_chats(request.user):
            return JsonResponse({'ok': False, 'error': 'Not allowed.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapper


def visible_conversations(user):
    qs = Conversation.objects.select_related('assigned_to', 'quote')
    if in_groups(user, FINANCE_GROUP, ADMIN_GROUP):
        return qs
    return qs.filter(channel=Conversation.Channel.SALES)


def _unread():
    """Customer messages newer than the last time an agent looked."""
    return Count(
        'messages',
        filter=Q(messages__sender=Message.Sender.CUSTOMER) & (
            Q(agent_read_at__isnull=True) | Q(messages__created_at__gt=F('agent_read_at'))
        ),
    )


def _tab_filter(qs, tab, user):
    if tab == 'waiting':
        return qs.filter(status=Conversation.Status.OPEN, assigned_to__isnull=True)
    if tab == 'mine':
        return qs.filter(status=Conversation.Status.OPEN, assigned_to=user)
    if tab == 'closed':
        return qs.filter(status=Conversation.Status.CLOSED)
    return qs.filter(status=Conversation.Status.OPEN)


class InboxView(ChatAgentMixin, TemplateView):
    template_name = 'chat/inbox.html'


@require_GET
@agent_required
def conversation_list(request):
    tab = request.GET.get('tab', 'open')
    if tab not in TABS:
        tab = 'open'
    base = visible_conversations(request.user)

    counts = {t: _tab_filter(base, t, request.user).count() for t in TABS if t != 'closed'}

    qs = _tab_filter(base, tab, request.user)
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(customer_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q)
        )

    latest = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at', '-pk')
    qs = qs.annotate(
        preview=Subquery(latest.values('body')[:1]),
        preview_sender=Subquery(latest.values('sender')[:1]),
        unread=_unread(),
    )[:100]

    items = []
    for c in qs:
        data = conversation_dict(c, for_agent=True)
        data.update({
            'preview': c.preview or ('Shared a product' if c.preview_sender == 'agent' else ''),
            'preview_sender': c.preview_sender or '',
            'unread': c.unread,
        })
        items.append(data)

    # For the tab title badge: chats waiting for anyone, plus my own.
    mine_or_waiting = _tab_filter(base, 'open', request.user).filter(
        Q(assigned_to__isnull=True) | Q(assigned_to=request.user)
    )
    unread_total = sum(mine_or_waiting.annotate(n=_unread()).values_list('n', flat=True))
    return JsonResponse({'tab': tab, 'counts': counts, 'items': items, 'unread_total': unread_total})


@require_GET
@agent_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(visible_conversations(request.user), pk=pk)
    try:
        after = int(request.GET.get('after', 0))
    except ValueError:
        after = 0

    messages = conversation.messages.select_related('agent', 'product__brand', 'product__category')
    if after:
        messages = messages.filter(pk__gt=after)

    # Viewing a chat marks it read for everyone on the team.
    Conversation.objects.filter(pk=pk).update(agent_read_at=timezone.now())

    shared = (
        Product.objects.filter(chat_messages__conversation=conversation)
        .select_related('brand', 'category').distinct()
    )
    return JsonResponse({
        'conversation': conversation_dict(conversation, for_agent=True),
        'messages': [message_dict(m) for m in messages],
        'shared_products': [product_card(p) for p in shared],
    })


@require_POST
@agent_required
def send(request, pk):
    conversation = get_object_or_404(visible_conversations(request.user), pk=pk)
    if not conversation.is_open:
        return JsonResponse({'ok': False, 'error': 'Reopen this chat to reply.'}, status=400)

    data = read_json(request)
    body = (data.get('body') or '').strip()[:MAX_MESSAGE]
    product = None
    if data.get('product_id'):
        product = Product.objects.filter(pk=data['product_id'], is_active=True).select_related('brand', 'category').first()
        if product is None:
            return JsonResponse({'ok': False, 'error': 'That product is no longer available.'}, status=400)
    if not body and product is None:
        return JsonResponse({'ok': False, 'error': 'Type a message first.'}, status=400)

    message = Message.objects.create(
        conversation=conversation, sender=Message.Sender.AGENT,
        agent=request.user, body=body, product=product,
    )
    updates = {'last_message_at': message.created_at, 'agent_read_at': message.created_at}
    # The first person to reply takes the chat.
    if conversation.assigned_to_id is None:
        updates['assigned_to'] = request.user
    Conversation.objects.filter(pk=pk).update(**updates)
    return JsonResponse({'ok': True, 'message': message_dict(message)})


def _system(conversation, body):
    now = timezone.now()
    Message.objects.create(conversation=conversation, sender=Message.Sender.SYSTEM, body=body)
    return now


@require_POST
@agent_required
def take(request, pk):
    conversation = get_object_or_404(visible_conversations(request.user), pk=pk)
    conversation.assigned_to = request.user
    conversation.save(update_fields=['assigned_to'])
    return JsonResponse({'ok': True})


@require_POST
@agent_required
def set_status(request, pk):
    conversation = get_object_or_404(visible_conversations(request.user), pk=pk)
    action = read_json(request).get('action')
    name = request.user.first_name or request.user.username
    if action == 'close' and conversation.is_open:
        now = _system(conversation, f'{name} closed the chat. Thanks for talking with us!')
        conversation.status = Conversation.Status.CLOSED
        conversation.closed_at = now
    elif action == 'reopen' and not conversation.is_open:
        now = _system(conversation, f'{name} reopened the chat.')
        conversation.status = Conversation.Status.OPEN
        conversation.closed_at = None
    else:
        return JsonResponse({'ok': True})
    conversation.last_message_at = now
    conversation.save(update_fields=['status', 'closed_at', 'last_message_at'])
    return JsonResponse({'ok': True})


@require_GET
@agent_required
def product_search(request):
    q = (request.GET.get('q') or '').strip()
    qs = Product.objects.filter(is_active=True).select_related('brand', 'category')
    for word in q.split()[:5]:
        qs = qs.filter(
            Q(name__icontains=word) | Q(sku__icontains=word)
            | Q(brand__name__icontains=word) | Q(category__name__icontains=word)
        )
    qs = qs.order_by('name')[:40]
    return JsonResponse({'items': [product_card(p) for p in qs]})


@require_POST
@agent_required
def create_quote(request, pk):
    """Raise a quote request for the visitor from the products in the chat.

    It goes into the normal Finance queue as Pending, addressed to the
    contact details taken at the start of the chat.
    """
    conversation = get_object_or_404(visible_conversations(request.user), pk=pk)
    data = read_json(request)

    lines = {}
    for row in data.get('items') or []:
        try:
            product_id = int(row.get('product_id'))
            quantity = int(row.get('quantity'))
        except (TypeError, ValueError, AttributeError):
            continue
        if quantity >= 1:
            lines[product_id] = lines.get(product_id, 0) + min(quantity, 100000)

    products = {p.pk: p for p in Product.objects.filter(pk__in=lines, is_active=True)}
    if not products:
        return JsonResponse({'ok': False, 'error': 'Add at least one product to the quote.'}, status=400)

    notes = (data.get('notes') or '').strip()[:2000]
    agent_name = request.user.get_full_name() or request.user.username

    with transaction.atomic():
        quote = Quote.objects.create(
            customer=conversation.customer,
            customer_name=conversation.customer_name,
            email=conversation.email,
            phone=conversation.phone,
            notes=notes,
            internal_notes=f'Raised from live chat #{conversation.pk} by {agent_name}.',
        )
        QuoteItem.objects.bulk_create([
            QuoteItem(quote=quote, product=products[pid], quantity=lines[pid])
            for pid in products
        ])
        conversation.quote = quote
        conversation.last_message_at = _system(
            conversation,
            f'Quote request {quote.reference} has been created with {len(products)} '
            f'product{"s" if len(products) != 1 else ""}. Our team will price it and email it to '
            f'{conversation.email}.',
        )
        conversation.save(update_fields=['quote', 'last_message_at'])

        transaction.on_commit(lambda: (send_quote_confirmation_email(quote), notify_finance_team(quote)))

    return JsonResponse({'ok': True, 'quote': {'id': quote.pk, 'reference': quote.reference}})
