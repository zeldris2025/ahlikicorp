"""Template helpers for the public catalogue."""

from django import template

register = template.Library()

# Specification keys that are internal bookkeeping rather than something a
# customer chooses a product by. They stay on the record — the import and the
# staff portal still rely on them — but they are not printed on the catalogue.
HIDDEN_SPEC_KEYS = {
    'product no.',
    'product no',
    'product number',
    'sku',
}


@register.filter
def public_specs(specifications):
    """The specification entries worth showing a customer.

    Returns a list of (key, value) pairs so the template can iterate it the
    same way it iterated the raw dict.
    """
    if not isinstance(specifications, dict):
        return []
    return [
        (key, value)
        for key, value in specifications.items()
        if str(key).strip().lower() not in HIDDEN_SPEC_KEYS and value not in (None, '')
    ]
