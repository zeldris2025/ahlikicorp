"""Admin page to move the site's data between installations.

Export bundles the database content and the uploaded images it refers to
into one .zip; Import loads such a file into this site. It is meant for
copying a local or Docker site up to Azure (or back) without touching git or
the server's file system.

Superusers only: an import can create or change any record, including user
accounts and their permissions.
"""

import io
import json
import os
import tempfile
import zipfile
from pathlib import PurePosixPath

from django import forms
from django.apps import apps
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.db import models
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

FORMAT_VERSION = 1
MAX_UPLOAD_BYTES = 300 * 1024 * 1024

# Rebuilt by `migrate` on every site, or meaningless outside the site that
# made them, so they are never carried across.
ALWAYS_EXCLUDED = ['contenttypes', 'auth.permission', 'sessions', 'admin.logentry']
PRODUCT_MODELS = ['products.Product', 'products.ProductImage', 'products.Category']

# Accounts created by `seed_data` with passwords that are written in the
# code. They are exported with their password disabled, so a copy of local
# data never brings a publicly known login onto a live site.
DEMO_LOGINS = {
    'admin@example.com': 'AdminPass123!',
    'finance@example.com': 'FinancePass123!',
    'customer@example.com': 'CustomerPass123!',
}


class ExportForm(forms.Form):
    include_products = forms.BooleanField(
        required=False,
        label='Include the product catalogue',
        help_text='Products, product categories and their images. Leave unticked to copy everything else.',
    )


class ImportForm(forms.Form):
    file = forms.FileField(label='Export file (.zip)')
    confirm = forms.BooleanField(
        label='I understand this adds to and overwrites records on this site',
    )

    def clean_file(self):
        upload = self.cleaned_data['file']
        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError('The file is larger than 300 MB.')
        if not zipfile.is_zipfile(upload):
            raise forms.ValidationError('This is not an export file. Choose the .zip made by Export.')
        upload.seek(0)
        return upload


def _require_superuser(request):
    if not request.user.is_superuser:
        raise PermissionDenied


def _disable_demo_passwords(objects):
    User = get_user_model()
    label = User._meta.label_lower
    known = {
        user.get_username()
        for user in User.objects.filter(username__in=DEMO_LOGINS)
        if user.check_password(DEMO_LOGINS[user.get_username()])
    }
    disabled = []
    for obj in objects:
        if obj['model'] == label and obj['fields'].get('username') in known:
            # "!" marks an unusable password in Django; the account can be
            # given a real one later with "Change password" in the admin.
            obj['fields']['password'] = '!disabled-on-export'
            disabled.append(obj['fields']['username'])
    return disabled


def _referenced_files(objects):
    """Names of uploaded files the exported records point at."""
    names = set()
    file_fields = {}
    for obj in objects:
        label = obj['model']
        if label not in file_fields:
            model = apps.get_model(label)
            file_fields[label] = [f.name for f in model._meta.fields if isinstance(f, models.FileField)]
        for field in file_fields[label]:
            value = obj['fields'].get(field)
            if value:
                names.add(value)
    return sorted(names)


def build_export(include_products):
    exclude = list(ALWAYS_EXCLUDED)
    if not include_products:
        exclude += PRODUCT_MODELS

    buffer = io.StringIO()
    call_command(
        'dumpdata',
        natural_foreign=True,
        natural_primary=True,
        exclude=exclude,
        stdout=buffer,
        verbosity=0,
    )
    objects = json.loads(buffer.getvalue() or '[]')
    disabled = _disable_demo_passwords(objects)

    archive = io.BytesIO()
    media_count = 0
    missing = []
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('data.json', json.dumps(objects))
        for name in _referenced_files(objects):
            if not default_storage.exists(name):
                missing.append(name)
                continue
            with default_storage.open(name, 'rb') as fh:
                bundle.writestr(f'media/{name}', fh.read())
            media_count += 1
        bundle.writestr('manifest.json', json.dumps({
            'format': FORMAT_VERSION,
            'created': timezone.localtime().isoformat(),
            'include_products': include_products,
            'records': len(objects),
            'media_files': media_count,
            'demo_passwords_disabled': disabled,
        }, indent=2))
    return archive.getvalue()


def _safe_media_name(member):
    """The storage name for a zip member under media/, or None if unsafe."""
    path = PurePosixPath(member)
    if path.parts[:1] != ('media',) or len(path.parts) < 2 or member.endswith('/'):
        return None
    rel = PurePosixPath(*path.parts[1:])
    if rel.is_absolute() or '..' in rel.parts or '\\' in member:
        return None
    return str(rel)


def run_import(upload):
    with zipfile.ZipFile(upload) as bundle:
        names = set(bundle.namelist())
        if 'data.json' not in names or 'manifest.json' not in names:
            raise ValueError('This zip was not made by Export (data.json or manifest.json is missing).')
        manifest = json.loads(bundle.read('manifest.json'))
        if manifest.get('format') != FORMAT_VERSION:
            raise ValueError('This export was made by a different version of the site.')

        # loaddata only reads from a file path, and runs in one transaction,
        # so a bad file changes nothing.
        handle, path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(handle, 'wb') as fh:
                fh.write(bundle.read('data.json'))
            call_command('loaddata', path, verbosity=0)
        finally:
            os.remove(path)

        media_count = 0
        for member in sorted(names):
            name = _safe_media_name(member)
            if not name:
                continue
            if default_storage.exists(name):
                default_storage.delete(name)
            default_storage.save(name, ContentFile(bundle.read(member)))
            media_count += 1

    # Company lists, counts and the header address are cached.
    cache.clear()
    return manifest, media_count


def data_transfer_view(request):
    _require_superuser(request)
    export_form = ExportForm()
    import_form = ImportForm()

    if request.method == 'POST' and request.POST.get('action') == 'export':
        export_form = ExportForm(request.POST)
        if export_form.is_valid():
            include = export_form.cleaned_data['include_products']
            content = build_export(include)
            stamp = timezone.localtime().strftime('%Y-%m-%d-%H%M')
            response = HttpResponse(content, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="ahliki-data-{stamp}.zip"'
            return response

    if request.method == 'POST' and request.POST.get('action') == 'import':
        import_form = ImportForm(request.POST, request.FILES)
        if import_form.is_valid():
            try:
                manifest, media_count = run_import(import_form.cleaned_data['file'])
            except Exception as exc:  # shown to the superuser; nothing was saved
                messages.error(request, f'Import failed, nothing was changed: {exc}')
            else:
                messages.success(
                    request,
                    f'Imported {manifest.get("records", 0)} records and {media_count} images '
                    f'(exported {manifest.get("created", "")[:16].replace("T", " ")}).',
                )
                return redirect('admin_data_transfer')

    context = {
        **admin.site.each_context(request),
        'title': 'Import / export data',
        'export_form': export_form,
        'import_form': import_form,
    }
    return render(request, 'admin/data_transfer.html', context)
