from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Product, Extra

WAFFLES = [
    dict(name='Mordé Clásico', description='Waffle dorado con topping suave y balanceado.',
         price=12.90, is_featured=True, display_order=1),
    dict(name='Mordé Chocolate', description='Para los amantes del cacao y el antojo dulce.',
         price=14.90, is_featured=True, display_order=2),
    dict(name='Mordé Frutas & Miel', description='Fresco, ligero y naturalmente delicioso.',
         price=15.90, is_featured=True, display_order=3),
    dict(name='Mordé Banano Crunch', description='Banano, crema y toque crocante.',
         price=15.50, display_order=4),
    dict(name='Mordé Personalizado', description='Arma tu combinación favorita.',
         price=16.90, price_is_from=True, is_customizable=True, is_featured=True, display_order=5),
    dict(name='Mini Mordé Box', description='Porción ideal para compartir o probar sabores.',
         price=18.90, display_order=6),
]

COMBOS = [
    dict(name='Combo Mordé + bebida', description='Elige tu Mordé favorito y acompáñalo con una bebida natural.',
         price=21.90, is_combo=True, display_order=7,
         combo_products=['Mordé Clásico']),
    dict(name='Dúo Mordé', description='Elige 2 Mordés y disfruta en buena compañía.',
         price=28.90, is_combo=True, display_order=8,
         combo_products=['Mordé Chocolate', 'Mordé Frutas & Miel']),
]

EXTRAS = [
    dict(name='Miel', icon_emoji='🍯', price=2.00, display_order=1),
    dict(name='Fresa', icon_emoji='🍓', price=2.00, display_order=2),
    dict(name='Banano', icon_emoji='🍌', price=2.00, display_order=3),
    dict(name='Chocolate', icon_emoji='🍫', price=2.00, display_order=4),
    dict(name='Granola', icon_emoji='🥣', price=2.00, display_order=5),
    dict(name='Arándano', icon_emoji='🫐', price=2.00, display_order=6),
]


class Command(BaseCommand):
    help = 'Carga los productos, combos y extras de Mordé (datos de las capturas de diseño).'

    def handle(self, *args, **options):
        created_count = 0
        combo_links = {}
        for item in WAFFLES + COMBOS:
            item = dict(item)
            related_names = item.pop('combo_products', None)
            slug = slugify(item['name'])
            product, created = Product.objects.update_or_create(
                slug=slug, defaults={**item, 'slug': slug},
            )
            created_count += created
            if related_names is not None:
                combo_links[product.pk] = related_names

        for product_pk, related_names in combo_links.items():
            related = Product.objects.filter(name__in=related_names)
            Product.objects.get(pk=product_pk).combo_products.set(related)

        for item in EXTRAS:
            _, created = Extra.objects.update_or_create(
                name=item['name'], defaults=item,
            )
            created_count += created

        self.stdout.write(self.style.SUCCESS(
            f'Catálogo cargado: {len(WAFFLES)} waffles, {len(COMBOS)} combos, '
            f'{len(EXTRAS)} extras ({created_count} nuevos registros).'
        ))
