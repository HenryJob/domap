from django.db import migrations

# Zonas iniciales de ejemplo (Lima Metropolitana). El costo es editable desde
# /admin en cualquier momento sin necesidad de otra migración.
ZONES = [
    ('San Miguel', 5.00),
    ('Pueblo Libre', 5.00),
    ('Magdalena del Mar', 5.00),
    ('Jesús María', 6.00),
    ('Lince', 6.00),
    ('Cercado de Lima', 6.00),
    ('Miraflores', 7.00),
    ('San Isidro', 7.00),
    ('Surquillo', 7.00),
    ('Breña', 7.00),
    ('San Borja', 8.00),
    ('Surco', 9.00),
    ('La Molina', 10.00),
    ('Los Olivos', 10.00),
    ('San Juan de Lurigancho', 12.00),
    ('Ate', 12.00),
]


def seed_zones(apps, schema_editor):
    DeliveryZone = apps.get_model('orders', 'DeliveryZone')
    for name, fee in ZONES:
        DeliveryZone.objects.get_or_create(name=name, defaults={'fee': fee, 'active': True})


def remove_zones(apps, schema_editor):
    DeliveryZone = apps.get_model('orders', 'DeliveryZone')
    DeliveryZone.objects.filter(name__in=[name for name, _ in ZONES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_deliveryzone_order_delivery_zone'),
    ]

    operations = [
        migrations.RunPython(seed_zones, remove_zones),
    ]
