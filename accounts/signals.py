from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    if sender.name != 'accounts':
        return

    customer, _ = Group.objects.get_or_create(name='Customer')
    finance, _ = Group.objects.get_or_create(name='Finance')
    admin, _ = Group.objects.get_or_create(name='Admin')
    finance.permissions.set(Permission.objects.filter(codename__in=(
        'view_quote', 'change_quote', 'manage_quotes', 'view_product', 'change_product',
    )))
    admin.permissions.set(Permission.objects.all())
    customer.permissions.clear()