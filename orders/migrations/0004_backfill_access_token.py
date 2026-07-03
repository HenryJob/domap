import secrets

from django.db import migrations


def backfill_access_token(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.filter(access_token=''):
        order.access_token = secrets.token_urlsafe(24)
        order.save(update_fields=['access_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_order_access_token_order_email_order_user'),
    ]

    operations = [
        migrations.RunPython(backfill_access_token, migrations.RunPython.noop),
    ]
