from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver

# Finance works entirely in the staff portal at /manage/, never in Django
# Admin. These permissions cover exactly that surface: full product and
# category maintenance, plus pricing and progressing quotes. Deliberately
# absent: users, groups, permissions, sessions, locations and site content.
FINANCE_PERMISSIONS = (
    'add_product', 'change_product', 'delete_product', 'view_product',
    'add_productimage', 'change_productimage', 'delete_productimage', 'view_productimage',
    'add_category', 'change_category', 'view_category',
    'view_brand',
    'view_quote', 'change_quote', 'manage_quotes',
    'view_quoteitem', 'add_quoteitem', 'change_quoteitem', 'delete_quoteitem',
)


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    if sender.name != 'accounts':
        return

    customer, _ = Group.objects.get_or_create(name='Customer')
    finance, _ = Group.objects.get_or_create(name='Finance')
    admin, _ = Group.objects.get_or_create(name='Admin')

    finance.permissions.set(Permission.objects.filter(codename__in=FINANCE_PERMISSIONS))
    admin.permissions.set(Permission.objects.all())
    customer.permissions.clear()
