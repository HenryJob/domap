from django.shortcuts import render
from catalog.models import Product


HOME_STEPS = [
    {'icon': '🛍️', 'title': 'Elige tu waffle', 'description': 'Explora el menú y selecciona tu favorito.'},
    {'icon': '📞', 'title': 'Elige cómo pedir', 'description': 'Pide por WhatsApp o directamente desde la web.'},
    {'icon': '🛵', 'title': 'Te lo preparamos', 'description': 'Con ingredientes seleccionados y mucho amor.'},
    {'icon': '📦', 'title': 'Lo recibes', 'description': 'Delivery a tu puerta o recojo coordinado en nuestro punto.'},
]


def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True)[:4]
    context = {'featured_products': featured, 'home_steps': HOME_STEPS}
    return render(request, 'core/home.html', context)


def nosotros(request):
    return render(request, 'core/nosotros.html')


def beneficios(request):
    return render(request, 'core/beneficios.html')
