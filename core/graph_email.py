"""Send the site's email through Microsoft 365 using the Graph API.

Uses an Entra ID (Azure AD) app registration with the client-credentials
flow, so no user password is stored. The app needs the *application*
permission Mail.Send (admin-consented); mail goes out from GRAPH_SENDER, a
real mailbox or shared mailbox in the tenant.

Enable with:
    EMAIL_BACKEND=core.graph_email.GraphEmailBackend
    GRAPH_TENANT_ID=...
    GRAPH_CLIENT_ID=...
    GRAPH_CLIENT_SECRET=...
    GRAPH_SENDER=noreply@ahliki.com
"""

import base64
import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

TOKEN_URL = 'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token'
SEND_URL = 'https://graph.microsoft.com/v1.0/users/{sender}/sendMail'
TIMEOUT = 20

# One token per process, reused until shortly before it expires (~1 hour).
_token_lock = threading.Lock()
_token = {'value': None, 'expires': 0}


def _post(url, body, headers):
    request = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', 'replace')[:500]
        raise RuntimeError(f'Microsoft Graph returned {exc.code}: {detail}') from exc


def _recipients(addresses):
    result = []
    for address in addresses or []:
        name, email = parseaddr(address)
        if email:
            entry = {'emailAddress': {'address': email}}
            if name:
                entry['emailAddress']['name'] = name
            result.append(entry)
    return result


class GraphEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.tenant = getattr(settings, 'GRAPH_TENANT_ID', '')
        self.client_id = getattr(settings, 'GRAPH_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'GRAPH_CLIENT_SECRET', '')
        self.sender = getattr(settings, 'GRAPH_SENDER', '') or parseaddr(settings.DEFAULT_FROM_EMAIL)[1]
        missing = [name for name, value in (
            ('GRAPH_TENANT_ID', self.tenant),
            ('GRAPH_CLIENT_ID', self.client_id),
            ('GRAPH_CLIENT_SECRET', self.client_secret),
            ('GRAPH_SENDER', self.sender),
        ) if not value]
        if missing:
            raise ImproperlyConfigured(f'Graph email backend is missing: {", ".join(missing)}')

    def _access_token(self):
        with _token_lock:
            if _token['value'] and time.time() < _token['expires'] - 120:
                return _token['value']
            body = urllib.parse.urlencode({
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials',
            }).encode()
            _, raw = _post(
                TOKEN_URL.format(tenant=urllib.parse.quote(self.tenant)),
                body,
                {'Content-Type': 'application/x-www-form-urlencoded'},
            )
            data = json.loads(raw)
            _token['value'] = data['access_token']
            _token['expires'] = time.time() + int(data.get('expires_in', 3600))
            return _token['value']

    def _payload(self, message):
        body_type, content = 'Text', message.body
        for alt_content, mimetype in getattr(message, 'alternatives', []) or []:
            if mimetype == 'text/html':
                body_type, content = 'HTML', alt_content
                break

        graph_message = {
            'subject': message.subject,
            'body': {'contentType': body_type, 'content': content},
            'toRecipients': _recipients(message.to),
            'ccRecipients': _recipients(message.cc),
            'bccRecipients': _recipients(message.bcc),
        }
        if message.reply_to:
            graph_message['replyTo'] = _recipients(message.reply_to)

        # Show the display name from DEFAULT_FROM_EMAIL (e.g. "Ah Liki Quotes")
        # while sending from the licensed mailbox.
        from_name, _ = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        graph_message['from'] = {'emailAddress': {'address': self.sender, **({'name': from_name} if from_name else {})}}

        attachments = []
        for attachment in message.attachments:
            if isinstance(attachment, tuple) or hasattr(attachment, 'filename'):
                filename, data, mimetype = attachment[0], attachment[1], attachment[2]
                if isinstance(data, str):
                    data = data.encode('utf-8')
                attachments.append({
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': filename or 'attachment',
                    'contentType': mimetype or 'application/octet-stream',
                    'contentBytes': base64.b64encode(data).decode('ascii'),
                })
        if attachments:
            graph_message['attachments'] = attachments

        return {'message': graph_message, 'saveToSentItems': True}

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                token = self._access_token()
                _post(
                    SEND_URL.format(sender=urllib.parse.quote(self.sender)),
                    json.dumps(self._payload(message)).encode('utf-8'),
                    {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                )
                sent += 1
            except Exception:
                logger.exception('Graph email to %s failed', message.recipients())
                if not self.fail_silently:
                    raise
        return sent
