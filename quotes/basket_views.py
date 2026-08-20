"""Views for assembling and submitting a quote basket."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .basket import QuoteBasket
from .email import notify_finance_team, send_quote_confirmation_email
from .forms import QuoteRequestForm
from .models import QuoteItem


def _wants_json(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


@require_POST
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
def basket_update(request, pk):
    basket = QuoteBasket(request)
    basket.set_quantity(pk, request.POST.get('quantity', 1))
    return redirect('quotes:basket')


@require_POST
def basket_remove(request, pk):
    basket = QuoteBasket(request)
    basket.remove(pk)
    if _wants_json(request):
        return JsonResponse({'ok': True, 'count': len(basket), 'lines': basket.line_count})
    messages.info(request, 'Item removed from your quote request.')
    return redirect('quotes:basket')


@require_POST
def basket_clear(request):
    QuoteBasket(request).clear()
    messages.info(request, 'Your quote request has been emptied.')
    return redirect('quotes:basket')


def basket_detail(request):
    basket = QuoteBasket(request)
    return render(request, 'quotes/basket.html', {'basket_items': basket.items()})


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
