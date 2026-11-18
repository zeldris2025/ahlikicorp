"""Create a first admin account on a brand-new site that has none.

Runs from startup.sh on every start, but only acts when the database has no
superuser at all, so it never changes or re-creates an existing account and
does nothing once real accounts have been imported.

The repository is public, so only the password's one-way hash is kept here;
the password was handed to the site owner separately. Change it after the
first sign-in (top right of the admin: "Change password").
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

USERNAME = 'ahliki-admin'
PASSWORD_HASH = 'pbkdf2_sha256$1000000$IsVoSu6GQAzwq2zAYJo9CA$DmaRQNX1z7TayeOwMbuU1xuxAVKomtMBWjRjo+kHdGQ='


class Command(BaseCommand):
    help = 'Create the first admin account if the site has no superuser yet.'

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('An admin account already exists; nothing to do.')
            return
        user = User(username=USERNAME, is_staff=True, is_superuser=True, is_active=True)
        user.password = PASSWORD_HASH
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Created first admin account "{USERNAME}".'))
