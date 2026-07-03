from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_backfill_access_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='access_token',
            field=models.CharField(blank=True, editable=False, max_length=40, unique=True),
        ),
    ]
