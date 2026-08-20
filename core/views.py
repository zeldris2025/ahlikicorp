from django.conf import settings
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.core.cache import cache
from .models import Location, ContactMessage, NewsletterSubscriber
from .forms import ContactForm, NewsletterForm
from products.models import Brand, Product

class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        companies = cache.get_or_set(
            'group_companies',
            lambda: list(Brand.objects.all().order_by('sort_order', 'name')),
            3600,
        )
        context['companies'] = companies
        # Hero spotlight deck reuses the same records.
        context['brands'] = companies
        context['featured_products'] = cache.get_or_set('featured_products', lambda: Product.objects.filter(is_active=True, is_exclusive=True)[:6], 1800)
        context['locations_count'] = cache.get_or_set('locations_count', lambda: Location.objects.count(), 3600)

        # Hero background video. A self-hosted file takes precedence over the
        # YouTube fallback; both are loaded lazily by the template.
        context['hero_video_file'] = settings.HERO_VIDEO_FILE
        context['hero_video_poster'] = settings.HERO_VIDEO_POSTER
        context['hero_video_youtube_id'] = (
            '' if settings.HERO_VIDEO_FILE else settings.HERO_VIDEO_YOUTUBE_ID
        )
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'

class CompaniesView(TemplateView):
    """Detail page for the operating companies within the group."""

    template_name = 'core/companies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Brand.objects.all().order_by('sort_order', 'name')
        return context

class LocationsView(ListView):
    model = Location
    template_name = 'core/locations.html'
    context_object_name = 'locations'
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['headquarters'] = Location.objects.filter(is_headquarters=True).first()
        return context

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you! We will respond to your message shortly.')
            return redirect('core:home')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})

def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully subscribed to our newsletter!')
            return redirect(request.META.get('HTTP_REFERER', 'core:home'))
        else:
            messages.error(request, 'This email is already subscribed.')
            return redirect(request.META.get('HTTP_REFERER', 'core:home'))
    return redirect('core:home')
