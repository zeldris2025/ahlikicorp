"""Role checks for the staff portal.

Group membership is the single source of truth for role, checked server-side on
every protected view. Hiding a link in a template is presentation, not access
control, so nothing here relies on the navigation being correct.
"""

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

FINANCE_GROUP = 'Finance'
ADMIN_GROUP = 'Admin'


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
