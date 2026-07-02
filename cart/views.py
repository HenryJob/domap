import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import Cart
from .wishlist import Wishlist


def _log_cart_event(request, product_id, event_type, quantity=1):
    try:
        from analytics.services import log_cart_event
        log_cart_event(request, product_id=product_id, event_type=event_type, quantity=quantity)
    except ImportError:
        pass


def _log_wishlist_event(request, product_id, event_type):
    try:
        from analytics.services import log_wishlist_event
        log_wishlist_event(request, product_id=product_id, event_type=event_type)
    except ImportError:
        pass


@require_POST
def cart_add(request):
    data = json.loads(request.body or '{}')
    product_id = int(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    extra_ids = [int(x) for x in data.get('extra_ids', [])]
    notes = data.get('notes', '')

    if not Product.objects.filter(id=product_id, is_active=True).exists():
        return JsonResponse({'error': 'Producto no disponible'}, status=400)

    cart = Cart(request)
    line_id = cart.add(product_id, quantity, extra_ids, notes)
    _log_cart_event(request, product_id, 'add', quantity)

    return JsonResponse({
        'line_id': line_id,
        'cart_count': cart.total_quantity(),
        'cart_subtotal': str(cart.subtotal()),
    })


@require_POST
def cart_update(request, line_id):
    data = json.loads(request.body or '{}')
    quantity = int(data.get('quantity', 1))
    cart = Cart(request)
    line = cart.data.get(str(line_id))
    if line:
        _log_cart_event(request, line['product_id'], 'update', quantity)
    cart.update(line_id, quantity)
    return JsonResponse({'cart_count': cart.total_quantity(), 'cart_subtotal': str(cart.subtotal())})


@require_POST
def cart_remove(request, line_id):
    cart = Cart(request)
    line = cart.data.get(str(line_id))
    if line:
        _log_cart_event(request, line['product_id'], 'remove')
    cart.remove(line_id)
    return JsonResponse({'cart_count': cart.total_quantity(), 'cart_subtotal': str(cart.subtotal())})


@require_POST
def wishlist_toggle(request):
    data = json.loads(request.body or '{}')
    product_id = int(data.get('product_id'))
    wishlist = Wishlist(request)
    added = wishlist.toggle(product_id)
    _log_wishlist_event(request, product_id, 'add' if added else 'remove')
    return JsonResponse({'in_wishlist': added, 'wishlist_count': wishlist.count()})
