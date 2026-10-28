from django.db import migrations

SALES_GROUP = 'Sales Girls'


def create_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name=SALES_GROUP)


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Left in place on reverse: members may already have been added to it.
        migrations.RunPython(create_group, migrations.RunPython.noop),
    ]
