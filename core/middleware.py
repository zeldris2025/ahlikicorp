"""Keep the site on one address.

www.<SITE_DOMAIN> always redirects to the bare domain. The Azure default
address (*.azurewebsites.net) redirects too, but only when
REDIRECT_TO_SITE_DOMAIN is on, so it stays usable until DNS is confirmed.
"""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        domain = getattr(settings, 'SITE_DOMAIN', '')
        self.target = domain
        self.redirect_hosts = set()
        if domain:
            self.redirect_hosts.add(f'www.{domain}')
            azure_host = getattr(settings, 'AZURE_HOSTNAME', '').lower()
            if azure_host and getattr(settings, 'REDIRECT_TO_SITE_DOMAIN', False):
                self.redirect_hosts.add(azure_host)

    def __call__(self, request):
        if self.redirect_hosts:
            host = request.get_host().lower().rsplit(':', 1)[0]
            if host in self.redirect_hosts:
                return HttpResponsePermanentRedirect(f'https://{self.target}{request.get_full_path()}')
        return self.get_response(request)
