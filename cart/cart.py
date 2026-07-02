from collections import Counter

CART_SESSION_KEY = 'cart'


class Cart:
    """Carrito guardado en la sesión: {line_id: {product_id, quantity, extra_ids, notes}}.
    No usa modelos de BD porque es estado efímero antes del checkout."""

    def __init__(self, request):
        self.session = request.session
        self.session.setdefault(CART_SESSION_KEY, {})

    @property
    def data(self):
        return self.session[CART_SESSION_KEY]

    def _next_line_id(self):
        existing = [int(k) for k in self.data.keys()]
        return str(max(existing) + 1) if existing else '1'

    def add(self, product_id, quantity=1, extra_ids=None, notes=''):
        line_id = self._next_line_id()
        self.data[line_id] = {
            'product_id': product_id,
            'quantity': quantity,
            'extra_ids': extra_ids or [],
            'notes': notes,
        }
        self._save()
        return line_id

    def update(self, line_id, quantity):
        line_id = str(line_id)
        if line_id in self.data:
            if quantity <= 0:
                del self.data[line_id]
            else:
                self.data[line_id]['quantity'] = quantity
            self._save()

    def remove(self, line_id):
        line_id = str(line_id)
        if line_id in self.data:
            del self.data[line_id]
            self._save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self._save()

    def total_quantity(self):
        return sum(line['quantity'] for line in self.data.values())

    def is_empty(self):
        return len(self.data) == 0

    def lines(self):
        """Devuelve las líneas del carrito con los objetos Product/Extra resueltos.

        Cada extra puede repetirse en extra_ids (ej. [3, 3, 5] = 2x extra-3 + 1x
        extra-5); aquí se agrupan en pares (extra, cantidad) para mostrar
        "2x Miel" en vez de la misma línea repetida dos veces."""
        from catalog.models import Product, Extra
        product_ids = [line['product_id'] for line in self.data.values()]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        extra_ids = {eid for line in self.data.values() for eid in line.get('extra_ids', [])}
        extras = {e.id: e for e in Extra.objects.filter(id__in=extra_ids)}

        result = []
        for line_id, line in self.data.items():
            product = products.get(line['product_id'])
            if not product:
                continue
            extra_counts = Counter(line.get('extra_ids', []))
            line_extras = [(extras[eid], qty) for eid, qty in extra_counts.items() if eid in extras]
            extras_total = sum(extra.price * qty for extra, qty in line_extras)
            unit_price = product.price + extras_total
            result.append({
                'line_id': line_id,
                'product': product,
                'quantity': line['quantity'],
                'extras': line_extras,
                'notes': line.get('notes', ''),
                'unit_price': unit_price,
                'line_total': unit_price * line['quantity'],
            })
        return result

    def subtotal(self):
        return sum(line['line_total'] for line in self.lines())

    def _save(self):
        self.session.modified = True
