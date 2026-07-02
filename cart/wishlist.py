WISHLIST_SESSION_KEY = 'wishlist'


class Wishlist:
    """Lista de favoritos guardada en sesión: lista de product_id."""

    def __init__(self, request):
        self.session = request.session
        self.session.setdefault(WISHLIST_SESSION_KEY, [])

    @property
    def data(self):
        return self.session[WISHLIST_SESSION_KEY]

    def toggle(self, product_id):
        product_id = int(product_id)
        if product_id in self.data:
            self.data.remove(product_id)
            added = False
        else:
            self.data.append(product_id)
            added = True
        self.session.modified = True
        return added

    def count(self):
        return len(self.data)

    def products(self):
        from catalog.models import Product
        return Product.objects.filter(id__in=self.data)
