from django.shortcuts import render
from .models import Product, Extra

MENU_STEPS = [
    {'icon': '🛍️', 'title': 'Elige tu producto', 'description': 'Explora nuestro menú y selecciona tu Mordé favorito.'},
    {'icon': '📞', 'title': 'Define cómo pedir', 'description': 'Elige entre delivery o recojo y confirma tus datos.'},
    {'icon': '🛵', 'title': 'Recibe por delivery o recojo coordinado', 'description': 'Lo preparamos al momento y lo recibes fresco y delicioso.'},
]


def menu(request):
    products = Product.objects.filter(is_active=True)
    combos = products.filter(is_combo=True)
    waffles = products.filter(is_combo=False)
    extras = Extra.objects.filter(is_active=True)

    try:
        from analytics.services import log_product_views
        log_product_views(request, list(waffles) + list(combos))
    except ImportError:
        pass

    context = {
        'waffles': waffles,
        'combos': combos,
        'extras': extras,
        'menu_steps': MENU_STEPS,
    }
    return render(request, 'catalog/menu.html', context)
