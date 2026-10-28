"""Turning an approved application into a working account.

Kept out of the views so that Django Admin, the staff portal and any future
management command all create accounts the same way.
"""

import logging

from django.contrib.auth.models import Group, User
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from .email import send_application_approved, send_application_rejected
from .models import CustomerApplication, UserProfile
from .permissions import CUSTOMER_GROUP

logger = logging.getLogger('accounts')

# Ambiguous characters are left out: these passwords get read off a screen and
# typed by hand, and 0/O and 1/l/I are where that goes wrong.
PASSWORD_ALPHABET = 'abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
PASSWORD_LENGTH = 12


def generate_password():
    return get_random_string(PASSWORD_LENGTH, PASSWORD_ALPHABET)


def _unique_username(email):
    """The email, or the email with a counter if it is already taken."""
    base = email.strip().lower()[:150] or 'customer'
    username = base
    suffix = 2
    while User.objects.filter(username__iexact=username).exists():
        tail = f'-{suffix}'
        username = f'{base[:150 - len(tail)]}{tail}'
        suffix += 1
    return username


@transaction.atomic
def approve_application(application, reviewer=None):
    """Create the account for an approved application and email the details.

    Returns (user, password) on success, or (user, None) if the application had
    already been approved — in which case nothing is created or re-sent, so a
    double click cannot issue a second password.
    """
    if application.user_id:
        return application.user, None

    first_name, _, last_name = application.full_name.strip().partition(' ')
    password = generate_password()

    user = User.objects.create_user(
        username=_unique_username(application.email),
        email=application.email,
        password=password,
        first_name=first_name[:150],
        last_name=last_name[:150],
    )

    group, _ = Group.objects.get_or_create(name=CUSTOMER_GROUP)
    user.groups.add(group)

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.company = application.organisation
    profile.phone = application.phone
    profile.save()

    application.user = user
    application.status = CustomerApplication.Status.APPROVED
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer if reviewer and reviewer.is_authenticated else None
    application.save(update_fields=['user', 'status', 'reviewed_at', 'reviewed_by'])

    # Sent after the row is written: a mail failure is logged inside _send and
    # must not roll back an account that already exists.
    send_application_approved(application, user.username, password)
    logger.info('Approved application %s for %s', application.pk, application.email)
    return user, password


def reject_application(application, reviewer=None, notify=True, include_notes=False):
    """Mark an application declined, optionally telling the applicant."""
    application.status = CustomerApplication.Status.REJECTED
    application.reviewed_at = timezone.now()
    application.reviewed_by = reviewer if reviewer and reviewer.is_authenticated else None
    application.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])

    if notify:
        send_application_rejected(application, include_notes=include_notes)
    return application
