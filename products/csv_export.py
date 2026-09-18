"""CSV export of every dataset the site holds.

One registry describes each dataset once — its columns and how a row is
built — and both the single-file download and the "everything" ZIP are
driven from it. Adding a new model to the export means adding one entry
here, not touching a view or a template.

Exports are read-only snapshots for spreadsheets and backups. The product
export deliberately uses the same column names as the product *import*
(``csv_import.CSV_COLUMNS``) so a file can be pulled out, edited and pushed
straight back in.
"""

import csv
import io
import json
import zipfile

from django.http import HttpResponse
from django.utils import timezone


def _local(value):
    """A timestamp a spreadsheet can read, in the site's timezone."""
    if not value:
        return ''
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime('%Y-%m-%d %H:%M')


def _products():
    from .models import Product

    rows = Product.objects.select_related('brand', 'category').order_by('name')
    for product in rows:
        yield [
            product.name,
            product.category.name if product.category_id else '',
            product.description,
            product.cost_price,
            product.stock_quantity,
            'true' if product.is_exclusive else 'false',
            json.dumps(product.specifications or {}),
            product.sku,
            product.brand.name if product.brand_id else '',
            'true' if product.is_active else 'false',
            product.image.url if product.image else '',
            _local(product.created_at),
            _local(product.updated_at),
        ]


def _categories():
    from django.db.models import Count

    from .models import Category

    for category in Category.objects.annotate(n=Count('products')).order_by('name'):
        yield [category.name, category.slug, category.n]


def _companies():
    from .models import Brand

    for brand in Brand.objects.order_by('sort_order', 'name'):
        yield [
            brand.name,
            brand.slug,
            brand.sector,
            brand.tagline,
            brand.description,
            json.dumps(brand.highlights or []),
            brand.accent_color,
            brand.sort_order,
        ]


def _exclusive_brands():
    from .models import ExclusiveBrand

    for brand in ExclusiveBrand.objects.order_by('sort_order', 'name'):
        yield [
            brand.name,
            brand.note,
            brand.website,
            brand.sort_order,
            'true' if brand.is_active else 'false',
        ]


def _promotions():
    from .models import Promotion

    for promotion in Promotion.objects.order_by('sort_order', '-created_at'):
        yield [
            promotion.kicker,
            promotion.headline,
            promotion.subtext,
            promotion.image.url if promotion.image else '',
            promotion.cta_label,
            promotion.cta_url,
            promotion.accent_color,
            _local(promotion.starts_at),
            _local(promotion.ends_at),
            'true' if promotion.is_active else 'false',
            promotion.sort_order,
        ]


def _locations():
    from core.models import Location

    for location in Location.objects.select_related('company').order_by('sort_order', 'name'):
        yield [
            location.name,
            location.company.name if location.company_id else '',
            location.address,
            location.island,
            location.phone,
            location.email,
            location.opening_hours,
            location.latitude if location.latitude is not None else '',
            location.longitude if location.longitude is not None else '',
            'true' if location.is_headquarters else 'false',
            location.sort_order,
        ]


def _quotes():
    from quotes.models import Quote

    rows = (
        Quote.objects
        .select_related('delivery_location')
        .prefetch_related('items')
        .order_by('-created_at')
    )
    for quote in rows:
        items = list(quote.items.all())
        subtotal = sum(item.line_total for item in items)
        tax = subtotal * quote.tax_rate / 100
        yield [
            quote.reference,
            quote.customer_name,
            quote.company,
            quote.email,
            quote.phone,
            quote.get_status_display(),
            quote.delivery_location.name if quote.delivery_location_id else '',
            quote.delivery_address,
            len(items),
            subtotal,
            quote.tax_rate,
            tax,
            subtotal + tax,
            quote.valid_until or '',
            quote.notes,
            _local(quote.created_at),
        ]


def _quote_items():
    from quotes.models import QuoteItem

    rows = (
        QuoteItem.objects
        .select_related('quote', 'product')
        .order_by('-quote__created_at', 'product__name')
    )
    for item in rows:
        yield [
            item.quote.reference,
            item.product.sku,
            item.product.name,
            item.quantity,
            item.unit_price if item.unit_price is not None else '',
            item.line_total,
        ]


def _contact_messages():
    from core.models import ContactMessage

    for message in ContactMessage.objects.order_by('-created_at'):
        yield [
            message.name,
            message.email,
            message.phone,
            message.subject,
            message.message,
            _local(message.created_at),
            _local(message.resolved_at),
        ]


def _subscribers():
    from core.models import NewsletterSubscriber

    for subscriber in NewsletterSubscriber.objects.order_by('-created_at'):
        yield [
            subscriber.email,
            'true' if subscriber.is_active else 'false',
            _local(subscriber.created_at),
        ]


