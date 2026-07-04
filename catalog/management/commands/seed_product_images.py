import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from catalog.models import Product

# Fotos reales de Unsplash (licencia libre, sin atribución requerida),
# elegidas para que representen el sabor/tipo real de cada producto en vez
# de compartir una sola foto genérica de waffle para todo el catálogo.
PRODUCT_IMAGES = {
    'morde-clasico': (
        'https://images.unsplash.com/photo-1441633980922-d18ca151ee64?w=900&q=80',
        'morde-clasico.jpg',
    ),
    'morde-chocolate': (
        'https://images.unsplash.com/photo-1580915411954-282cb1b0d780?w=900&q=80',
        'morde-chocolate.jpg',
    ),
    'morde-frutas-miel': (
        'https://images.unsplash.com/photo-1558584724-0e4d32ca55a4?w=900&q=80',
        'morde-frutas-miel.jpg',
    ),
    'morde-banano-crunch': (
        'https://images.unsplash.com/photo-1491273289208-9340cb42e5d9?w=900&q=80',
        'morde-banano-crunch.jpg',
    ),
    'morde-personalizado': (
        'https://images.unsplash.com/photo-1706166654770-56756519360b?w=900&q=80',
        'morde-personalizado.jpg',
    ),
    'mini-morde-box': (
        'https://images.unsplash.com/photo-1562376552-0d160a2f238d?w=900&q=80',
        'mini-morde-box.jpg',
    ),
    'combo-morde-bebida': (
        'https://images.unsplash.com/photo-1657019358241-9c9c6a8c1798?w=900&q=80',
        'combo-morde-bebida.jpg',
    ),
    'duo-morde': (
        'https://images.unsplash.com/photo-1647210391533-5fe30109e94a?w=900&q=80',
        'duo-morde.png',
    ),
}


class Command(BaseCommand):
    help = 'Descarga y asigna una foto real (Unsplash, licencia libre) a cada producto por slug.'

    def handle(self, *args, **options):
        updated = 0
        for slug, (url, filename) in PRODUCT_IMAGES.items():
            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Producto no encontrado, se omite: {slug}'))
                continue

            if product.image:
                self.stdout.write(f'{slug} ya tiene imagen, se omite.')
                continue

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read()

            product.image.save(filename, ContentFile(content), save=True)
            updated += 1
            self.stdout.write(self.style.SUCCESS(f'{slug} -> {filename}'))

        self.stdout.write(self.style.SUCCESS(f'Listo: {updated} producto(s) actualizado(s).'))
