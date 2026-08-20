"""Align Django Admin access with role.

Only Admin belongs in Django Admin: it exposes users, groups, permissions,
sessions and every model in the project. Finance works in the staff portal at
/manage/, which is scoped to product and quote maintenance, so Finance accounts
must not carry is_staff — that flag alone is what grants /admin/ entry.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Grant Django Admin access to Admin accounts only; revoke it elsewhere.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Report changes without applying them.')

    def handle(self, *args, **options):
        dry = options['dry_run']
        granted = revoked = 0

        for user in User.objects.prefetch_related('groups'):
            groups = {g.name for g in user.groups.all()}
            should_be_staff = user.is_superuser or 'Admin' in groups

            if should_be_staff and not user.is_staff:
                self.stdout.write(self.style.SUCCESS(f'GRANT  admin access -> {user.username}'))
                if not dry:
                    user.is_staff = True
                    user.save(update_fields=['is_staff'])
                granted += 1

            elif not should_be_staff and user.is_staff:
                self.stdout.write(self.style.WARNING(f'REVOKE admin access <- {user.username} ({", ".join(sorted(groups)) or "no groups"})'))
                if not dry:
                    user.is_staff = False
                    user.save(update_fields=['is_staff'])
                revoked += 1

        self.stdout.write('')
        verb = 'would be' if dry else 'were'
        self.stdout.write(f'{granted} granted, {revoked} revoked ({verb} applied)')
