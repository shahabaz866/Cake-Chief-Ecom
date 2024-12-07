# Generated by Django 5.1.1 on 2024-11-22 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_app', '0013_alter_cartitem_variant'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='delivery_charge',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='cart',
            name='packaging_charge',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='cart',
            name='tax',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]