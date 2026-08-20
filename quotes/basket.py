"""Session-backed quote basket.

Customers assemble a list of products before submitting a quote request, so the
basket has to survive across requests without requiring an account. It stores
only product ids and quantities; names and prices are always read back from the
database, so a renamed or deactivated product can never be misrepresented from
a stale session.
"""

from products.models import Product

SESSION_KEY = 'quote_basket'


class QuoteBasket:
    def __init__(self, request):
        self.session = request.session
        basket = self.session.get(SESSION_KEY)
        if not isinstance(basket, dict):
            basket = {}
        self.basket = basket

    # -- mutation ---------------------------------------------------------
    def add(self, product, quantity=1, replace=False):
        key = str(product.pk)
        quantity = max(1, int(quantity))
        if replace or key not in self.basket:
            self.basket[key] = quantity
        else:
            self.basket[key] = self.basket[key] + quantity
        self.save()

    def set_quantity(self, product_id, quantity):
        key = str(product_id)
        if key not in self.basket:
            return
        quantity = int(quantity)
        if quantity < 1:
            self.remove(product_id)
        else:
            self.basket[key] = quantity
            self.save()

    def remove(self, product_id):
        self.basket.pop(str(product_id), None)
        self.save()

    def clear(self):
        self.session[SESSION_KEY] = {}
        self.basket = {}
        self.session.modified = True

    def save(self):
        self.session[SESSION_KEY] = self.basket
        self.session.modified = True

    # -- reading ----------------------------------------------------------
    def items(self):
        """Basket lines with live product data attached.

        Products that have since been deactivated or deleted are dropped from
        the session rather than shown, so a customer cannot request a quote for
        something no longer offered.
        """
        if not self.basket:
            return []

        products = Product.objects.filter(
            pk__in=self.basket.keys(), is_active=True
        ).select_related('brand', 'category')
        found = {str(p.pk): p for p in products}

        stale = [k for k in self.basket if k not in found]
        if stale:
            for key in stale:
                self.basket.pop(key, None)
            self.save()

        return [
            {'product': found[key], 'quantity': qty}
            for key, qty in self.basket.items()
            if key in found
        ]

    def __len__(self):
        return sum(self.basket.values()) if self.basket else 0

    @property
    def line_count(self):
        return len(self.basket)

    def __contains__(self, product_id):
        return str(product_id) in self.basket
