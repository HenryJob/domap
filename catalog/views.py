from django.shortcuts import render
from .models import Product, Extra
from core.constants import SALE_STEPS


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
        'menu_steps': SALE_STEPS,
    }
    return render(request, 'catalog/menu.html', context)
