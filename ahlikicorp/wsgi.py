# Copyright (c) 2026 Charlie Wilson Ah Kuoi. All rights reserved.
# Proprietary and confidential. Use, copying or distribution requires the
# prior written permission of Charlie Wilson Ah Kuoi. See LICENSE.

"""
WSGI config for ahlikicorp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ahlikicorp.settings')

application = get_wsgi_application()