# key -> what it is called, what file it becomes, its columns, and its rows.
# The order here is the order shown on the export screen and inside the ZIP.
DATASETS = {
    'products': {
        'label': 'Products',
        'description': 'The full catalogue. Uses the same columns as the product import, so an edited export can be uploaded straight back.',
        'filename': 'products.csv',
        'header': [
            'name', 'category', 'description', 'cost_price', 'stock_quantity',
            'is_exclusive', 'specifications', 'sku', 'brand', 'is_active',
            'image', 'created_at', 'updated_at',
        ],
        'rows': _products,
    },
    'categories': {
        'label': 'Categories',
        'description': 'Every category with the number of products filed under it.',
        'filename': 'categories.csv',
        'header': ['name', 'slug', 'product_count'],
        'rows': _categories,
    },
    'companies': {
        'label': 'Companies',
        'description': 'The group operating companies and their public copy.',
        'filename': 'companies.csv',
        'header': ['name', 'slug', 'sector', 'tagline', 'description', 'highlights', 'accent_color', 'sort_order'],
        'rows': _companies,
    },
    'exclusive_brands': {
        'label': 'Exclusive logos',
        'description': 'Supplier brands carried on exclusive terms.',
        'filename': 'exclusive_brands.csv',
        'header': ['name', 'caption', 'website', 'sort_order', 'is_active'],
        'rows': _exclusive_brands,
    },
    'promotions': {
        'label': 'Promotions',
        'description': 'Home page promotion slides, including scheduling dates.',
        'filename': 'promotions.csv',
        'header': [
            'kicker', 'headline', 'subtext', 'image', 'cta_label', 'cta_url',
            'accent_color', 'starts_at', 'ends_at', 'is_active', 'sort_order',
        ],
        'rows': _promotions,
    },
    'locations': {
        'label': 'Locations',
        'description': 'Stores, depots and offices with contact details and map coordinates.',
        'filename': 'locations.csv',
        'header': [
            'name', 'company', 'address', 'island', 'phone', 'email',
            'opening_hours', 'latitude', 'longitude', 'is_headquarters', 'sort_order',
        ],
        'rows': _locations,
    },
    'quotes': {
        'label': 'Quote requests',
        'description': 'One row per quote, with totals calculated from its priced lines.',
        'filename': 'quotes.csv',
        'header': [
            'reference', 'customer_name', 'company', 'email', 'phone', 'status',
            'delivery_location', 'delivery_address', 'item_count', 'subtotal',
            'tax_rate', 'tax_total', 'total', 'valid_until', 'notes', 'created_at',
        ],
        'rows': _quotes,
    },
    'quote_items': {
        'label': 'Quote lines',
        'description': 'Every line on every quote, joined back by quote reference.',
        'filename': 'quote_items.csv',
        'header': ['quote_reference', 'sku', 'product', 'quantity', 'unit_price', 'line_total'],
        'rows': _quote_items,
    },
    'contact_messages': {
        'label': 'Contact messages',
        'description': 'Enquiries sent through the contact form.',
        'filename': 'contact_messages.csv',
        'header': ['name', 'email', 'phone', 'subject', 'message', 'created_at', 'resolved_at'],
        'rows': _contact_messages,
    },
    'subscribers': {
        'label': 'Newsletter subscribers',
        'description': 'Email addresses collected from the newsletter form.',
        'filename': 'subscribers.csv',
        'header': ['email', 'is_active', 'created_at'],
        'rows': _subscribers,
    },
}


def _write_csv(dataset, stream):
    """Write one dataset to a text stream; returns the number of data rows.

    The caller cannot get that count by counting newlines afterwards: a
    product description is free text and may contain its own line breaks
    inside a quoted field.
    """
    writer = csv.writer(stream)
    writer.writerow(dataset['header'])
    written = 0
    for row in dataset['rows']():
        writer.writerow(row)
        written += 1
    return written


def dataset_counts():
    """Row count per dataset, for the export screen.

    Counting is a separate cheap query rather than a walk of the generator,
    which would otherwise build every row twice just to render the page.
    """
    from core.models import ContactMessage, Location, NewsletterSubscriber
    from quotes.models import Quote, QuoteItem

    from .models import Brand, Category, ExclusiveBrand, Product, Promotion

    return {
        'products': Product.objects.count(),
        'categories': Category.objects.count(),
        'companies': Brand.objects.count(),
        'exclusive_brands': ExclusiveBrand.objects.count(),
        'promotions': Promotion.objects.count(),
        'locations': Location.objects.count(),
        'quotes': Quote.objects.count(),
        'quote_items': QuoteItem.objects.count(),
        'contact_messages': ContactMessage.objects.count(),
        'subscribers': NewsletterSubscriber.objects.count(),
    }


def dataset_response(key):
    """One dataset as a downloadable CSV."""
    dataset = DATASETS[key]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{dataset["filename"]}"'
    # Excel on Windows needs the BOM to read UTF-8 without mangling accents.
    response.write('﻿')
    _write_csv(dataset, response)
    return response


def archive_response():
    """Every dataset at once, as a ZIP of CSV files plus a manifest.

    Built in memory: the whole site's data is a few megabytes of text at the
    scale this runs at, and a temporary file would only add cleanup to get
    wrong.
    """
    stamp = timezone.localtime().strftime('%Y-%m-%d')
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        manifest = ['Ah Liki Investment Corporation — data export', f'Generated: {timezone.localtime():%Y-%m-%d %H:%M}', '']

        for key, dataset in DATASETS.items():
            text = io.StringIO()
            count = _write_csv(dataset, text)
            archive.writestr(dataset['filename'], '﻿' + text.getvalue())
            manifest.append(f'{dataset["filename"]:<24} {count:>6} rows   {dataset["label"]}')

        manifest += [
            '',
            'All files are UTF-8 CSV with a byte order mark, so Excel opens them',
            'without mangling accented characters. products.csv uses the same',
            'columns as the product import and can be edited and uploaded back.',
        ]
        archive.writestr('README.txt', '\n'.join(manifest) + '\n')

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="ahliki-export-{stamp}.zip"'
    return response
