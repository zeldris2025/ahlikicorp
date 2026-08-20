from pathlib import Path

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

        # Hero background video. Resolution order:
        #   1. HERO_VIDEO_FILE if set explicitly
        #   2. any video dropped into static/videos/ (zero config)
        #   3. the YouTube fallback
        # A self-hosted file always wins: it needs no third-party script and
        # cannot be stripped by a content blocker the way an embed can.
        video_file = settings.HERO_VIDEO_FILE or self._discover_hero_video()
        context['hero_video_file'] = video_file
        poster = settings.HERO_VIDEO_POSTER
        if poster and not poster.startswith(('http://', 'https://', '/')):
            from django.templatetags.static import static as static_url
            poster = static_url(poster)
        context['hero_video_poster'] = poster
        context['hero_video_youtube_id'] = (
            '' if video_file else settings.HERO_VIDEO_YOUTUBE_ID
        )
        return context

    @staticmethod
    def _discover_hero_video():
        """Return the URL of a video dropped into static/videos/, if any.

        Lets someone add a hero video by copying a file into the folder, with
        no settings change. The result is cached so this does not touch the
        filesystem on every request.
        """
        cached = cache.get('hero_video_discovered')
        if cached is not None:
            return cached

        from django.templatetags.static import static as static_url

        folder = Path(settings.BASE_DIR) / 'static' / 'videos'
        found = ''
        if folder.is_dir():
            # mp4 first: the widest browser support of the three.
            for pattern in ('*.mp4', '*.webm', '*.mov'):
                matches = sorted(folder.glob(pattern))
                if matches:
                    found = static_url(f'videos/{matches[0].name}')
                    break

        cache.set('hero_video_discovered', found, 300)
        return found

class AboutView(TemplateView):
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['locations_count'] = cache.get_or_set(
            'locations_count', lambda: Location.objects.count(), 3600
        )
        return context

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

    def get_queryset(self):
        # Not paginated: the map plots every site, so a partial page would
        # leave pins without matching cards.
        return Location.objects.select_related('company').order_by('sort_order', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locations = context['locations']

        context['headquarters'] = next((l for l in locations if l.is_headquarters), None)
        context['companies'] = Brand.objects.all().order_by('sort_order', 'name')

        # Only sites with coordinates can be plotted; the rest still list.
        context['map_points'] = [
            {
                'id': l.pk,
                'name': l.name,
                'address': l.address,
                'island': l.island,
                'hours': l.opening_hours,
                'phone': l.phone,
                'lat': float(l.latitude),
                'lng': float(l.longitude),
                'company': l.company.name if l.company else '',
                'slug': l.company.slug if l.company else '',
                'colour': l.company.accent_color if l.company else '#04212a',
                'hq': l.is_headquarters,
            }
            for l in locations
            if l.latitude is not None and l.longitude is not None
        ]
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
