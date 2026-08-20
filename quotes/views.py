from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView, DetailView, View
from django.http import HttpResponse, Http404
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.cache import cache
from .models import Quote, QuoteItem
from .forms import QuoteRequestForm, QuoteItemFormSet, QuoteStatusForm
from .email import send_quote_confirmation_email, send_quote_to_customer, notify_finance_team
from .pdf import generate_quote_pdf
from products.models import Product

class QuoteCreateView(CreateView):
    model = Quote
    form_class = QuoteRequestForm
    template_name = 'quotes/create.html'

    def form_valid(self, form):
        quote = form.save(commit=False)
        quote.customer = self.request.user if self.request.user.is_authenticated else None
        quote.save()
        send_quote_confirmation_email(quote)
        notify_finance_team(quote)
        messages.success(self.request, f'Quote {quote.reference} submitted successfully!')
        return redirect('quotes:confirmation', pk=quote.pk)

class QuoteConfirmationView(DetailView):
    model = Quote
    template_name = 'quotes/confirmation.html'
    context_object_name = 'quote'

class QuoteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Quote
    template_name = 'quotes/list.html'
    context_object_name = 'quotes'
    paginate_by = 20

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Finance', 'Admin']).exists()

    def get_queryset(self):
        return Quote.objects.all().select_related('customer', 'delivery_location').prefetch_related('items')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_quotes'] = Quote.objects.count()
        context['pending_quotes'] = Quote.objects.filter(status=Quote.Status.PENDING).count()
        context['quoted_quotes'] = Quote.objects.filter(status=Quote.Status.QUOTED).count()
        return context

class QuoteDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Quote
    template_name = 'quotes/detail.html'
    context_object_name = 'quote'

    def test_func(self):
        quote = self.get_object()
        return (self.request.user.groups.filter(name__in=['Finance', 'Admin']).exists() or
                quote.customer == self.request.user)

    def get_queryset(self):
        return Quote.objects.select_related('customer', 'delivery_location').prefetch_related('items__product')

class QuoteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Quote
    form_class = QuoteStatusForm
    template_name = 'quotes/edit.html'

    def test_func(self):
        return self.request.user.groups.filter(name__in=['Finance', 'Admin']).exists()

    def form_valid(self, form):
        quote = form.save()
        messages.success(self.request, f'Quote {quote.reference} updated successfully.')
        if quote.status == Quote.Status.QUOTED:
            send_quote_to_customer(quote)
            messages.info(self.request, 'Quote PDF sent to customer.')
        return redirect('quotes:detail', pk=quote.pk)

@login_required
def quote_pdf_view(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    if not (request.user.groups.filter(name__in=['Finance', 'Admin']).exists() or
            quote.customer == request.user):
        raise Http404('Access denied.')

    pdf_bytes = cache.get(f'quote_pdf_{quote.pk}')
    if not pdf_bytes:
        pdf_bytes = generate_quote_pdf(quote)
        cache.set(f'quote_pdf_{quote.pk}', pdf_bytes, 86400)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quote.reference}.pdf"'
    return response

@login_required
@permission_required('quotes.manage_quotes', raise_exception=True)
def quote_add_items(request, pk):
    quote = get_object_or_404(Quote, pk=pk)

    if request.method == 'POST':
        formset = QuoteItemFormSet(request.POST, instance=quote)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Quote items updated.')
            return redirect('quotes:detail', pk=quote.pk)
    else:
        formset = QuoteItemFormSet(instance=quote)

    return render(request, 'quotes/add_items.html', {'quote': quote, 'formset': formset})
