"""Server-side check of the reCAPTCHA v2 "I'm not a robot" checkbox."""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


def verify_recaptcha(token, remote_ip=None):
    """Ask Google whether the checkbox token is genuine.

    Fails closed: an empty token, a network error or an unreadable answer all
    count as not verified, so an outage never lets bots through.
    """
    if not settings.RECAPTCHA_ENABLED:
        return True
    if not token:
        return False

    payload = {'secret': settings.RECAPTCHA_SECRET_KEY, 'response': token}
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        request = urllib.request.Request(
            VERIFY_URL, data=urllib.parse.urlencode(payload).encode()
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.load(response)
    except Exception:
        logger.exception('reCAPTCHA verification request failed')
        return False

    return bool(result.get('success'))
