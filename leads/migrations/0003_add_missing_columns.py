from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_add_missing_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='phone',
            field=models.CharField(max_length=15, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='event_place',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='advance_amount',
            field=models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True),
        ),
    ]
