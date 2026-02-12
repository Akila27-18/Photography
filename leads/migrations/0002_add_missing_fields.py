from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='phone',
            field=models.CharField(max_length=15, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='email',
            field=models.EmailField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='event_place',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='lead',
            name='advance_amount',
            field=models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True),
        ),
    ]
