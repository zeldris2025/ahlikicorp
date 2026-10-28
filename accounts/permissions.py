"""Role checks for the staff portal.

Group membership is the single source of truth for role, checked server-side on
every protected view. Hiding a link in a template is presentation, not access
control, so nothing here relies on the navigation being correct.
"""

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

FINANCE_GROUP = 'Finance'
ADMIN_GROUP = 'Admin'
# Approved trade customers. Membership is granted only when an administrator
# approves a customer application, so it is the marker of a verified account.
CUSTOMER_GROUP = 'Customers'
# Sales staff who answer live chats from the assistant. They work only in the
# chat inbox, not the rest of the staff portal.
SALES_GROUP = 'Sales Girls'


def in_groups(user, *names):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=names).exists()


def is_finance(user):
    return in_groups(user, FINANCE_GROUP, ADMIN_GROUP)


def is_admin(user):
    return in_groups(user, ADMIN_GROUP)


def is_sales(user):
    return in_groups(user, SALES_GROUP)


def can_answer_chats(user):
    """May this user work the live chat inbox?"""
    return in_groups(user, SALES_GROUP, FINANCE_GROUP, ADMIN_GROUP)


def is_verified_customer(user):
    """May this user raise a quote request?

    Only approved customers and staff. Anonymous visitors cannot, which is the
    point: a quote must be traceable to an account someone has vetted.
    """
    return in_groups(user, CUSTOMER_GROUP, FINANCE_GROUP, ADMIN_GROUP)


class VerifiedCustomerMixin(AccessMixin):
    """Restrict a view to approved trade accounts.

    Anonymous visitors go to the login page. Someone signed in but still
    awaiting approval is told so and sent home rather than shown a 403 they
    can do nothing about — their account is coming, it just is not ready.
    This matches quotes.basket_views.verified_customer_required so the whole
    quote flow behaves the same way.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not is_verified_customer(request.user):
            from django.contrib import messages
            from django.shortcuts import redirect

            messages.warning(
                request,
                'Your trade account is still being reviewed. '
                'We will email you as soon as it is approved.',
            )
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)


class StaffPortalMixin(AccessMixin):
    """Restrict a view to the staff portal roles.

    Anonymous visitors are sent to the login page; a signed-in user without the
    role gets 403 rather than a login loop, since logging in again will not
    help them.
    """

    allowed_groups = (FINANCE_GROUP, ADMIN_GROUP)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not in_groups(request.user, *self.allowed_groups):
            raise PermissionDenied('This area is restricted to authorised staff.')
        return super().dispatch(request, *args, **kwargs)


class AdminOnlyMixin(StaffPortalMixin):
    allowed_groups = (ADMIN_GROUP,)


class ChatAgentMixin(StaffPortalMixin):
    """The live chat inbox: sales staff plus Finance and Admin."""

    allowed_groups = (SALES_GROUP, FINANCE_GROUP, ADMIN_GROUP)
