"""Views for assembling and submitting a quote basket."""

import functools

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.permissions import is_verified_customer
from products.models import Product

from .basket import QuoteBasket
from .email import notify_finance_team, send_quote_confirmation_email
from .forms import QuoteRequestForm
from .models import QuoteItem


def _wants_json(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def verified_customer_required(view):
    """Only approved trade accounts may build or submit a quote.

    Enforced on every basket endpoint, not just the pages with buttons: the
    add-to-quote POST is reachable directly, so hiding the button is not what
    keeps an unapproved visitor out.

    The live catalogue posts by fetch, so an unapproved caller gets JSON with
    somewhere to go rather than an HTML login page it cannot display.
    """

    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if is_verified_customer(request.user):
            return view(request, *args, **kwargs)

        login_url = reverse('accounts:login')
        if _wants_json(request):
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'approval_required',
                    'message': (
                        'Sign in with an approved trade account to request a quote.'
                        if not request.user.is_authenticated
                        else 'Your trade account is still awaiting approval.'
                    ),
                    'login_url': login_url,
                },
                status=403,
            )

        if not request.user.is_authenticated:
            messages.info(request, 'Please sign in with your trade account to request a quote.')
            return redirect(f'{login_url}?next={request.get_full_path()}')

        messages.warning(
            request,
            'Your trade account is still being reviewed. We will email you as soon as it is approved.',
        )
        return redirect('core:home')

    return wrapper


@require_POST
@verified_customer_required
def basket_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    basket = QuoteBasket(request)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    basket.add(product, quantity)

    if _wants_json(request):
        return JsonResponse({
            'ok': True,
            'count': len(basket),
            'lines': basket.line_count,
            'name': product.name,
        })

    messages.success(request, f'{product.name} added to your quote request.')
    return redirect(request.META.get('HTTP_REFERER') or 'products:list')


@require_POST
@verified_customer_required
def basket_update(request, pk):
    basket = QuoteBasket(request)
    basket.set_quantity(pk, request.POST.get('quantity', 1))
    return redirect('quotes:basket')


@require_POST
@verified_customer_required
def basket_remove(request, pk):
    basket = QuoteBasket(request)
    basket.remove(pk)
    if _wants_json(request):
        return JsonResponse({'ok': True, 'count': len(basket), 'lines': basket.line_count})
    messages.info(request, 'Item removed from your quote request.')
    return redirect('quotes:basket')


@require_POST
@verified_customer_required
def basket_clear(request):
    QuoteBasket(request).clear()
    messages.info(request, 'Your quote request has been emptied.')
    return redirect('quotes:basket')


@verified_customer_required
def basket_detail(request):
    basket = QuoteBasket(request)
    return render(request, 'quotes/basket.html', {'basket_items': basket.items()})


@verified_customer_required
def checkout(request):
    """Turn the basket into a Quote with its line items."""
    basket = QuoteBasket(request)
    items = basket.items()

    if not items:
        messages.info(request, 'Add some products before requesting a quote.')
        return redirect('products:list')

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST)
        if form.is_valid():
            quote = form.save(commit=False)
            quote.customer = request.user if request.user.is_authenticated else None
            quote.save()

            # unit_price is deliberately left unset: pricing is Finance's job,
            # and cost prices are never exposed to the customer.
            QuoteItem.objects.bulk_create([
                QuoteItem(quote=quote, product=line['product'], quantity=line['quantity'])
                for line in items
            ])

            basket.clear()
            send_quote_confirmation_email(quote)
            notify_finance_team(quote)
            messages.success(request, f'Quote request {quote.reference} submitted.')
            return redirect('quotes:confirmation', pk=quote.pk)
    else:
        initial = {}
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            initial = {
                'customer_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'company': getattr(profile, 'company', ''),
                'phone': getattr(profile, 'phone', ''),
            }
        form = QuoteRequestForm(initial=initial)

    return render(request, 'quotes/checkout.html', {'form': form, 'basket_items': items})
