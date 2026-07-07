from django.shortcuts import render
from catalog.models import Product
from .constants import SALE_STEPS


def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True)[:4]
    context = {'featured_products': featured, 'home_steps': SALE_STEPS}
    return render(request, 'core/home.html', context)


def nosotros(request):
    return render(request, 'core/nosotros.html')


def beneficios(request):
    return render(request, 'core/beneficios.html')
