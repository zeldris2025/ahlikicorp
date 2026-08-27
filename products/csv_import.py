"""Shared CSV import for products.

The staff portal and Django Admin both offer a product import, and they must
agree on the column set and on how a row is interpreted — so the parsing lives
here and both entry points call in.
"""

import csv
import io
import json
from decimal import Decimal, InvalidOperation

from django.http import HttpResponse
from django.utils.text import slugify

from .models import Brand, Category, Product

# Column order is also the order used by the downloadable template.
CSV_COLUMNS = [
    'name',
    'category',
    'description',
    'cost_price',
    'stock_quantity',
    'is_exclusive',
    'specifications',
]

TEMPLATE_ROWS = [
    [
        'Long Grain White Rice 25kg',
        'Grains',
        'Premium imported long grain rice',
        '45.00',
        '100',
        'false',
        '{"Pack size": "25kg sack"}',
    ],
    [
        'Coconut Oil 1L',
        'Oils',
        'Pure virgin coconut oil',
        '12.50',
        '50',
        'true',
        '{"Size": "1 litre"}',
    ],
]

TRUE_VALUES = ('true', '1', 'yes', 'y')


class CsvImportError(Exception):
    """The file as a whole could not be imported — nothing was created."""


def template_response(filename='product_import_template.csv'):
    """A ready-to-fill CSV with the header row and two example products."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(CSV_COLUMNS)
    writer.writerows(TEMPLATE_ROWS)
    return response


class ImportResult:
    def __init__(self):
        self.created = 0
        self.created_categories = set()
        self.errors = []  # (row_number, message)
        self.skipped = []  # (row_number, message)

    @property
    def has_errors(self):
        return bool(self.errors)

    @property
    def has_skipped(self):
        return bool(self.skipped)

    def error_summary(self):
        return 'Errors in rows: ' + ', '.join(f'{row} ({msg})' for row, msg in self.errors)

    def skipped_summary(self):
        return (
            f'{len(self.skipped)} unchanged row(s) skipped: '
            + ', '.join(f'{row} ({msg})' for row, msg in self.skipped)
        )

    def success_summary(self):
        msg = f'{self.created} product(s) created successfully.'
        if self.created_categories:
            msg += ' Auto-created categories: ' + ', '.join(sorted(self.created_categories)) + '.'
        return msg


def _get_or_create_category(name, result):
    category = Category.objects.filter(name__iexact=name).first()
    if category:
        return category

    base_slug = slugify(name) or 'category'
    slug, n = base_slug, 2
    while Category.objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{n}'
        n += 1

    category = Category.objects.create(name=name, slug=slug)
    result.created_categories.add(category.name)
    return category


def _parse_specifications(raw):
    raw = (raw or '').strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError('specifications must be valid JSON, e.g. {"Pack size": "25kg"}')
    if not isinstance(value, dict):
        raise ValueError('specifications must be a JSON object')
    return value


def _parse_price(raw):
    raw = (raw or '').strip()
    if not raw:
        return Decimal('0')
    try:
        return Decimal(raw)
    except InvalidOperation:
        raise ValueError('cost_price must be a number, e.g. 45.00')


def _fingerprint(name, category_id, description, cost_price, stock_quantity,
                 is_exclusive, specifications):
    """The values that decide whether two rows describe the same product.

    Re-uploading last week's sheet with a handful of new lines is the normal
    way staff work, so a row whose fingerprint already exists is not an error —
    it is simply nothing to do. ``specifications`` is compared as sorted JSON
    so key order in the file does not matter.
    """
    return (
        name.strip().lower(),
        category_id,
        description.strip(),
        Decimal(cost_price),
        int(stock_quantity),
        bool(is_exclusive),
        json.dumps(specifications or {}, sort_keys=True),
    )


def import_products(csv_file, brand_slug='ahliki-wholesale'):
    """Create products from an uploaded CSV file.

    Rows that fail are skipped and reported; the rest still import. Raises
    ``CsvImportError`` only when nothing can be read at all.
    """
    brand = Brand.objects.filter(slug=brand_slug).first()
    if not brand:
        raise CsvImportError('Ah Liki Wholesale brand not found. Create it before importing.')

    try:
        content = csv_file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        raise CsvImportError('The file could not be read as UTF-8 text. Re-save it as CSV UTF-8.')

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise CsvImportError('The CSV file is empty.')

    headers = {(h or '').strip().lower() for h in reader.fieldnames}
    missing = [c for c in ('name', 'category') if c not in headers]
    if missing:
        raise CsvImportError('Missing required column(s): ' + ', '.join(missing))

    result = ImportResult()

    # Fingerprints of the products already on file for this brand, plus every
    # row accepted so far, so a sheet that repeats itself only imports once.
    seen = {
        _fingerprint(
            p.name, p.category_id, p.description, p.cost_price,
            p.stock_quantity, p.is_exclusive, p.specifications,
        )
        for p in Product.objects.filter(brand=brand).only(
            'name', 'category_id', 'description', 'cost_price',
            'stock_quantity', 'is_exclusive', 'specifications',
        )
    }

    for row_num, row in enumerate(reader, start=2):
        row = {(k or '').strip().lower(): (v or '') for k, v in row.items()}
        try:
            name = row.get('name', '').strip()
            if not name:
                result.errors.append((row_num, 'Product name is required'))
                continue

            category_name = row.get('category', '').strip()
            if not category_name:
                result.errors.append((row_num, 'Category is required'))
                continue

            category = _get_or_create_category(category_name, result)

            stock = row.get('stock_quantity', '').strip()

            description = row.get('description', '').strip()
            cost_price = _parse_price(row.get('cost_price'))
            stock_quantity = int(stock) if stock else 0
            is_exclusive = row.get('is_exclusive', '').strip().lower() in TRUE_VALUES
            specifications = _parse_specifications(row.get('specifications'))

            fingerprint = _fingerprint(
                name, category.pk, description, cost_price,
                stock_quantity, is_exclusive, specifications,
            )
            if fingerprint in seen:
                result.skipped.append((row_num, f'{name} is already on file, unchanged'))
                continue

            product = Product(
                name=name,
                brand=brand,
                category=category,
                description=description,
                cost_price=cost_price,
                stock_quantity=stock_quantity,
                is_exclusive=is_exclusive,
                is_active=True,
                specifications=specifications,
            )
            product.save()
            seen.add(fingerprint)
            result.created += 1
        except Exception as exc:  # a bad row must not abort the whole file
            result.errors.append((row_num, str(exc)))

    return result
